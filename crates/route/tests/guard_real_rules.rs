use sealrun_route::metric::Tool;
use sealrun_route::plan::plan;
use sealrun_route::state::{Inv, Move, State};
use sealrun_route::tech::Item;
use sealrun_world::grid::{Grid, Tile};

fn hand_map() -> Grid {
    let mut g = Grid::new(3, 2);
    g.set(0, 0, Tile::Tree);
    g.set(2, 0, Tile::Iron);
    g.set(1, 1, Tile::Stone);
    g
}

fn start() -> State {
    State { pos: (1, 0), inv: Inv::EMPTY }
}

fn check(grid: &Grid, start: State, route: &[Move]) -> Result<(u64, State), String> {
    let mut s = start;
    let mut ticks = 0;
    for (i, m) in route.iter().enumerate() {
        let (next, cost) = step(grid, s, *m).map_err(|e| format!("move {i} {m:?}: {e}"))?;
        s = next;
        ticks += cost;
    }
    Ok((ticks, s))
}

fn step(grid: &Grid, s: State, m: Move) -> Result<(State, u64), String> {
    match m {
        Move::Walk(p) => {
            if !four_neighbour(grid, s.pos, p) {
                return Err(format!("{p:?} is not a 4-neighbour of {:?}", s.pos));
            }
            match grid.get(p.0, p.1) {
                Tile::Air | Tile::Goal => Ok((State { pos: p, inv: s.inv }, 5)),
                t => Err(format!("cannot walk into {t:?}")),
            }
        }
        Move::Mine(p) => {
            if !four_neighbour(grid, s.pos, p) {
                return Err(format!("{p:?} is not a 4-neighbour of {:?}", s.pos));
            }
            let mut inv = s.inv;
            let (ticks, gained) = match grid.get(p.0, p.1) {
                Tile::Tree => (60, &mut inv.wood),
                Tile::Stone => {
                    let ticks = match s.inv.pick {
                        Tool::Hand => return Err("stone needs a wood pickaxe, have Hand".into()),
                        Tool::Wood => 23,
                        Tool::Stone => 12,
                        Tool::Iron => 8,
                    };
                    (ticks, &mut inv.stone)
                }
                Tile::Iron => {
                    let ticks = match s.inv.pick {
                        Tool::Hand | Tool::Wood => {
                            return Err(format!("iron needs a stone pickaxe, have {:?}", s.inv.pick))
                        }
                        Tool::Stone => 23,
                        Tool::Iron => 15,
                    };
                    (ticks, &mut inv.iron_ore)
                }
                t => return Err(format!("cannot mine {t:?}")),
            };
            *gained += 1;
            Ok((State { pos: s.pos, inv }, ticks))
        }
        Move::Craft(item) => {
            let inv = craft(s.inv, item).ok_or_else(|| format!("{item:?} is not craftable from {:?}", s.inv))?;
            Ok((State { pos: s.pos, inv }, 20))
        }
        Move::Smelt => {
            if !(s.inv.furnace && s.inv.iron_ore >= 1) {
                return Err("smelt needs a furnace and iron ore".into());
            }
            let inv = Inv { iron_ore: s.inv.iron_ore - 1, iron: s.inv.iron + 1, ..s.inv };
            Ok((State { pos: s.pos, inv }, 200))
        }
    }
}

fn four_neighbour(grid: &Grid, from: (u32, u32), to: (u32, u32)) -> bool {
    let dx = (from.0 as i64 - to.0 as i64).abs();
    let dy = (from.1 as i64 - to.1 as i64).abs();
    dx + dy == 1 && grid.in_bounds(to.0 as i64, to.1 as i64)
}

fn craft(i: Inv, item: Item) -> Option<Inv> {
    match item {
        Item::Table if !i.table && i.wood >= 1 => Some(Inv { wood: i.wood - 1, table: true, ..i }),
        Item::WoodPickaxe if i.table && i.pick == Tool::Hand && i.wood >= 2 => {
            Some(Inv { wood: i.wood - 2, pick: Tool::Wood, ..i })
        }
        Item::StonePickaxe if i.table && i.wood >= 1 && i.stone >= 3 && i.pick < Tool::Stone => {
            Some(Inv { wood: i.wood - 1, stone: i.stone - 3, pick: Tool::Stone, ..i })
        }
        Item::Furnace if i.table && !i.furnace && i.stone >= 8 => Some(Inv { stone: i.stone - 8, furnace: true, ..i }),
        Item::IronPickaxe if i.table && i.furnace && i.wood >= 1 && i.iron >= 3 && i.pick < Tool::Iron => {
            Some(Inv { wood: i.wood - 1, iron: i.iron - 3, pick: Tool::Iron, ..i })
        }
        _ => None,
    }
}

#[test]
fn guard_real_rules() {
    let g = hand_map();
    let s = start();
    let (plan_ticks, route) = plan(&g, s, (1, 0), |st| st.inv.iron_ore >= 1).expect("plan finds iron");
    assert_eq!(plan_ticks, 392, "hand count: 4 trees 240, table 20, wood pick 20, 3 stone 69, stone pick 20, iron 23");
    let (ticks, end) = check(&g, s, &route).expect("plan route replays");
    assert_eq!(ticks, plan_ticks, "checker ticks vs plan ticks");
    assert!(end.pos == (1, 0) && end.inv.iron_ore >= 1, "end state {end:?}");

    let wood_iron = [
        Move::Mine((0, 0)),
        Move::Mine((0, 0)),
        Move::Mine((0, 0)),
        Move::Craft(Item::Table),
        Move::Craft(Item::WoodPickaxe),
        Move::Mine((2, 0)),
    ];
    let err = check(&g, s, &wood_iron).expect_err("a wood pick must not mine iron");
    assert!(err.contains("stone pickaxe"), "error was: {err}");

    let err = check(&g, s, &[Move::Walk((1, 1))]).expect_err("walking into stone must fail");
    assert!(err.contains("Stone"), "error was: {err}");

    let mut row = Grid::new(3, 1);
    row.set(0, 0, Tile::Tree);
    row.set(2, 0, Tile::Stone);
    let done = |st: &State| st.inv.furnace && st.inv.pick >= Tool::Stone;
    let (furnace_ticks, furnace_route) = plan(&row, s, (1, 0), done).expect("plan finds a furnace with a stone pickaxe");
    assert_eq!(furnace_ticks, 485, "hand count: 4 trees 240, 4 crafts 80, 3 stone with wood pick 69, 8 stone with stone pick 96");
    let (replayed, end) = check(&row, s, &furnace_route).expect("furnace route replays");
    assert_eq!(replayed, furnace_ticks, "checker ticks vs plan ticks, furnace route");
    assert!(end.pos == (1, 0) && end.inv.furnace && end.inv.pick >= Tool::Stone, "end state {end:?}");
}
