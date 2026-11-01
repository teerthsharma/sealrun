//! realmodel::moves is the per-move API; it forwards state::moves costs and drops moves whose next state passes a cap.
//! Caps mirror realmodel.rs within_caps (private, so restated): wood 5, stone 11, iron_ore 3, iron 3.
use sealrun_route::metric::{dig, Tool, CRAFT_TICKS, WALK_TICKS};
use sealrun_route::realmodel::{moves as real_moves, Step};
use sealrun_route::state::{moves as state_moves, Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};

// SMELT_TICKS is private to state.rs and has no metric.rs value, so smelt is compared state vs realmodel only.
const TILES: [Tile; 6] = [Tile::Air, Tile::Stone, Tile::Water, Tile::Tree, Tile::Iron, Tile::Goal];
const TOOLS: [Tool; 4] = [Tool::Hand, Tool::Wood, Tool::Stone, Tool::Iron];
const CAP_WOOD: u16 = 5;
const CAP_STONE: u16 = 11;
const CAP_IRON_ORE: u16 = 3;
const CAP_IRON: u16 = 3;
const EXPECTED_GAPS: usize = 2464;

#[derive(Clone, Copy, Debug)]
enum Want {
    Absent,
    Cost(u64),
    Present,
}

#[derive(Default)]
struct Tally {
    cases: usize,
    seen: [usize; 4],
    gap: [usize; 4],
    cost_bad: Vec<String>,
    presence_bad: Vec<String>,
}

fn kind(m: Move) -> usize {
    match m {
        Move::Walk(_) => 0,
        Move::Mine(_) => 1,
        Move::Craft(_) => 2,
        Move::Smelt => 3,
    }
}

fn past_cap(s: &State) -> bool {
    s.inv.wood > CAP_WOOD || s.inv.stone > CAP_STONE || s.inv.iron_ore > CAP_IRON_ORE || s.inv.iron > CAP_IRON
}

fn check(t: &mut Tally, case: &str, m: Move, want: Want, state: Option<(u64, bool)>, real: Option<u64>) {
    t.cases += 1;
    t.seen[kind(m)] += 1;
    let s = state.map(|(c, _)| c);
    let cost_ok = match want {
        Want::Absent => s.is_none() && real.is_none(),
        Want::Cost(c) => s.unwrap_or(c) == c && real.unwrap_or(c) == c,
        Want::Present => match (s, real) {
            (Some(a), Some(b)) => a == b,
            _ => true,
        },
    };
    if !cost_ok {
        t.cost_bad.push(format!("{case} {m:?} want {want:?}: state {s:?}, realmodel {real:?}"));
    }
    match (state, real) {
        (Some((_, true)), None) => t.gap[kind(m)] += 1,
        (Some((_, false)), None) => {
            t.presence_bad.push(format!("{case} {m:?}: state offers, realmodel drops, next state within caps"))
        }
        (None, Some(_)) => t.presence_bad.push(format!("{case} {m:?}: realmodel offers, state does not")),
        (None, None) if !matches!(want, Want::Absent) => {
            t.presence_bad.push(format!("{case} {m:?}: neither model offers, metric expects it"))
        }
        _ => {}
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
            let sc = |m: Move| st.iter().find(|(x, _, _)| *x == m).map(|(_, n, c)| (*c, past_cap(n)));
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
                        t.presence_bad.push(format!("{case} {m:?}: realmodel offers, state does not"));
                    }
                }
            }
        }
    }
    let gaps: usize = t.gap.iter().sum();
    println!(
        "guard_route_costs_match_metric: {} cases ({} walk, {} mine, {} craft, {} smelt)",
        t.cases, t.seen[0], t.seen[1], t.seen[2], t.seen[3]
    );
    println!(
        "cap-boundary gaps: {} walk, {} mine, {} craft, {} smelt = {gaps}; cost mismatches {}; presence failures {}",
        t.gap[0],
        t.gap[1],
        t.gap[2],
        t.gap[3],
        t.cost_bad.len(),
        t.presence_bad.len()
    );
    assert!(t.cost_bad.is_empty(), "{} cost mismatches:\n{}", t.cost_bad.len(), t.cost_bad.join("\n"));
    assert!(t.presence_bad.is_empty(), "{} presence failures:\n{}", t.presence_bad.len(), t.presence_bad.join("\n"));
    assert_eq!(gaps, EXPECTED_GAPS, "cap-boundary gap count changed; the caps or the move list moved");
}
