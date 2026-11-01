use crate::metric::dig;
use crate::state::{self, Move, State};
use sealrun_world::grid::{Grid, Tile};
use std::collections::{BTreeMap, BTreeSet, BinaryHeap, VecDeque};
use std::cmp::Reverse;

pub const SWIM: u64 = 10;
pub const NODE_CAP: usize = 2_000_000;
const TUNNEL_EXTRA: u64 = 5;
const DIRS: [(i64, i64); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Step {
    Base(Move),
    Swim((u32, u32)),
    Tunnel((u32, u32)),
}

// ponytail: same recipe-total caps as plan::successors, so the state space is finite for Dijkstra.
fn within_caps(s: &State) -> bool {
    s.inv.wood <= 5 && s.inv.stone <= 11 && s.inv.iron_ore <= 3 && s.inv.iron <= 3
}

pub fn moves(grid: &Grid, s: &State) -> Vec<(Step, State, u64)> {
    let mut out: Vec<(Step, State, u64)> = state::moves(grid, s)
        .into_iter()
        .map(|(m, n, w)| (Step::Base(m), n, w))
        .filter(|(_, n, _)| within_caps(n))
        .collect();
    let (x, y) = (s.pos.0 as i64, s.pos.1 as i64);
    for (dx, dy) in DIRS {
        let (nx, ny) = (x + dx, y + dy);
        if !grid.in_bounds(nx, ny) {
            continue;
        }
        let p = (nx as u32, ny as u32);
        match grid.get(p.0, p.1) {
            Tile::Water => out.push((Step::Swim(p), State { pos: p, inv: s.inv }, SWIM)),
            Tile::Stone => {
                let Some(d) = dig(Tile::Stone, s.inv.pick) else { continue };
                out.push((Step::Tunnel(p), State { pos: p, inv: s.inv }, d.ticks + TUNNEL_EXTRA));
            }
            _ => {}
        }
    }
    out
}

type Parents = BTreeMap<State, (u64, Option<(State, Step)>)>;

pub fn plan_real(grid: &Grid, start: State, done: impl Fn(&State) -> bool, cap: usize) -> (Option<u64>, Vec<Step>, usize) {
    let mut best: Parents = BTreeMap::new();
    let mut heap = BinaryHeap::new();
    best.insert(start, (0, None));
    heap.push(Reverse((0u64, start)));
    let mut expanded = 0;
    while let Some(Reverse((d, s))) = heap.pop() {
        if best[&s].0 != d {
            continue;
        }
        if done(&s) {
            let mut path = Vec::new();
            let mut cur = s;
            while let Some((prev, m)) = best[&cur].1 {
                path.push(m);
                cur = prev;
            }
            path.reverse();
            return (Some(d), path, expanded);
        }
        if expanded == cap {
            return (None, Vec::new(), expanded);
        }
        expanded += 1;
        for (m, n, w) in moves(grid, &s) {
            let nd = d + w;
            if best.get(&n).is_none_or(|(old, _)| nd < *old) {
                best.insert(n, (nd, Some((s, m))));
                heap.push(Reverse((nd, n)));
            }
        }
    }
    (None, Vec::new(), expanded)
}

pub fn bfs_real(grid: &Grid, start: State, done: impl Fn(&State) -> bool, max_nodes: usize) -> (Option<u64>, Vec<Step>, usize) {
    let max_nodes = max_nodes.min(NODE_CAP);
    let mut seen = BTreeSet::from([start]);
    let mut parent: BTreeMap<State, (State, Step, u64)> = BTreeMap::new();
    let mut frontier = VecDeque::from([start]);
    let mut expanded = 0;
    while let Some(cur) = frontier.pop_front() {
        if done(&cur) {
            let (mut ticks, mut route) = (0, Vec::new());
            let mut at = cur;
            while at != start {
                let (prev, m, cost) = parent[&at];
                ticks += cost;
                route.push(m);
                at = prev;
            }
            route.reverse();
            return (Some(ticks), route, expanded);
        }
        if expanded == max_nodes {
            return (None, Vec::new(), expanded);
        }
        expanded += 1;
        for (m, next, cost) in moves(grid, &cur) {
            if seen.insert(next) {
                parent.insert(next, (cur, m, cost));
                frontier.push_back(next);
            }
        }
    }
    (None, Vec::new(), expanded)
}
