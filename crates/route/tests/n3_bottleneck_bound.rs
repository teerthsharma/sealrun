#[path = "common/n3_priced.rs"]
mod n3_priced;

use n3_priced::cheapest;
use std::cmp::Reverse;
use std::collections::BinaryHeap;

const HAND: [&str; 5] = ["...#...", "...~...", "S..#..G", "...#...", "......."];
const SEALED: [&str; 2] = ["S.#", "##G"];
const ADJACENT: [&str; 1] = ["SG"];

fn price(tile: u8, swim: u32, dig: u32) -> u32 {
    match tile {
        b'#' => dig,
        b'~' => swim,
        _ => 1,
    }
}

/// Per-step prices of one optimal route, using the cost model of `cheapest`.
fn route_steps(map: &[&str], swim: u32, dig: u32) -> Option<Vec<u32>> {
    let grid: Vec<&[u8]> = map.iter().map(|row| row.as_bytes()).collect();
    let (h, w) = (grid.len(), grid.first()?.len());
    let find = |tile: u8| (0..h * w).find(|&i| grid[i / w][i % w] == tile);
    let start = find(b'S')?;
    let goal = find(b'G')?;
    let mut dist = vec![u32::MAX; h * w];
    let mut prev = vec![usize::MAX; h * w];
    let mut heap = BinaryHeap::new();
    dist[start] = 0;
    heap.push(Reverse((0u32, start)));
    while let Some(Reverse((d, i))) = heap.pop() {
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
            let nd = d + price(grid[j / w][j % w], swim, dig);
            if nd < dist[j] {
                dist[j] = nd;
                prev[j] = i;
                heap.push(Reverse((nd, j)));
            }
        }
    }
    if dist[goal] == u32::MAX {
        return None;
    }
    let mut steps = Vec::new();
    let mut at = goal;
    while at != start {
        steps.push(price(grid[at / w][at % w], swim, dig));
        at = prev[at];
    }
    steps.reverse();
    Some(steps)
}

#[test]
fn route_cost_at_least_bottleneck() {
    let grids: [(&str, &[&str]); 3] = [
        ("HAND", &HAND[..]),
        ("SEALED", &SEALED[..]),
        ("ADJACENT", &ADJACENT[..]),
    ];
    let (mut routes, mut equal) = (0usize, 0usize);
    for (name, map) in grids {
        for swim in 1..=9 {
            for dig in 1..=9 {
                let steps = route_steps(map, swim, dig).expect("goal reachable");
                let total: u32 = steps.iter().sum();
                let dearest = steps.iter().copied().max().expect("route has a step");
                assert!(
                    total >= dearest,
                    "{name} swim={swim} dig={dig}: total {total} >= dearest {dearest}, steps {steps:?}"
                );
                assert_eq!(
                    Some(total),
                    cheapest(map, swim, dig),
                    "{name} swim={swim} dig={dig}: route sum disagrees with cheapest"
                );
                if steps.len() == 1 {
                    assert_eq!(total, dearest, "{name} swim={swim} dig={dig}: single step");
                    equal += 1;
                }
                routes += 1;
            }
        }
    }
    assert!(routes > 0, "no route was checked");
    println!("routes checked: {routes}, with equality (single step): {equal}");
}
