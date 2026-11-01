use crate::euler::euler;
use crate::uf::UnionFind;
use sealrun_world::grid::Grid;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub struct Betti {
    pub b0: usize,
    pub b1: usize,
}

pub fn betti(grid: &Grid) -> Betti {
    let (w, h) = (grid.w(), grid.h());
    let n = w as usize * h as usize;
    let open = |x: u32, y: u32| grid.get(x, y).is_open();
    let idx = |x: u32, y: u32| y as usize * w as usize + x as usize;
    let mut uf = UnionFind::new(n);
    let mut open_cells = 0usize;
    for y in 0..h {
        for x in 0..w {
            if !open(x, y) {
                continue;
            }
            open_cells += 1;
            if x + 1 < w && open(x + 1, y) {
                uf.union(idx(x, y), idx(x + 1, y));
            }
            if y + 1 < h && open(x, y + 1) {
                uf.union(idx(x, y), idx(x, y + 1));
            }
        }
    }
    let b0 = uf.sets() - (n - open_cells);
    let b1 = b0 as i64 - euler(grid);
    assert!(b1 >= 0, "euler characteristic exceeds component count");
    Betti { b0, b1: b1 as usize }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sealrun_world::grid::Tile;

    fn from_rows(rows: &[&str]) -> Grid {
        let h = rows.len() as u32;
        let w = rows.first().map_or(0, |r| r.len()) as u32;
        let mut g = Grid::new(w, h);
        for (y, row) in rows.iter().enumerate() {
            for (x, c) in row.bytes().enumerate() {
                if c == b'#' {
                    g.set(x as u32, y as u32, Tile::Stone);
                }
            }
        }
        g
    }

    #[test]
    fn betti_of_ring_is_one_one() {
        assert_eq!(betti(&from_rows(&["...", ".#.", "..."])), Betti { b0: 1, b1: 1 });
        assert_eq!(
            betti(&from_rows(&[".....", ".....", ".....", ".....", "....."])),
            Betti { b0: 1, b1: 0 }
        );
        assert_eq!(
            betti(&from_rows(&[".....", ".....", "..#..", ".....", "....."])),
            Betti { b0: 1, b1: 1 }
        );
        assert_eq!(
            betti(&from_rows(&["...#...", ".#.#.#.", "...#..."])),
            Betti { b0: 2, b1: 2 }
        );

        let mut checker = Grid::new(4, 4);
        for y in 0..4u32 {
            for x in 0..4u32 {
                if (x + y) % 2 != 0 {
                    checker.set(x, y, Tile::Stone);
                }
            }
        }
        assert_eq!(betti(&checker), Betti { b0: 8, b1: 0 });

        assert_eq!(betti(&from_rows(&[])), Betti { b0: 0, b1: 0 });

        assert_eq!(
            betti(&from_rows(&[
                ".......", ".......", "..#....", ".......", "....#..", ".......", ".......",
            ])),
            Betti { b0: 1, b1: 2 }
        );
        assert_eq!(
            betti(&from_rows(&[
                ".......", ".......", "..#....", "...#...", ".......", ".......", ".......",
            ])),
            Betti { b0: 1, b1: 1 }
        );
    }
}
