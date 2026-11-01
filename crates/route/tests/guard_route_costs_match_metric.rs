//! realmodel::moves is the per-move API; it forwards state::moves costs and adds only the caps filter.
use sealrun_route::metric::{dig, Tool, CRAFT_TICKS, WALK_TICKS};
use sealrun_route::realmodel::{moves as real_moves, Step};
use sealrun_route::state::{moves as state_moves, Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};

// SMELT_TICKS is private to state.rs and has no metric.rs value, so smelt is compared state vs realmodel only.
const TILES: [Tile; 6] = [Tile::Air, Tile::Stone, Tile::Water, Tile::Tree, Tile::Iron, Tile::Goal];
const TOOLS: [Tool; 4] = [Tool::Hand, Tool::Wood, Tool::Stone, Tool::Iron];

#[derive(Clone, Copy, Debug)]
enum Want {
    Absent,
    Cost(u64),
    Present,
}

#[derive(Default)]
struct Tally {
    cases: usize,
    walk: usize,
    mine: usize,
    craft: usize,
    smelt: usize,
    bad: Vec<String>,
}

fn check(t: &mut Tally, case: &str, m: Move, want: Want, sc: Option<u64>, rc: Option<u64>) {
    let ok = match want {
        Want::Absent => sc.is_none() && rc.is_none(),
        Want::Cost(c) => sc == Some(c) && rc == Some(c),
        Want::Present => sc.is_some() && sc == rc,
    };
    t.cases += 1;
    match m {
        Move::Walk(_) => t.walk += 1,
        Move::Mine(_) => t.mine += 1,
        Move::Craft(_) => t.craft += 1,
        Move::Smelt => t.smelt += 1,
    }
    if !ok {
        t.bad.push(format!("{case} {m:?} want {want:?}: state {sc:?}, realmodel {rc:?}"));
    }
}

fn inventories() -> Vec<Inv> {
    let mut out = Vec::new();
    for wood in [0, 1, 2, 5] {
        for stone in [0, 3, 8, 11] {
            for iron_ore in [0, 1, 3] {
                for iron in [0, 3] {
                    for table in [false, true] {
                        for furnace in [false, true] {
                            for pick in TOOLS {
                                out.push(Inv { wood, stone, iron_ore, iron, table, furnace, pick });
                            }
                        }
                    }
                }
            }
        }
    }
    out
}

#[test]
fn guard_route_costs_match_metric() {
    let mut t = Tally::default();
    for tile in TILES {
        for inv in inventories() {
            let mut grid = Grid::new(3, 1);
            grid.set(2, 0, tile);
            let s = State { pos: (1, 0), inv };
            let st = state_moves(&grid, &s);
            let rl = real_moves(&grid, &s);
            let sc = |m: Move| st.iter().find(|(x, _, _)| *x == m).map(|(_, _, c)| *c);
            let rc = |m: Move| rl.iter().find(|(x, _, _)| *x == Step::Base(m)).map(|(_, _, c)| *c);
            let case = format!("tile={tile:?} inv={inv:?}");

            let far_walk = if tile.is_open() { Want::Cost(WALK_TICKS) } else { Want::Absent };
            let mine = match dig(tile, inv.pick) {
                Some(d) if d.drops => Want::Cost(d.ticks),
                _ => Want::Absent,
            };
            let explicit = [
                (Move::Walk((0, 0)), Want::Cost(WALK_TICKS)),
                (Move::Walk((2, 0)), far_walk),
                (Move::Mine((2, 0)), mine),
                (Move::Mine((0, 0)), Want::Absent),
            ];
            for (m, want) in explicit {
                check(&mut t, &case, m, want, sc(m), rc(m));
            }
            for (m, _, _) in &st {
                match m {
                    Move::Craft(_) => check(&mut t, &case, *m, Want::Cost(CRAFT_TICKS), sc(*m), rc(*m)),
                    Move::Smelt => check(&mut t, &case, *m, Want::Present, sc(*m), rc(*m)),
                    Move::Walk(_) | Move::Mine(_) => {}
                }
            }
            for (step, _, _) in &rl {
                if let Step::Base(m) = step {
                    if sc(*m).is_none() {
                        t.bad.push(format!("{case} {m:?}: realmodel offers, state does not"));
                    }
                }
            }
        }
    }
    println!(
        "guard_route_costs_match_metric: {} cases ({} walk, {} mine, {} craft, {} smelt), {} mismatches",
        t.cases,
        t.walk,
        t.mine,
        t.craft,
        t.smelt,
        t.bad.len()
    );
    assert!(t.bad.is_empty(), "{} of {} cases mismatch:\n{}", t.bad.len(), t.cases, t.bad.join("\n"));
}
