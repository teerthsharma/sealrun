#[repr(u8)]
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Tile {
    Air = 0,
    Stone = 1,
    Water = 2,
    Tree = 3,
    Iron = 4,
    Goal = 5,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum GridError {
    ShortHeader,
    LengthMismatch,
    UnknownTile(u8),
}

#[derive(Clone, PartialEq, Eq, Debug)]
pub struct Grid {
    w: u32,
    h: u32,
    cells: Vec<Tile>,
}

const HEADER: usize = 8;

impl Grid {
    pub fn new(w: u32, h: u32) -> Self {
        Self { w, h, cells: vec![Tile::Air; w as usize * h as usize] }
    }

    pub fn w(&self) -> u32 {
        self.w
    }

    pub fn h(&self) -> u32 {
        self.h
    }

    pub fn get(&self, x: u32, y: u32) -> Tile {
        self.cells[y as usize * self.w as usize + x as usize]
    }

    pub fn set(&mut self, x: u32, y: u32, t: Tile) {
        self.cells[y as usize * self.w as usize + x as usize] = t;
    }

    pub fn in_bounds(&self, x: i64, y: i64) -> bool {
        x >= 0 && y >= 0 && x < self.w as i64 && y < self.h as i64
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut out = Vec::with_capacity(HEADER + self.cells.len());
        out.extend_from_slice(&self.w.to_le_bytes());
        out.extend_from_slice(&self.h.to_le_bytes());
        out.extend(self.cells.iter().map(|&t| t as u8));
        out
    }

    pub fn from_bytes(bytes: &[u8]) -> Result<Grid, GridError> {
        if bytes.len() < HEADER {
            return Err(GridError::ShortHeader);
        }
        let w = u32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]);
        let h = u32::from_le_bytes([bytes[4], bytes[5], bytes[6], bytes[7]]);
        let body = &bytes[HEADER..];
        if body.len() as u64 != w as u64 * h as u64 {
            return Err(GridError::LengthMismatch);
        }
        let cells = body.iter().map(|&b| tile_from_byte(b)).collect::<Result<Vec<_>, _>>()?;
        Ok(Grid { w, h, cells })
    }
}

fn tile_from_byte(b: u8) -> Result<Tile, GridError> {
    Ok(match b {
        0 => Tile::Air,
        1 => Tile::Stone,
        2 => Tile::Water,
        3 => Tile::Tree,
        4 => Tile::Iron,
        5 => Tile::Goal,
        _ => return Err(GridError::UnknownTile(b)),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pattern_tile(v: u32) -> Tile {
        match v {
            0 => Tile::Air,
            1 => Tile::Stone,
            2 => Tile::Water,
            3 => Tile::Tree,
            4 => Tile::Iron,
            _ => Tile::Goal,
        }
    }

    #[test]
    fn grid_bytes_roundtrip() {
        let (w, h) = (37u32, 23u32);
        let mut g = Grid::new(w, h);
        for y in 0..h {
            for x in 0..w {
                g.set(x, y, pattern_tile((x * 7 + y * 3) % 6));
            }
        }

        let bytes = g.to_bytes();
        let back = Grid::from_bytes(&bytes).expect("roundtrip decodes");
        assert_eq!(back, g);
        assert_eq!(back.to_bytes(), bytes);

        assert!(Grid::from_bytes(&bytes[..bytes.len() - 1]).is_err());

        let mut bad = bytes.clone();
        bad[8] = 9;
        assert_eq!(Grid::from_bytes(&bad), Err(GridError::UnknownTile(9)));
    }
}
