mod common;

use common::start_finish;
use sealrun_route::metric::{Tool, WALK_TICKS};
use sealrun_route::realmodel::{bfs_real, moves, plan_real, Step, NODE_CAP};
use sealrun_route::state::{Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};
use std::path::Path;
use std::time::Instant;

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

fn cap_hit(ticks: Option<u64>, nodes: usize) -> bool {
    ticks.is_none() && nodes >= NODE_CAP
}

fn cell(ticks: Option<u64>, nodes: usize) -> String {
    if cap_hit(ticks, nodes) {
        "cap hit".to_string()
    } else {
        opt(ticks)
    }
}

#[test]
fn swim_costs_ten_then_walk() {
    let mut g = Grid::new(3, 1);
    g.set(1, 0, Tile::Water);
    let start = State { pos: (0, 0), inv: Inv::EMPTY };
    let done = |s: &State| s.pos == (2, 0);

    let (ticks, route, _) = plan_real(&g, start, done);
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

    let (ticks, route, _) = plan_real(&g, start, done);
    assert_eq!(ticks, Some(23 + 5 + WALK_TICKS));
    assert_eq!(route, vec![Step::Tunnel((1, 0)), Step::Base(Move::Walk((2, 0)))]);
    assert_eq!(replay(&g, start, &route, done), 23 + 5 + WALK_TICKS);

    let (ticks, _, _) = bfs_real(&g, start, done, 1_000);
    assert_eq!(ticks, Some(23 + 5 + WALK_TICKS));
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

    const BUDGETS: [usize; 3] = [10_000, 100_000, 1_000_000];
    let done = |s: &State| s.inv.iron_ore >= 1;

    let mut json_rows = Vec::new();
    let mut plan_routed = 0usize;
    let mut plan_nodes = 0usize;
    let mut plan_ms = 0f64;
    let mut bfs_routed = [0usize; 3];
    let mut bfs_nodes = [0usize; 3];
    let mut bfs_ms = [0f64; 3];
    let mut plan_caps = 0usize;
    let mut bfs_caps = [0usize; 3];

    println!("start kind  x  y | plan ticks nodes ms | bfs1e4 ticks nodes ms | bfs1e5 ticks nodes ms | bfs1e6 ticks nodes ms");
    for &(pos, kind) in &starts {
        let start = State { pos, inv: Inv::EMPTY };
        let t = Instant::now();
        let (pt, proute, pn) = plan_real(&grid, start, done);
        let pms = t.elapsed().as_secs_f64() * 1000.0;
        if let Some(ticks) = pt {
            assert_eq!(replay(&grid, start, &proute, done), ticks, "plan route cost at {pos:?}");
        }
        let pcap = cap_hit(pt, pn);
        plan_caps += pcap as usize;
        plan_routed += pt.is_some() as usize;
        plan_nodes += pn;
        plan_ms += pms;

        let mut cells = Vec::new();
        let mut bfs_json = Vec::new();
        for (i, &budget) in BUDGETS.iter().enumerate() {
            let t = Instant::now();
            let (bt, broute, bn) = bfs_real(&grid, start, done, budget);
            let ms = t.elapsed().as_secs_f64() * 1000.0;
            if let Some(ticks) = bt {
                assert_eq!(replay(&grid, start, &broute, done), ticks, "bfs route cost at {pos:?}");
            }
            if let Some(q) = bt {
                if let Some(p) = pt {
                    assert!(p <= q, "plan ticks {p} > bfs ticks {q} at {pos:?} budget {budget}: bug");
                } else {
                    assert!(pcap, "bfs routed {pos:?} at budget {budget} but plan_real exhausted without a route");
                }
            }
            bfs_routed[i] += bt.is_some() as usize;
            bfs_caps[i] += cap_hit(bt, bn) as usize;
            bfs_nodes[i] += bn;
            bfs_ms[i] += ms;
            cells.push(format!("{:>7} {:>7} {:>8.1}", cell(bt, bn), bn, ms));
            bfs_json.push(format!(
                "{{\"budget\":{budget},\"ticks\":{},\"nodes\":{bn},\"cap_hit\":{},\"ms\":{ms:.3}}}",
                opt(bt),
                cap_hit(bt, bn)
            ));
        }
        println!(
            "{kind:<6} {:>3} {:>3} | {:>7} {:>7} {:>8.1} | {}",
            pos.0,
            pos.1,
            cell(pt, pn),
            pn,
            pms,
            cells.join(" | ")
        );
        json_rows.push(format!(
            "{{\"kind\":\"{kind}\",\"x\":{},\"y\":{},\"plan\":{{\"ticks\":{},\"nodes\":{pn},\"cap_hit\":{pcap},\"ms\":{pms:.3}}},\"bfs\":[{}]}}",
            pos.0,
            pos.1,
            opt(pt),
            bfs_json.join(",")
        ));
    }

    let bfs_summary: Vec<String> = BUDGETS
        .iter()
        .enumerate()
        .map(|(i, b)| {
            format!(
                "{{\"budget\":{b},\"routed\":{},\"cap_hits\":{},\"nodes\":{},\"ms\":{:.3}}}",
                bfs_routed[i], bfs_caps[i], bfs_nodes[i], bfs_ms[i]
            )
        })
        .collect();
    let json = format!(
        "{{\"grid\":\"crates/route/tests/fixtures/rs_seed7_spawn.grid\",\"goal\":\"iron_ore >= 1\",\"node_cap\":{NODE_CAP},\"starts\":{},\"plan\":{{\"routed\":{plan_routed},\"cap_hits\":{plan_caps},\"nodes\":{plan_nodes},\"ms\":{plan_ms:.3}}},\"bfs\":[{}],\"rows\":[{}]}}\n",
        starts.len(),
        bfs_summary.join(","),
        json_rows.join(",")
    );
    let out = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../lab/results/research");
    std::fs::create_dir_all(&out).expect("results dir");
    std::fs::write(out.join("race_realmodel.json"), json).expect("write race json");

    println!("node cap {NODE_CAP}");
    println!("starts {} | plan routed {plan_routed} cap hits {plan_caps} nodes {plan_nodes} ms {plan_ms:.1}", starts.len());
    for (i, b) in BUDGETS.iter().enumerate() {
        println!(
            "bfs {b}: routed {} cap hits {} nodes {} ms {:.1}",
            bfs_routed[i], bfs_caps[i], bfs_nodes[i], bfs_ms[i]
        );
    }
}
