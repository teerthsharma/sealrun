use sealrun_topo::betti::{betti, Betti};
use sealrun_topo::flood::islands;
use sealrun_world::grid::{Grid, Tile};

// Floor is 4-connected, walls are 8-connected: corner contact joins walls, never floor.
fn walls(w: u32, h: u32, stones: &[(u32, u32)]) -> Grid {
    let mut g = Grid::new(w, h);
    for &(x, y) in stones {
        g.set(x, y, Tile::Stone);
    }
    g
}

#[test]
fn betti_dual_connectivity_corner_touch() {
    let cases = [
        (walls(2, 2, &[(1, 0), (0, 1)]), 2, 0),
        (walls(3, 3, &[(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)]), 4, 0),
        (walls(7, 7, &[(2, 2), (3, 3)]), 1, 1),
        (walls(7, 7, &[(2, 2), (3, 3), (4, 2)]), 1, 1),
        (walls(8, 8, &[(2, 2), (5, 5)]), 1, 2),
    ];
    for (g, b0, b1) in cases {
        assert_eq!(betti(&g), Betti { b0, b1 });
        assert_eq!(islands(&g), b0);
    }
}
