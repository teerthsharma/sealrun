use crate::state::{moves, Move, State};
use sealrun_world::grid::Grid;
use std::collections::{BTreeMap, BTreeSet, VecDeque};

// ponytail: budget counts expanded states, not wall-clock, so the result is identical run to run; a timer would not be.
pub fn bfs(grid: &Grid, start: State, goal_pos: (u32, u32), done: impl Fn(&State) -> bool, max_nodes: usize) -> Option<(u64, Vec<Move>)> {
    let mut seen = BTreeSet::from([start]);
    let mut parent: BTreeMap<State, (State, Move, u64)> = BTreeMap::new();
    let mut frontier = VecDeque::from([start]);
    let mut expanded = 0;
    while let Some(cur) = frontier.pop_front() {
        if cur.pos == goal_pos && done(&cur) {
            let (mut ticks, mut route) = (0, Vec::new());
            let mut at = cur;
            while at != start {
                let (prev, m, cost) = parent[&at];
                ticks += cost;
                route.push(m);
                at = prev;
            }
            route.reverse();
            return Some((ticks, route));
        }
        if expanded == max_nodes {
            return None;
        }
        expanded += 1;
        for (m, next, cost) in moves(grid, &cur) {
            if seen.insert(next) {
                parent.insert(next, (cur, m, cost));
                frontier.push_back(next);
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::metric::Tool;
    use crate::state::Inv;
    use sealrun_world::grid::Tile;

    fn has_wood_pick(s: &State) -> bool {
        s.inv.pick >= Tool::Wood
    }

    fn map() -> Grid {
        let mut g = Grid::new(6, 6);
        for (x, y) in [(2, 0), (2, 1), (2, 2)] {
            g.set(x, y, Tile::Tree);
        }
        for (x, y) in [(4, 4), (4, 5), (5, 4)] {
            g.set(x, y, Tile::Stone);
        }
        g
    }

    #[test]
    fn baseline_bfs_finds_valid_route() {
        let grid = map();
        let start = State { pos: (0, 0), inv: Inv::EMPTY };
        let goal = (5, 0);
        let found = bfs(&grid, start, goal, has_wood_pick, 1_000_000);

        let (ticks, route) = found.clone().expect("route found");
        let mut cur = start;
        let mut total = 0;
        for m in &route {
            let (_, next, cost) = moves(&grid, &cur)
                .into_iter()
                .find(|(mm, _, _)| mm == m)
                .expect("move is legal here");
            total += cost;
            cur = next;
        }
        assert_eq!(cur.pos, goal);
        assert!(has_wood_pick(&cur));
        assert_eq!(total, ticks);

        assert_eq!(bfs(&grid, start, goal, has_wood_pick, 1), None);
        assert_eq!(bfs(&grid, start, goal, has_wood_pick, 1_000_000), found);
    }
}
