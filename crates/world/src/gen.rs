use crate::grid::{Grid, Tile};
use crate::noise::value_noise;
use std::cmp::Reverse;
use crate::rng::hash;

pub fn generate(seed: u64, w: u32, h: u32) -> Grid {
    let mut g = Grid::new(w, h);
    for y in 0..h {
        for x in 0..w {
            let (xi, yi) = (i64::from(x), i64::from(y));
            let coarse = value_noise(seed, xi, yi, 16);
            let fine = value_noise(seed ^ 0x9e37_79b9_7f4a_7c15, xi, yi, 4);
            let height = (3 * coarse + fine) / 4;
            let tile = if height < 20000 {
                Tile::Water
            } else if height < 40000 {
                if hash(seed ^ 0x7472_6565, xi, yi).is_multiple_of(23) {
                    Tile::Tree
                } else {
                    Tile::Air
                }
            } else if hash(seed ^ 0x6972_6f6e, xi, yi).is_multiple_of(31) {
                Tile::Iron
            } else {
                Tile::Stone
            };
            g.set(x, y, tile);
        }
    }
    g
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct World {
    pub grid: Grid,
    pub start: (u32, u32),
    pub goal: (u32, u32),
}

pub fn world(seed: u64, w: u32, h: u32) -> World {
    let mut grid = generate(seed, w, h);
    let mut open = cells(w, h).filter(|&c| grid.get(c.0, c.1).is_open()).count();
    while open < 2 {
        let c = nearest(w, h, (w / 2, h / 2), |c| !grid.get(c.0, c.1).is_open())
            .expect("a closed cell exists");
        grid.set(c.0, c.1, Tile::Air);
        open += 1;
    }
    let start = nearest(w, h, (w / 2, h / 2), |c| grid.get(c.0, c.1).is_open())
        .expect("an open cell exists");
    let goal = cells(w, h)
        .filter(|&c| grid.get(c.0, c.1).is_open())
        .min_by_key(|&c| Reverse(dist(start, c)))
        .expect("an open cell exists");
    grid.set(goal.0, goal.1, Tile::Goal);
    if !has(&grid, w, h, |t| t == Tile::Tree) {
        let c = nearest(w, h, start, |c| {
            grid.get(c.0, c.1) == Tile::Air && c != start && c != goal
        })
        .or_else(|| nearest(w, h, start, |c| c != start && c != goal))
        .expect("a free cell exists");
        grid.set(c.0, c.1, Tile::Tree);
    }
    if !has(&grid, w, h, |t| t == Tile::Iron) {
        let c = nearest(w, h, start, |c| grid.get(c.0, c.1) == Tile::Stone)
            .or_else(|| {
                nearest(w, h, start, |c| {
                    c != start && c != goal && grid.get(c.0, c.1) != Tile::Tree
                })
            })
            .expect("a free cell exists");
        grid.set(c.0, c.1, Tile::Iron);
    }
    World { grid, start, goal }
}

fn cells(w: u32, h: u32) -> impl Iterator<Item = (u32, u32)> {
    (0..h).flat_map(move |y| (0..w).map(move |x| (x, y)))
}

fn dist(a: (u32, u32), b: (u32, u32)) -> u64 {
    u64::from(a.0.abs_diff(b.0)) + u64::from(a.1.abs_diff(b.1))
}

fn nearest(
    w: u32,
    h: u32,
    from: (u32, u32),
    pred: impl Fn((u32, u32)) -> bool,
) -> Option<(u32, u32)> {
    cells(w, h).filter(|&c| pred(c)).min_by_key(|&c| dist(from, c))
}

fn has(g: &Grid, w: u32, h: u32, pred: impl Fn(Tile) -> bool) -> bool {
    cells(w, h).any(|c| pred(g.get(c.0, c.1)))
}

#[cfg(test)]
mod tests {
    use super::generate;
    use crate::grid::Tile;

    #[test]
    fn same_seed_same_world() {
        let a = generate(7, 64, 64);
        assert_eq!(a.to_bytes(), generate(7, 64, 64).to_bytes());
        assert_ne!(a.to_bytes(), generate(8, 64, 64).to_bytes());
        let has = |t: Tile| (0..64).any(|y| (0..64).any(|x| a.get(x, y) == t));
        for t in [Tile::Air, Tile::Stone, Tile::Water, Tile::Tree, Tile::Iron] {
            assert!(has(t), "seed 7 has no {t:?}");
        }
    }
}
