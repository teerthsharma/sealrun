use sealrun_world::grid::{Grid, GridError, Tile};

fn tile(v: u8) -> Tile {
    match v {
        0 => Tile::Air,
        1 => Tile::Stone,
        2 => Tile::Water,
        3 => Tile::Tree,
        4 => Tile::Iron,
        5 => Tile::Goal,
        other => panic!("tile {other} not in contract table"),
    }
}

#[test]
fn loads_contract_grid_tiles() {
    let bytes: &[u8] = include_bytes!("fixtures/contract_4x3.grid");
    let g = Grid::from_bytes(bytes).expect("contract grid decodes");
    assert_eq!(g.w(), 4);
    assert_eq!(g.h(), 3);
    let rows: [[u8; 4]; 3] = [[0, 1, 2, 3], [4, 5, 0, 1], [2, 3, 4, 5]];
    for (y, row) in rows.iter().enumerate() {
        for (x, &v) in row.iter().enumerate() {
            assert_eq!(g.get(x as u32, y as u32), tile(v), "cell ({x}, {y})");
        }
    }
    assert_eq!(g.to_bytes(), bytes);

    let mut bad = bytes.to_vec();
    bad[8] = 6;
    assert_eq!(Grid::from_bytes(&bad), Err(GridError::UnknownTile(6)));

    assert_eq!(Grid::from_bytes(&bytes[..7]), Err(GridError::ShortHeader));
    assert_eq!(
        Grid::from_bytes(&bytes[..bytes.len() - 1]),
        Err(GridError::LengthMismatch)
    );
}
