use sealrun_route::realmodel::{bfs_real, moves, plan_real, Step};
use sealrun_route::setup::start_finish;
use sealrun_route::state::{Inv, State};
use sealrun_world::grid::{Grid, Tile};

/// The goal: hold one iron ore. Same rule as the saved seed-7 race.
fn goal(s: &State) -> bool {
    s.inv.iron_ore >= 1
}

pub fn centre_start(grid: &Grid) -> Option<(u32, u32)> {
    start_finish(grid).map(|(s, _)| s)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Race {
    pub start: (u32, u32),
    pub plan_ticks: Option<u64>,
    pub bfs_ticks: Option<u64>,
}

fn replay(grid: &Grid, start: State, route: &[Step]) -> u64 {
    let mut cur = start;
    let mut total = 0;
    for step in route {
        let (_, next, cost) = moves(grid, &cur)
            .into_iter()
            .find(|(m, _, _)| m == step)
            .expect("route step is legal here");
        total += cost;
        cur = next;
    }
    assert!(goal(&cur), "route ends in the goal state");
    total
}

/// Runs both planners from `start` with the same node budget.
/// Panics if a route does not replay to its claimed ticks, or if the planner is slower than bfs.
pub fn race(grid: &Grid, start: (u32, u32), budget: usize) -> Race {
    let s = State { pos: start, inv: Inv::EMPTY };
    let (pt, proute, _) = plan_real(grid, s, goal, budget);
    let (bt, broute, _) = bfs_real(grid, s, goal, budget);
    if let Some(t) = pt {
        assert_eq!(replay(grid, s, &proute), t, "planner route cost at {start:?}");
    }
    if let Some(t) = bt {
        assert_eq!(replay(grid, s, &broute), t, "bfs route cost at {start:?}");
        if let Some(p) = pt {
            assert!(p <= t, "planner {p} > bfs {t} at {start:?}: bug");
        }
    }
    Race { start, plan_ticks: pt, bfs_ticks: bt }
}

/// Every air cell, nearest the grid centre first (ties: smaller y, then x). Deterministic.
pub fn air_starts_by_distance(grid: &Grid) -> Vec<(u32, u32)> {
    let (cx, cy) = ((grid.w() / 2) as i64, (grid.h() / 2) as i64);
    let mut v: Vec<(u32, u32)> = (0..grid.h())
        .flat_map(|y| (0..grid.w()).map(move |x| (x, y)))
        .filter(|&(x, y)| grid.get(x, y) == Tile::Air)
        .collect();
    v.sort_by_key(|&(x, y)| ((x as i64 - cx).abs() + (y as i64 - cy).abs(), y, x));
    v
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Tally {
    pub starts: usize,
    pub wins: usize,
    pub ties: usize,
    pub losses: usize,
    pub planner_only: usize,
    pub bfs_only: usize,
    pub neither: usize,
}

/// Counts, over `starts`, where the planner wins, ties or loses against bfs at equal budget.
/// A loss is the planner slower than bfs, or routing nothing where bfs routes.
pub fn tally(grid: &Grid, starts: &[(u32, u32)], budget: usize) -> Tally {
    let mut t = Tally { starts: starts.len(), ..Tally::default() };
    for &st in starts {
        let r = race(grid, st, budget);
        match (r.plan_ticks, r.bfs_ticks) {
            (Some(p), Some(b)) if p < b => t.wins += 1,
            (Some(p), Some(b)) if p == b => t.ties += 1,
            (Some(_), Some(_)) => t.losses += 1,
            (Some(_), None) => t.planner_only += 1,
            (None, Some(_)) => {
                t.bfs_only += 1;
                t.losses += 1;
            }
            (None, None) => t.neither += 1,
        }
    }
    t
}

fn json_opt(v: Option<u64>) -> String {
    v.map_or("null".to_string(), |x| x.to_string())
}

fn tally_json(t: &Tally) -> String {
    format!(
        "{{\"starts\":{},\"wins\":{},\"ties\":{},\"losses\":{},\"planner_only\":{},\"bfs_only\":{},\"neither\":{}}}",
        t.starts, t.wins, t.ties, t.losses, t.planner_only, t.bfs_only, t.neither
    )
}

/// `sealrun race <grid-file> [--budget N] [--starts K]`
/// Prints one JSON object: the centre race, and (if K > 0) a tally over the K nearest air starts.
pub fn run(args: &[String]) -> Result<String, String> {
    let usage = "usage: sealrun race <grid-file> [--budget N] [--starts K]";
    let (cmd, rest) = args.split_first().ok_or(usage)?;
    if cmd != "race" {
        return Err(format!("unknown command {cmd:?}; {usage}"));
    }
    let (path, mut opts) = rest.split_first().ok_or(usage)?;
    let (mut budget, mut k) = (100_000usize, 0usize);
    while let Some((flag, tail)) = opts.split_first() {
        let (val, after) = tail.split_first().ok_or(format!("{flag} needs a value"))?;
        let n: usize = val.parse().map_err(|_| format!("{flag} needs a whole number, got {val:?}"))?;
        match flag.as_str() {
            "--budget" => budget = n,
            "--starts" => k = n,
            other => return Err(format!("unknown option {other:?}; {usage}")),
        }
        opts = after;
    }
    let bytes = std::fs::read(path).map_err(|e| format!("{path}: {e}"))?;
    let grid = Grid::from_bytes(&bytes).map_err(|e| format!("{path}: {e:?}"))?;
    let start = centre_start(&grid).ok_or("grid has no air start or no iron")?;
    let r = race(&grid, start, budget);
    let t = if k > 0 {
        let starts: Vec<_> = air_starts_by_distance(&grid).into_iter().take(k).collect();
        tally_json(&tally(&grid, &starts, budget))
    } else {
        "null".to_string()
    };
    Ok(format!(
        "{{\"grid\":{path:?},\"budget\":{budget},\"centre\":{{\"start\":[{},{}],\"plan_ticks\":{},\"bfs_ticks\":{}}},\"tally\":{t}}}",
        r.start.0,
        r.start.1,
        json_opt(r.plan_ticks),
        json_opt(r.bfs_ticks)
    ))
}
