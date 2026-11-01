use sealrun_topo::betti::{betti, Betti};
use sealrun_world::grid::{Grid, Tile};

fn stone_with_air(w: u32, h: u32, air: &[(u32, u32)]) -> Grid {
    let mut g = Grid::new(w, h);
    for y in 0..h {
        for x in 0..w {
            g.set(x, y, Tile::Stone);
        }
    }
    for &(x, y) in air {
        g.set(x, y, Tile::Air);
    }
    g
}

fn inverted(g: &Grid) -> Grid {
    let mut out = Grid::new(g.w(), g.h());
    for y in 0..g.h() {
        for x in 0..g.w() {
            let t = match g.get(x, y) {
                Tile::Air => Tile::Stone,
                Tile::Stone => Tile::Air,
                other => other,
            };
            out.set(x, y, t);
        }
    }
    out
}

fn caves(g: &Grid) -> usize {
    betti(&inverted(g)).b1
}

#[test]
fn betti_b2_enclosed_cavity_counts_once() {
    let bubble = stone_with_air(7, 7, &[(3, 3)]);
    assert_eq!(betti(&bubble), Betti { b0: 1, b1: 0 });
    assert_eq!(caves(&bubble), 1);

    let open = stone_with_air(7, 7, &[(3, 3), (3, 4), (3, 5), (3, 6)]);
    assert_eq!(caves(&open), 0);

    let two = stone_with_air(9, 9, &[(2, 2), (6, 6)]);
    assert_eq!(caves(&two), 2);

    let block: Vec<(u32, u32)> = (2..4).flat_map(|x| (2..4).map(move |y| (x, y))).collect();
    assert_eq!(caves(&stone_with_air(7, 7, &block)), 1);

    assert_eq!(caves(&stone_with_air(5, 5, &[])), 0);
}
