use crate::grid::{Grid, Tile};
use crate::noise::value_noise;
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
