use sealrun_world::grid::{Grid, Tile};

/// The start: the air cell nearest the grid centre (ties: smaller y, then x).
/// The finish: the iron nearest that start, with an open neighbour to stand on.
pub fn start_finish(grid: &Grid) -> Option<((u32, u32), (u32, u32))> {
    let (w, h) = (grid.w(), grid.h());
    let cells = || (0..h).flat_map(move |y| (0..w).map(move |x| (x, y)));
    let (cx, cy) = ((w / 2) as i64, (h / 2) as i64);
    let start = cells()
        .filter(|&(x, y)| grid.get(x, y) == Tile::Air)
        .min_by_key(|&(x, y)| ((x as i64 - cx).abs() + (y as i64 - cy).abs(), y, x))?;
    let (sx, sy) = (start.0 as i64, start.1 as i64);
    let mut irons: Vec<(u32, u32)> = cells().filter(|&(x, y)| grid.get(x, y) == Tile::Iron).collect();
    irons.sort_by_key(|&(x, y)| ((x as i64 - sx).abs() + (y as i64 - sy).abs(), y, x));
    let finish = irons.iter().find_map(|&(x, y)| open_neighbour(grid, x, y))?;
    Some((start, finish))
}

fn open_neighbour(grid: &Grid, x: u32, y: u32) -> Option<(u32, u32)> {
    let (x, y) = (x as i64, y as i64);
    [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
        .into_iter()
        .find(|&(nx, ny)| grid.in_bounds(nx, ny) && grid.get(nx as u32, ny as u32).is_open())
        .map(|(nx, ny)| (nx as u32, ny as u32))
}
