use sealrun_world::grid::Grid;

pub fn euler(grid: &Grid) -> i64 {
    let (w, h) = (grid.w(), grid.h());
    let open = |x: u32, y: u32| grid.get(x, y).is_open();
    let mut chi = 0i64;
    for y in 0..h {
        for x in 0..w {
            if !open(x, y) {
                continue;
            }
            chi += 1;
            if x + 1 < w && open(x + 1, y) {
                chi -= 1;
            }
            if y + 1 < h && open(x, y + 1) {
                chi -= 1;
            }
            if x + 1 < w && y + 1 < h && open(x + 1, y) && open(x, y + 1) && open(x + 1, y + 1) {
                chi += 1;
            }
        }
    }
    chi
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
    fn euler_of_ring_is_zero() {
        assert_eq!(euler(&from_rows(&["...", ".#.", "..."])), 0);
        assert_eq!(euler(&from_rows(&[".....", ".....", ".....", ".....", "....."])), 1);
        assert_eq!(euler(&from_rows(&[".....", ".....", "..#..", ".....", "....."])), 0);

        let mut checker = Grid::new(4, 4);
        for y in 0..4u32 {
            for x in 0..4u32 {
                if (x + y) % 2 != 0 {
                    checker.set(x, y, Tile::Stone);
                }
            }
        }
        assert_eq!(euler(&checker), 8);

        assert_eq!(euler(&from_rows(&["...#...", ".#.#.#.", "...#..."])), 0);
        assert_eq!(euler(&Grid::new(0, 0)), 0);
        assert_eq!(euler(&Grid::new(2, 2)), 1);
    }
}
