use sealrun_world::grid::Grid;

const NEIGHBOURS: [(i64, i64); 8] = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)];

pub fn mask_at(grid: &Grid, x: u32, y: u32) -> u8 {
    NEIGHBOURS.iter().enumerate().fold(0u8, |m, (bit, &(dx, dy))| {
        let (nx, ny) = (x as i64 + dx, y as i64 + dy);
        if grid.in_bounds(nx, ny) && grid.get(nx as u32, ny as u32).is_open() {
            m | (1 << bit)
        } else {
            m
        }
    })
}

pub fn chi_delta(mask: u8) -> i64 {
    const BLOCKS: [u8; 4] = [0x0B, 0x16, 0x68, 0xD0];
    let open4 = (mask & 0x5A).count_ones() as i64;
    let blocks = BLOCKS.iter().filter(|&&b| mask & b == b).count() as i64;
    1 - open4 + blocks
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::euler::euler;
    use sealrun_world::grid::Tile;

    const OFFSETS: [(i64, i64); 8] = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)];

    fn place(grid: &mut Grid, cx: u32, cy: u32, mask: u8) {
        for (bit, (dx, dy)) in OFFSETS.iter().enumerate() {
            let (x, y) = (cx as i64 + dx, cy as i64 + dy);
            let open = (mask >> bit) & 1 == 1;
            grid.set(x as u32, y as u32, if open { Tile::Air } else { Tile::Stone });
        }
    }

    #[test]
    fn chi_delta_matches_recompute_all_256() {
        for mask in 0..=255u8 {
            let mut g = Grid::new(3, 3);
            place(&mut g, 1, 1, mask);
            g.set(1, 1, Tile::Stone);
            let e0 = euler(&g);
            g.set(1, 1, Tile::Air);
            let e1 = euler(&g);
            assert_eq!(e1 - e0, chi_delta(mask), "mask {mask:#010b}");
            assert_eq!(mask_at(&g, 1, 1), mask, "mask {mask:#010b}");
        }

        let mut wide = Grid::new(5, 5);
        for y in 0..5u32 {
            for x in 0..5u32 {
                if (x + y) % 2 == 0 {
                    wide.set(x, y, Tile::Stone);
                }
            }
        }
        let mask = 0x5A;
        place(&mut wide, 2, 2, mask);
        wide.set(2, 2, Tile::Stone);
        let e0 = euler(&wide);
        wide.set(2, 2, Tile::Air);
        let e1 = euler(&wide);
        assert_eq!(e1 - e0, chi_delta(mask));
        assert_eq!(mask_at(&wide, 2, 2), mask);

        let all_open = Grid::new(3, 3);
        assert_eq!(mask_at(&all_open, 0, 0), 0b1101_0000);
        assert_eq!(mask_at(&all_open, 2, 2), 0b0000_1011);
    }
}
