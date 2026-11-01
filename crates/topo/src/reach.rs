use crate::uf::UnionFind;
use sealrun_world::grid::Grid;

pub struct Reach {
    grid: Grid,
    uf: UnionFind,
}

impl Reach {
    pub fn new(grid: &Grid) -> Reach {
        let (w, h) = (grid.w(), grid.h());
        let mut uf = UnionFind::new(w as usize * h as usize);
        for y in 0..h {
            for x in 0..w {
                if !grid.get(x, y).is_open() {
                    continue;
                }
                let i = y as usize * w as usize + x as usize;
                if x + 1 < w && grid.get(x + 1, y).is_open() {
                    uf.union(i, i + 1);
                }
                if y + 1 < h && grid.get(x, y + 1).is_open() {
                    uf.union(i, i + w as usize);
                }
            }
        }
        Reach { grid: grid.clone(), uf }
    }

    fn open_index(&self, (x, y): (u32, u32)) -> Option<usize> {
        (x < self.grid.w() && y < self.grid.h() && self.grid.get(x, y).is_open())
            .then(|| y as usize * self.grid.w() as usize + x as usize)
    }

    pub fn can_walk(&mut self, from: (u32, u32), to: (u32, u32)) -> bool {
        match (self.open_index(from), self.open_index(to)) {
            (Some(a), Some(b)) => self.uf.find(a) == self.uf.find(b),
            _ => false,
        }
    }

    pub fn can_mine(&mut self, grid: &Grid, from: (u32, u32), item: (u32, u32)) -> bool {
        let (x, y) = (item.0 as i64, item.1 as i64);
        [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            .into_iter()
            .filter(|&(nx, ny)| grid.in_bounds(nx, ny))
            .any(|(nx, ny)| self.can_walk(from, (nx as u32, ny as u32)))
    }
}

#[cfg(test)]
mod tests {
    use super::Reach;
    use sealrun_world::grid::{Grid, Tile};

    #[test]
    fn sealed_pocket_is_unreachable() {
        let mut grid = Grid::new(9, 9);
        for i in 3..=7 {
            for &(x, y) in &[(i, 3), (i, 7), (3, i), (7, i)] {
                grid.set(x, y, Tile::Stone);
            }
        }
        grid.set(5, 5, Tile::Iron);
        grid.set(0, 1, Tile::Iron);

        let mut reach = Reach::new(&grid);
        assert!(!reach.can_mine(&grid, (0, 0), (5, 5)));
        assert!(!reach.can_walk((0, 0), (4, 4)));
        assert!(reach.can_walk((0, 0), (8, 8)));
        assert!(reach.can_mine(&grid, (0, 0), (0, 1)));

        grid.set(3, 5, Tile::Air);
        let mut reach = Reach::new(&grid);
        assert!(reach.can_mine(&grid, (0, 0), (5, 5)));
        assert!(reach.can_walk((0, 0), (4, 4)));
        assert!(reach.can_mine(&grid, (0, 0), (0, 1)));
    }
}
