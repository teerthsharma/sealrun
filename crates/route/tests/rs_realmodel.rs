mod common;

use common::start_finish;
use sealrun_route::metric::{Tool, WALK_TICKS};
use sealrun_route::realmodel::{bfs_real, moves, plan_real, Step, NODE_CAP};
use sealrun_route::state::{Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};
use std::path::Path;
use std::time::Instant;

const LEVELS: [usize; 3] = [10_000, 100_000, 1_000_000];

fn replay(grid: &Grid, start: State, route: &[Step], done: impl Fn(&State) -> bool) -> u64 {
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
    assert!(done(&cur), "route ends in a done state");
    total
}

fn opt(v: Option<u64>) -> String {
    v.map_or("null".to_string(), |x| x.to_string())
}

struct Run {
    budget: usize,
    expanded: usize,
    ticks: Option<u64>,
    cap_hit: bool,
    ms: f64,
}

impl Run {
    fn new(budget: usize, ticks: Option<u64>, expanded: usize, ms: f64) -> Self {
        Run { budget, expanded, ticks, cap_hit: ticks.is_none() && expanded >= budget, ms }
    }

    fn json(&self) -> String {
        format!(
            "{{\"budget\":{},\"expanded\":{},\"routed\":{},\"ticks\":{},\"cap_hit\":{},\"ms\":{:.3}}}",
            self.budget,
            self.expanded,
            self.ticks.is_some(),
            opt(self.ticks),
            self.cap_hit,
            self.ms
        )
    }

    fn cell(&self) -> String {
        if self.cap_hit {
            "cap hit".to_string()
        } else {
            opt(self.ticks)
        }
    }
}

#[derive(Default)]
struct Tally {
    routed: usize,
    cap_hits: usize,
    nodes: usize,
    ms: f64,
}

impl Tally {
    fn add(&mut self, r: &Run) {
        self.routed += r.ticks.is_some() as usize;
        self.cap_hits += r.cap_hit as usize;
        self.nodes += r.expanded;
        self.ms += r.ms;
    }

    fn json(&self) -> String {
        format!(
            "{{\"routed\":{},\"cap_hits\":{},\"nodes\":{},\"ms\":{:.3}}}",
            self.routed, self.cap_hits, self.nodes, self.ms
        )
    }
}

fn millis(t: Instant) -> f64 {
    t.elapsed().as_secs_f64() * 1000.0
}

#[test]
fn swim_costs_ten_then_walk() {
    let mut g = Grid::new(3, 1);
    g.set(1, 0, Tile::Water);
    let start = State { pos: (0, 0), inv: Inv::EMPTY };
    let done = |s: &State| s.pos == (2, 0);

    let (ticks, route, _) = plan_real(&g, start, done, NODE_CAP);
    assert_eq!(ticks, Some(10 + WALK_TICKS));
    assert_eq!(route, vec![Step::Swim((1, 0)), Step::Base(Move::Walk((2, 0)))]);
    assert_eq!(replay(&g, start, &route, done), 10 + WALK_TICKS);

    let (ticks, _, _) = bfs_real(&g, start, done, 1_000);
    assert_eq!(ticks, Some(10 + WALK_TICKS));
}

#[test]
fn tunnel_costs_dig_plus_five_then_walk() {
    let mut g = Grid::new(3, 1);
    g.set(1, 0, Tile::Stone);
    let start = State { pos: (0, 0), inv: Inv { pick: Tool::Wood, ..Inv::EMPTY } };
    let done = |s: &State| s.pos == (2, 0);

    let (ticks, route, _) = plan_real(&g, start, done, NODE_CAP);
    assert_eq!(ticks, Some(23 + 5 + WALK_TICKS));
    assert_eq!(route, vec![Step::Tunnel((1, 0)), Step::Base(Move::Walk((2, 0)))]);
    assert_eq!(replay(&g, start, &route, done), 23 + 5 + WALK_TICKS);

    let (ticks, _, _) = bfs_real(&g, start, done, 1_000);
    assert_eq!(ticks, Some(23 + 5 + WALK_TICKS));
}

#[test]
fn caps_bind_each_solver_at_its_own_budget() {
    let mut g = Grid::new(3, 1);
    g.set(1, 0, Tile::Water);
    let start = State { pos: (0, 0), inv: Inv::EMPTY };
    let done = |s: &State| s.pos == (2, 0);

    assert_eq!(plan_real(&g, start, done, 1), (None, vec![], 1));
    let (ticks, _, nodes) = plan_real(&g, start, done, 2);
    assert_eq!((ticks, nodes), (Some(10 + WALK_TICKS), 2));

    assert_eq!(bfs_real(&g, start, done, 1), (None, vec![], 1));
    let (ticks, _, nodes) = bfs_real(&g, start, done, 2);
    assert_eq!((ticks, nodes), (Some(10 + WALK_TICKS), 2));
}

#[test]
fn race_on_seed7_spawn_grid() {
    let grid = Grid::from_bytes(include_bytes!("fixtures/rs_seed7_spawn.grid")).expect("fixture decodes");
    let (centre, _) = start_finish(&grid).expect("fixture has a start and an iron");
    let air: Vec<(u32, u32)> = (0..grid.h())
        .flat_map(|y| (0..grid.w()).map(move |x| (x, y)))
        .filter(|&(x, y)| grid.get(x, y) == Tile::Air)
        .collect();
    let mut starts = vec![(centre, "centre")];
    starts.extend(air.iter().step_by(8).map(|&p| (p, "air8")));

    let done = |s: &State| s.inv.iron_ore >= 1;
    let mut plan_t: [Tally; 3] = Default::default();
    let mut bfs_t: [Tally; 3] = Default::default();
    let mut rows = Vec::new();

    println!("start kind  x  y | L=1e4 plan cell/nodes | bfs cell/nodes | L=1e5 plan | bfs | L=1e6 plan | bfs");
    for &(pos, kind) in &starts {
        let start = State { pos, inv: Inv::EMPTY };
        let mut levels = Vec::new();
        let mut line = String::new();
        for (i, &level) in LEVELS.iter().enumerate() {
            let t = Instant::now();
            let (pt, proute, pn) = plan_real(&grid, start, done, level);
            let pr = Run::new(level, pt, pn, millis(t));
            if let Some(ticks) = pt {
                assert_eq!(replay(&grid, start, &proute, done), ticks, "plan route cost at {pos:?}");
            }

            let t = Instant::now();
            let (bt, broute, bn) = bfs_real(&grid, start, done, level);
            let br = Run::new(level, bt, bn, millis(t));
            if let Some(ticks) = bt {
                assert_eq!(replay(&grid, start, &broute, done), ticks, "bfs route cost at {pos:?}");
                match pt {
                    Some(p) => assert!(p <= ticks, "plan ticks {p} > bfs ticks {ticks} at {pos:?} level {level}: bug"),
                    None => assert!(pr.cap_hit, "bfs routed {pos:?} at level {level} but plan_real exhausted"),
                }
            }

            plan_t[i].add(&pr);
            bfs_t[i].add(&br);
            line += &format!(" | {:>7} {:>7} | {:>7} {:>7}", pr.cell(), pn, br.cell(), bn);
            levels.push(format!("{{\"level\":{level},\"plan\":{},\"bfs\":{}}}", pr.json(), br.json()));
        }
        println!("{kind:<6} {:>3} {:>3}{line}", pos.0, pos.1);
        rows.push(format!("{{\"kind\":\"{kind}\",\"x\":{},\"y\":{},\"levels\":[{}]}}", pos.0, pos.1, levels.join(",")));
    }

    let summary: Vec<String> = LEVELS
        .iter()
        .enumerate()
        .map(|(i, l)| format!("{{\"level\":{l},\"plan\":{},\"bfs\":{}}}", plan_t[i].json(), bfs_t[i].json()))
        .collect();
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../lab/results/research");
    let legacy = std::fs::read_to_string(root.join("race_realmodel_legacy_cap2m.json")).expect("legacy run file");
    let json = format!(
        "{{\"grid\":\"crates/route/tests/fixtures/rs_seed7_spawn.grid\",\"goal\":\"iron_ore >= 1\",\"starts\":{},\"levels\":[{}],\"summary\":[{}],\"rows\":[{}],\"legacy_plan_cap_2000000\":{{\"label\":\"superseded: one plan_real cap of NODE_CAP=2,000,000 on every row against bfs budgets 1e4/1e5/1e6; cap_hit checked only NODE_CAP\",\"run\":{}}}}}\n",
        starts.len(),
        LEVELS.map(|l| l.to_string()).join(","),
        summary.join(","),
        rows.join(","),
        legacy.trim()
    );
    std::fs::create_dir_all(&root).expect("results dir");
    std::fs::write(root.join("race_realmodel.json"), json).expect("write race json");

    println!("starts {}", starts.len());
    for (i, l) in LEVELS.iter().enumerate() {
        println!(
            "level {l}: plan routed {} cap hits {} nodes {} ms {:.1} | bfs routed {} cap hits {} nodes {} ms {:.1}",
            plan_t[i].routed, plan_t[i].cap_hits, plan_t[i].nodes, plan_t[i].ms,
            bfs_t[i].routed, bfs_t[i].cap_hits, bfs_t[i].nodes, bfs_t[i].ms
        );
    }
}
