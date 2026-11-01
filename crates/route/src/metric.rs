use sealrun_world::grid::Tile;

pub const WALK_TICKS: u64 = 5;
pub const CRAFT_TICKS: u64 = 20;

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Tool {
    Hand,
    Wood,
    Stone,
    Iron,
}

impl Tool {
    fn speed(self) -> u64 {
        match self {
            Tool::Hand => 1,
            Tool::Wood => 2,
            Tool::Stone => 4,
            Tool::Iron => 6,
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Dig {
    pub ticks: u64,
    pub drops: bool,
}

pub fn dig(tile: Tile, tool: Tool) -> Option<Dig> {
    let (h10, speed, drops): (u64, u64, bool) = match tile {
        Tile::Stone => (15, tool.speed(), tool >= Tool::Wood),
        Tile::Tree => (20, 1, true),
        Tile::Iron => (30, tool.speed(), tool >= Tool::Stone),
        Tile::Air | Tile::Water | Tile::Goal => return None,
    };
    let ticks = if drops { (h10 * 3).div_ceil(speed) } else { (h10 * 10).div_ceil(speed) };
    Some(Dig { ticks, drops })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stone_is_faster_with_pickaxe() {
        assert_eq!(dig(Tile::Stone, Tool::Hand), Some(Dig { ticks: 150, drops: false }));
        assert_eq!(dig(Tile::Stone, Tool::Wood), Some(Dig { ticks: 23, drops: true }));
        assert_eq!(dig(Tile::Stone, Tool::Stone), Some(Dig { ticks: 12, drops: true }));
        assert_eq!(dig(Tile::Stone, Tool::Iron), Some(Dig { ticks: 8, drops: true }));
        assert_eq!(dig(Tile::Tree, Tool::Hand), Some(Dig { ticks: 60, drops: true }));
        assert_eq!(dig(Tile::Tree, Tool::Iron), Some(Dig { ticks: 60, drops: true }));
        assert_eq!(dig(Tile::Iron, Tool::Wood), Some(Dig { ticks: 150, drops: false }));
        assert_eq!(dig(Tile::Iron, Tool::Stone), Some(Dig { ticks: 23, drops: true }));
        assert_eq!(dig(Tile::Iron, Tool::Iron), Some(Dig { ticks: 15, drops: true }));
        for tile in [Tile::Air, Tile::Water, Tile::Goal] {
            assert_eq!(dig(tile, Tool::Iron), None);
        }
        let tools = [Tool::Hand, Tool::Wood, Tool::Stone, Tool::Iron];
        for pair in tools.windows(2) {
            let slower = dig(Tile::Stone, pair[0]).unwrap().ticks;
            let faster = dig(Tile::Stone, pair[1]).unwrap().ticks;
            assert!(faster <= slower);
        }
    }
}
