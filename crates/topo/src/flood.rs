use sealrun_world::grid::Grid;

pub fn islands(grid: &Grid) -> usize {
    let (w, h) = (grid.w() as usize, grid.h() as usize);
    let open = |i: usize| grid.get((i % w) as u32, (i / w) as u32).is_open();
    let mut seen = vec![false; w * h];
    let mut stack = Vec::new();
    let mut count = 0;
    for start in 0..w * h {
        if seen[start] || !open(start) {
            continue;
        }
        count += 1;
        seen[start] = true;
        stack.push(start);
        while let Some(i) = stack.pop() {
            let (x, y) = (i % w, i / w);
            let neighbours = [
                (x > 0).then(|| i - 1),
                (x + 1 < w).then(|| i + 1),
                (y > 0).then(|| i - w),
                (y + 1 < h).then(|| i + w),
            ];
            for j in neighbours.into_iter().flatten() {
                if !seen[j] && open(j) {
                    seen[j] = true;
                    stack.push(j);
                }
            }
        }
    }
    count
}

#[cfg(test)]
mod tests {
    use super::*;
    use sealrun_world::grid::Tile;

    fn paint(w: u32, h: u32, f: impl Fn(u32, u32) -> Tile) -> Grid {
        let mut g = Grid::new(w, h);
        for y in 0..h {
            for x in 0..w {
                g.set(x, y, f(x, y));
            }
        }
        g
    }

    #[test]
    fn flood_counts_islands() {
        assert_eq!(islands(&paint(5, 5, |_, _| Tile::Air)), 1);
        assert_eq!(
            islands(&paint(4, 4, |x, y| if (x + y) % 2 == 0 { Tile::Air } else { Tile::Stone })),
            8
        );
        assert_eq!(islands(&paint(7, 3, |x, _| if x == 3 { Tile::Stone } else { Tile::Air })), 2);
        assert_eq!(islands(&Grid::new(0, 0)), 0);
        assert_eq!(islands(&paint(4, 4, |_, _| Tile::Stone)), 0);
        assert_eq!(
            islands(&paint(3, 3, |x, y| if x == 1 && y == 1 { Tile::Stone } else { Tile::Air })),
            1
        );
    }
}
