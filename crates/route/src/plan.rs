use crate::state::{moves, Move, State};
use sealrun_topo::reach::Reach;
use sealrun_world::grid::Grid;
use std::cmp::Reverse;
use std::collections::{BTreeMap, BinaryHeap};

// ponytail: caps are the recipe totals (wood 5, stone 11, iron_ore 3, iron 3); raise them if a recipe grows.
pub fn successors(grid: &Grid, s: &State) -> Vec<(Move, State, u64)> {
    moves(grid, s)
        .into_iter()
        .filter(|(_, n, _)| n.inv.wood <= 5 && n.inv.stone <= 11 && n.inv.iron_ore <= 3 && n.inv.iron <= 3)
        .collect()
}

pub fn plan(grid: &Grid, start: State, goal_pos: (u32, u32), done: impl Fn(&State) -> bool) -> Option<(u64, Vec<Move>)> {
    if !Reach::new(grid).can_walk(start.pos, goal_pos) {
        return None;
    }
    let mut best: BTreeMap<State, (u64, Option<(State, Move)>)> = BTreeMap::new();
    let mut heap = BinaryHeap::new();
    best.insert(start, (0, None));
    heap.push(Reverse((0, start)));
    while let Some(Reverse((d, s))) = heap.pop() {
        if best[&s].0 != d {
            continue;
        }
        if s.pos == goal_pos && done(&s) {
            let mut path = Vec::new();
            let mut cur = s;
            while let Some((prev, m)) = best[&cur].1 {
                path.push(m);
                cur = prev;
            }
            path.reverse();
            return Some((d, path));
        }
        for (m, n, w) in successors(grid, &s) {
            let nd = d + w;
            if best.get(&n).is_none_or(|(old, _)| nd < *old) {
                best.insert(n, (nd, Some((s, m))));
                heap.push(Reverse((nd, n)));
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dijkstra::shortest;
    use crate::metric::Tool;
    use crate::state::Inv;
    use sealrun_world::gen::generate;
    use sealrun_world::grid::Tile;

    type Done = fn(&State) -> bool;

    const MAP: [&str; 6] = ["..T..S", ".S.W..", "..I.T.", "W.S.I.", "..T...", "S.I..."];

    fn has_wood_pick(s: &State) -> bool {
        s.inv.pick >= Tool::Wood
    }

    fn has_stone_pick(s: &State) -> bool {
        s.inv.pick >= Tool::Stone
    }

    fn parse(rows: &[&str]) -> Grid {
        let mut g = Grid::new(rows[0].len() as u32, rows.len() as u32);
        for (y, row) in rows.iter().enumerate() {
            for (x, c) in row.bytes().enumerate() {
                let t = match c {
                    b'.' => Tile::Air,
                    b'S' => Tile::Stone,
                    b'T' => Tile::Tree,
                    b'I' => Tile::Iron,
                    b'W' => Tile::Water,
                    _ => panic!("bad tile {}", c as char),
                };
                g.set(x as u32, y as u32, t);
            }
        }
        g
    }

    fn reach_all(grid: &Grid, start: State) -> (Vec<State>, Vec<Option<u64>>) {
        let mut states = vec![start];
        let mut index = BTreeMap::from([(start, 0usize)]);
        let mut adj: Vec<Vec<(usize, u64)>> = Vec::new();
        while adj.len() < states.len() {
            let s = states[adj.len()];
            let mut edges = Vec::new();
            for (_, n, w) in successors(grid, &s) {
                let next = states.len();
                let j = *index.entry(n).or_insert(next);
                if j == next {
                    states.push(n);
                }
                edges.push((j, w));
            }
            adj.push(edges);
        }
        let dist = shortest(&adj, 0);
        (states, dist)
    }

    fn min_goal(states: &[State], dist: &[Option<u64>], goal: (u32, u32), done: Done) -> Option<u64> {
        states.iter().zip(dist).filter(|(s, _)| s.pos == goal && done(s)).filter_map(|(_, d)| *d).min()
    }

    fn check(grid: &Grid, start: State, goal: (u32, u32), done: Done) -> bool {
        let (states, dist) = reach_all(grid, start);
        let want = min_goal(&states, &dist, goal, done);
        let got = plan(grid, start, goal, done);
        assert_eq!(got.as_ref().map(|p| p.0), want, "start {start:?} goal {goal:?}");
        if let Some((cost, path)) = got {
            let mut cur = start;
            let mut sum = 0;
            for m in path {
                let (_, next, w) = successors(grid, &cur)
                    .into_iter()
                    .find(|(x, _, _)| *x == m)
                    .expect("planned move is a successor");
                sum += w;
                cur = next;
            }
            assert_eq!(sum, cost);
            assert!(cur.pos == goal && done(&cur));
        }
        want.is_some()
    }

    #[test]
    fn plan_cost_equals_dijkstra() {
        let mut cases = vec![(parse(&MAP), (0, 0), (5, 5))];
        for seed in 0..6 {
            let g = generate(seed, 8, 8);
            let open: Vec<(u32, u32)> = (0..8)
                .flat_map(|y| (0..8).map(move |x| (x, y)))
                .filter(|&(x, y)| g.get(x, y).is_open())
                .collect();
            if let (Some(&start), Some(&goal)) = (open.first(), open.last()) {
                cases.push((g, start, goal));
            }
        }

        let mut found = 0;
        for (grid, pos, goal) in &cases {
            let start = State { pos: *pos, inv: Inv::EMPTY };
            for done in [has_wood_pick as Done, has_stone_pick as Done] {
                found += check(grid, start, *goal, done) as usize;
            }
        }
        assert!(found > 0, "no goal reachable in any case");

        let walled = parse(&[".....", ".....", ".....", "...SS", "...S."]);
        assert!(!check(&walled, State { pos: (0, 0), inv: Inv::EMPTY }, (4, 4), has_wood_pick));
    }
}
