use crate::delta::{chi_delta, mask_at};
use sealrun_world::grid::Grid;

const N4: [(i64, i64); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct DigPreview {
    pub joins: usize,
    pub d_b0: i64,
    pub d_b1: i64,
}

pub fn preview_mine(grid: &Grid, x: u32, y: u32) -> DigPreview {
    if grid.get(x, y).is_open() {
        return DigPreview { joins: 0, d_b0: 0, d_b1: 0 };
    }
    let w = grid.w() as usize;
    let mut seen = vec![false; w * grid.h() as usize];
    let mut stack = Vec::new();
    let mut joins = 0usize;
    for (dx, dy) in N4 {
        let (nx, ny) = (x as i64 + dx, y as i64 + dy);
        if !grid.in_bounds(nx, ny) || !grid.get(nx as u32, ny as u32).is_open() {
            continue;
        }
        let start = ny as usize * w + nx as usize;
        if seen[start] {
            continue;
        }
        joins += 1;
        seen[start] = true;
        stack.push((nx as u32, ny as u32));
        while let Some((cx, cy)) = stack.pop() {
            for (ex, ey) in N4 {
                let (qx, qy) = (cx as i64 + ex, cy as i64 + ey);
                if !grid.in_bounds(qx, qy) || !grid.get(qx as u32, qy as u32).is_open() {
                    continue;
                }
                let q = qy as usize * w + qx as usize;
                if !seen[q] {
                    seen[q] = true;
                    stack.push((qx as u32, qy as u32));
                }
            }
        }
    }
    // ponytail: flood fill costs O(island) per preview; upgrade to Surgery's union-find `find` once it is exposed.
    let d_b0 = 1 - joins as i64;
    let d_b1 = d_b0 - chi_delta(mask_at(grid, x, y));
    DigPreview { joins, d_b0, d_b1 }
}

#[cfg(test)]
mod tests {
    use super::{preview_mine, DigPreview};
    use crate::surgery::Surgery;
    use sealrun_world::gen::generate;
    use sealrun_world::grid::{Grid, Tile};

    fn delta_by_apply(grid: &Grid, x: u32, y: u32) -> (i64, i64) {
        let before = Surgery::new(grid.clone()).betti();
        let mut s = Surgery::new(grid.clone());
        s.mine(x, y);
        let after = s.betti();
        (after.b0 as i64 - before.b0 as i64, after.b1 as i64 - before.b1 as i64)
    }

    #[test]
    fn preview_matches_apply() {
        let mut row = Grid::new(3, 1);
        row.set(1, 0, Tile::Stone);
        let p = preview_mine(&row, 1, 0);
        assert_eq!(p, DigPreview { joins: 2, d_b0: -1, d_b1: 0 });
        assert_eq!((p.d_b0, p.d_b1), delta_by_apply(&row, 1, 0));

        let mut ring = Grid::new(3, 3);
        ring.set(1, 1, Tile::Stone);
        ring.set(1, 0, Tile::Stone);
        let p = preview_mine(&ring, 1, 0);
        assert_eq!(p, DigPreview { joins: 1, d_b0: 0, d_b1: 1 });
        assert_eq!((p.d_b0, p.d_b1), delta_by_apply(&ring, 1, 0));

        assert_eq!(
            preview_mine(&Grid::new(3, 3), 0, 0),
            DigPreview { joins: 0, d_b0: 0, d_b1: 0 }
        );

        let mut dug = 0usize;
        let mut state = 0x2545_F491_4F6C_DD1Du64;
        for seed in 0..20u64 {
            let grid = generate(seed, 32, 32);
            let before = Surgery::new(grid.clone()).betti();
            for _ in 0..200 {
                state = state
                    .wrapping_mul(6_364_136_223_846_793_005)
                    .wrapping_add(1_442_695_040_888_963_407);
                let x = (state >> 33) as u32 % 32;
                let y = (state >> 45) as u32 % 32;
                dug += (!grid.get(x, y).is_open()) as usize;
                let p = preview_mine(&grid, x, y);
                let mut s = Surgery::new(grid.clone());
                s.mine(x, y);
                let after = s.betti();
                assert_eq!(p.d_b0, after.b0 as i64 - before.b0 as i64, "seed {seed} cell ({x},{y})");
                assert_eq!(p.d_b1, after.b1 as i64 - before.b1 as i64, "seed {seed} cell ({x},{y})");
            }
        }
        assert!(dug > 0);
    }
}
