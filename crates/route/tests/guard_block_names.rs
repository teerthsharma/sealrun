use sealrun_route::state::{moves, Inv, Move, State};
use sealrun_world::grid::{Grid, GridError, Tile};

fn one_by_one(b: u8) -> Vec<u8> {
    vec![1, 0, 0, 0, 1, 0, 0, 0, b]
}

#[test]
fn guard_block_names() {
    for b in 0..=255u8 {
        let got = Grid::from_bytes(&one_by_one(b));
        if b <= 5 {
            assert!(got.is_ok(), "byte {b} should decode");
        } else {
            assert_eq!(got, Err(GridError::UnknownTile(b)), "byte {b}");
        }
    }

    let open: Vec<Tile> = [Tile::Air, Tile::Stone, Tile::Water, Tile::Tree, Tile::Iron, Tile::Goal]
        .into_iter()
        .filter(|t| t.is_open())
        .collect();
    assert_eq!(open, vec![Tile::Air, Tile::Goal]);

    let mut g = Grid::new(3, 1);
    g.set(1, 0, Tile::Water);
    let s = State { pos: (0, 0), inv: Inv::EMPTY };
    let ms: Vec<Move> = moves(&g, &s).into_iter().map(|(m, _, _)| m).collect();
    assert!(!ms.contains(&Move::Walk((1, 0))));
    assert!(!ms.contains(&Move::Mine((1, 0))));
}
