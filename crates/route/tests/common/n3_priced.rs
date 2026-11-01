use std::cmp::Reverse;
use std::collections::BinaryHeap;

/// Cheapest entry cost from `S` to `G`: air and goal 1, water `swim`, stone `dig`.
pub fn cheapest(map: &[&str], swim: u32, dig: u32) -> Option<u32> {
    let grid: Vec<&[u8]> = map.iter().map(|row| row.as_bytes()).collect();
    let (h, w) = (grid.len(), grid.first()?.len());
    let find = |tile: u8| (0..h * w).find(|&i| grid[i / w][i % w] == tile);
    let start = find(b'S')?;
    let goal = find(b'G')?;
    let mut dist = vec![u32::MAX; h * w];
    let mut heap = BinaryHeap::new();
    dist[start] = 0;
    heap.push(Reverse((0, start)));
    while let Some(Reverse((d, i))) = heap.pop() {
        if i == goal {
            return Some(d);
        }
        if d > dist[i] {
            continue;
        }
        let (y, x) = (i / w, i % w);
        let next = [
            (y > 0).then(|| i - w),
            (y + 1 < h).then(|| i + w),
            (x > 0).then(|| i - 1),
            (x + 1 < w).then(|| i + 1),
        ];
        for j in next.into_iter().flatten() {
            let step = match grid[j / w][j % w] {
                b'#' => dig,
                b'~' => swim,
                _ => 1,
            };
            let nd = d + step;
            if nd < dist[j] {
                dist[j] = nd;
                heap.push(Reverse((nd, j)));
            }
        }
    }
    None
}
