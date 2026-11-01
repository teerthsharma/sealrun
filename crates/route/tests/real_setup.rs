mod common;

use common::start_finish;
use sealrun_world::grid::{Grid, Tile};

fn from_rows(rows: &[&str]) -> Grid {
    let h = rows.len() as u32;
    let w = rows[0].len() as u32;
    let mut g = Grid::new(w, h);
    for (y, row) in rows.iter().enumerate() {
        for (x, c) in row.chars().enumerate() {
            let t = match c {
                '.' => Tile::Air,
                '#' => Tile::Stone,
                'I' => Tile::Iron,
                other => panic!("unknown cell {other:?}"),
            };
            g.set(x as u32, y as u32, t);
        }
    }
    g
}

#[test]
fn start_and_finish_picked_on_hand_grid() {
    let tie = from_rows(&["##.#.", "#.##I", "#I###", "#####", "#####"]);
    assert_eq!(start_finish(&tie), Some(((2, 0), (4, 0))));

    let walled = from_rows(&["#####", "#####", "##.##", "I.###", "##I##"]);
    assert_eq!(start_finish(&walled), Some(((2, 2), (1, 3))));

    let walled_only = from_rows(&["#I#.#"]);
    assert_eq!(start_finish(&walled_only), None);

    let no_iron = from_rows(&["..#"]);
    assert_eq!(start_finish(&no_iron), None);

    let no_air = from_rows(&["#I#"]);
    assert_eq!(start_finish(&no_air), None);
}
