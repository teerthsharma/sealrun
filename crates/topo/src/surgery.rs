use crate::betti::Betti;
use crate::delta::{chi_delta, mask_at};
use crate::euler::euler;
use crate::uf::UnionFind;
use sealrun_world::grid::{Grid, Tile};

const N4: [(i64, i64); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];

pub struct Surgery {
    grid: Grid,
    uf: UnionFind,
    b0: usize,
    chi: i64,
}

impl Surgery {
    pub fn new(grid: Grid) -> Surgery {
        let (w, h) = (grid.w(), grid.h());
        let n = w as usize * h as usize;
        let mut uf = UnionFind::new(n);
        let mut open_cells = 0usize;
        for y in 0..h {
            for x in 0..w {
                if !grid.get(x, y).is_open() {
                    continue;
                }
                open_cells += 1;
                let i = y as usize * w as usize + x as usize;
                if x + 1 < w && grid.get(x + 1, y).is_open() {
                    uf.union(i, i + 1);
                }
                if y + 1 < h && grid.get(x, y + 1).is_open() {
                    uf.union(i, i + w as usize);
                }
            }
        }
        let b0 = uf.sets() - (n - open_cells);
        let chi = euler(&grid);
        Surgery { grid, uf, b0, chi }
    }

    pub fn betti(&self) -> Betti {
        Betti { b0: self.b0, b1: (self.b0 as i64 - self.chi) as usize }
    }

    pub fn grid(&self) -> &Grid {
        &self.grid
    }

    pub fn mine(&mut self, x: u32, y: u32) {
        if self.grid.get(x, y).is_open() {
            return;
        }
        self.chi += chi_delta(mask_at(&self.grid, x, y));
        self.grid.set(x, y, Tile::Air);
        let w = self.grid.w() as usize;
        let i = y as usize * w + x as usize;
        let mut merged = 0usize;
        for (dx, dy) in N4 {
            let (nx, ny) = (x as i64 + dx, y as i64 + dy);
            if self.grid.in_bounds(nx, ny) && self.grid.get(nx as u32, ny as u32).is_open() {
                merged += self.uf.union(i, ny as usize * w + nx as usize) as usize;
            }
        }
        self.b0 = self.b0 + 1 - merged;
    }
}

#[cfg(test)]
mod tests {
    use super::Surgery;
    use crate::betti::{betti, Betti};
    use sealrun_world::gen::generate;
    use sealrun_world::grid::{Grid, Tile};

    #[test]
    fn mine_matches_full_recompute() {
        let mut ring = Grid::new(3, 3);
        ring.set(1, 1, Tile::Stone);
        let mut s = Surgery::new(ring);
        assert_eq!(s.betti(), Betti { b0: 1, b1: 1 });
        s.mine(1, 1);
        assert_eq!(s.betti(), Betti { b0: 1, b1: 0 });

        let mut row = Grid::new(5, 1);
        row.set(2, 0, Tile::Stone);
        let mut s = Surgery::new(row);
        assert_eq!(s.betti().b0, 2);
        s.mine(2, 0);
        assert_eq!(s.betti().b0, 1);

        for seed in 0..20u64 {
            let mut s = Surgery::new(generate(seed, 32, 32));
            let mut state = seed.wrapping_mul(0x9E37_79B9_7F4A_7C15) | 1;
            for step in 0..200 {
                state = state
                    .wrapping_mul(6_364_136_223_846_793_005)
                    .wrapping_add(1_442_695_040_888_963_407);
                let x = (state >> 33) as u32 % 32;
                let y = (state >> 45) as u32 % 32;
                s.mine(x, y);
                assert_eq!(s.betti(), betti(s.grid()), "seed {seed} step {step}");
            }
        }
    }
}
