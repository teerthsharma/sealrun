use crate::metric::{dig, Tool, CRAFT_TICKS, WALK_TICKS};
use crate::tech::Item;
use sealrun_world::grid::{Grid, Tile};

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct Inv {
    pub wood: u16,
    pub stone: u16,
    pub iron_ore: u16,
    pub iron: u16,
    pub table: bool,
    pub furnace: bool,
    pub pick: Tool,
}

impl Inv {
    pub const EMPTY: Inv = Inv {
        wood: 0,
        stone: 0,
        iron_ore: 0,
        iron: 0,
        table: false,
        furnace: false,
        pick: Tool::Hand,
    };
}

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub struct State {
    pub pos: (u32, u32),
    pub inv: Inv,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Move {
    Walk((u32, u32)),
    Mine((u32, u32)),
    Craft(Item),
    Smelt,
}

const SMELT_TICKS: u64 = 200;
const DIRS: [(i64, i64); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];

fn crafts(i: Inv) -> Vec<(Item, Inv)> {
    let mut out = Vec::new();
    if !i.table && i.wood >= 1 {
        out.push((Item::Table, Inv { wood: i.wood - 1, table: true, ..i }));
    }
    if i.table && i.pick == Tool::Hand && i.wood >= 2 {
        out.push((Item::WoodPickaxe, Inv { wood: i.wood - 2, pick: Tool::Wood, ..i }));
    }
    if i.table && i.wood >= 1 && i.stone >= 3 && i.pick < Tool::Stone {
        out.push((Item::StonePickaxe, Inv { wood: i.wood - 1, stone: i.stone - 3, pick: Tool::Stone, ..i }));
    }
    if i.table && !i.furnace && i.stone >= 8 {
        out.push((Item::Furnace, Inv { stone: i.stone - 8, furnace: true, ..i }));
    }
    if i.table && i.furnace && i.wood >= 1 && i.iron >= 3 && i.pick < Tool::Iron {
        out.push((Item::IronPickaxe, Inv { wood: i.wood - 1, iron: i.iron - 3, pick: Tool::Iron, ..i }));
    }
    out
}

pub fn moves(grid: &Grid, s: &State) -> Vec<(Move, State, u64)> {
    let (x, y) = (s.pos.0 as i64, s.pos.1 as i64);
    let near: Vec<(u32, u32)> = DIRS
        .iter()
        .map(|&(dx, dy)| (x + dx, y + dy))
        .filter(|&(nx, ny)| grid.in_bounds(nx, ny))
        .map(|(nx, ny)| (nx as u32, ny as u32))
        .collect();

    let mut out = Vec::new();
    for &p in &near {
        if grid.get(p.0, p.1).is_open() {
            out.push((Move::Walk(p), State { pos: p, inv: s.inv }, WALK_TICKS));
        }
    }
    for &p in &near {
        let tile = grid.get(p.0, p.1);
        let Some(d) = dig(tile, s.inv.pick).filter(|d| d.drops) else { continue };
        let mut inv = s.inv;
        match tile {
            Tile::Tree => inv.wood += 1,
            Tile::Stone => inv.stone += 1,
            Tile::Iron => inv.iron_ore += 1,
            _ => continue,
        }
        // ponytail: blocks never deplete and map edits arrive with the surgery goals, so counts are unbounded; a planner needs its own cap.
        out.push((Move::Mine(p), State { pos: s.pos, inv }, d.ticks));
    }
    for (item, inv) in crafts(s.inv) {
        out.push((Move::Craft(item), State { pos: s.pos, inv }, CRAFT_TICKS));
    }
    if s.inv.furnace && s.inv.iron_ore >= 1 {
        let inv = Inv { iron_ore: s.inv.iron_ore - 1, iron: s.inv.iron + 1, ..s.inv };
        out.push((Move::Smelt, State { pos: s.pos, inv }, SMELT_TICKS));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn grid_with_iron() -> Grid {
        let mut g = Grid::new(3, 1);
        g.set(2, 0, Tile::Iron);
        g
    }

    fn at(inv: Inv) -> State {
        State { pos: (1, 0), inv }
    }

    fn crafts(grid: &Grid, s: &State) -> Vec<Move> {
        moves(grid, s).into_iter().map(|(m, _, _)| m).filter(|m| matches!(m, Move::Craft(_))).collect()
    }

    #[test]
    fn iron_needs_stone_pickaxe() {
        let g = grid_with_iron();

        let wood = moves(&g, &at(Inv { pick: Tool::Wood, ..Inv::EMPTY }));
        assert!(wood.iter().all(|(_, n, _)| n.inv.iron_ore == 0));

        let stone = moves(&g, &at(Inv { pick: Tool::Stone, ..Inv::EMPTY }));
        assert!(!stone.iter().any(|(m, _, _)| *m == Move::Walk((2, 0))));
        let mines: Vec<_> = stone.iter().filter(|(m, _, _)| matches!(m, Move::Mine(_))).collect();
        assert_eq!(mines.len(), 1);
        assert_eq!(mines[0].0, Move::Mine((2, 0)));
        assert_eq!(mines[0].1.inv.iron_ore, 1);
        assert_eq!(mines[0].2, 23);
    }

    #[test]
    fn empty_inventory_offers_no_craft() {
        assert!(crafts(&Grid::new(3, 1), &at(Inv::EMPTY)).is_empty());
    }

    #[test]
    fn one_wood_offers_only_table() {
        let got = crafts(&Grid::new(3, 1), &at(Inv { wood: 1, ..Inv::EMPTY }));
        assert_eq!(got, vec![Move::Craft(Item::Table)]);
    }

    #[test]
    fn stone_pickaxe_spends_wood_and_stone() {
        let inv = Inv { table: true, wood: 1, stone: 3, pick: Tool::Wood, ..Inv::EMPTY };
        let next = moves(&Grid::new(3, 1), &at(inv))
            .into_iter()
            .find(|(m, _, _)| *m == Move::Craft(Item::StonePickaxe))
            .expect("stone pickaxe is offered")
            .1;
        assert_eq!(next.inv.pick, Tool::Stone);
        assert_eq!(next.inv.wood, 0);
        assert_eq!(next.inv.stone, 0);
    }

    #[test]
    fn smelt_needs_furnace() {
        let g = Grid::new(3, 1);
        let no_furnace = Inv { table: true, iron_ore: 1, ..Inv::EMPTY };
        assert!(!moves(&g, &at(no_furnace)).iter().any(|(m, _, _)| *m == Move::Smelt));
        let furnace = Inv { furnace: true, ..no_furnace };
        assert!(moves(&g, &at(furnace)).iter().any(|(m, _, _)| *m == Move::Smelt));
    }
}
