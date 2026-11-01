use sealrun_route::plan::plan;
use sealrun_route::state::{Inv, State};
use sealrun_world::grid::{Grid, Tile};
use std::path::Path;

#[test]
fn round1_routes_from_air_tiles() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let grid_path = root.join("lab/results/research/seed7_spawn.grid");
    let grid = Grid::from_bytes(&std::fs::read(&grid_path).expect("grid file")).expect("grid decodes");
    let cells: Vec<(u32, u32)> = (0..grid.h()).flat_map(|y| (0..grid.w()).map(move |x| (x, y))).collect();
    let airs: Vec<(u32, u32)> = cells.iter().copied().filter(|&(x, y)| grid.get(x, y) == Tile::Air).collect();

    let mut goals: Vec<(u32, u32)> = Vec::new();
    for &(x, y) in cells.iter().filter(|&&(x, y)| grid.get(x, y) == Tile::Iron) {
        let (x, y) = (x as i64, y as i64);
        for (nx, ny) in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)] {
            if grid.in_bounds(nx, ny) && grid.get(nx as u32, ny as u32).is_open() {
                goals.push((nx as u32, ny as u32));
            }
        }
    }
    goals.sort();
    goals.dedup();

    let done = |s: &State| s.inv.iron_ore >= 1;
    let mut routed = 0;
    for (i, &pos) in airs.iter().enumerate() {
        let start = State { pos, inv: Inv::EMPTY };
        if goals.iter().any(|&g| plan(&grid, start, g, done).is_some()) {
            routed += 1;
        }
        if i % 100 == 0 {
            println!("start {i}/{} routed so far {routed}", airs.len());
        }
    }

    let commit = std::process::Command::new("git")
        .args(["rev-parse", "HEAD"])
        .current_dir(&root)
        .output()
        .expect("git rev-parse")
        .stdout;
    let commit = String::from_utf8(commit).expect("utf8").trim().to_string();
    let json = format!(
        "{{\"model\":\"round1: crates/route/src/plan.rs plan() over state.rs moves (walk, mine with pickaxe, craft, smelt; no swim, no tunnel); done = iron_ore >= 1; goal = open tile next to iron\",\"grid\":\"lab/results/research/seed7_spawn.grid\",\"starts\":{},\"routed\":{routed},\"source_commit\":\"{commit}\"}}\n",
        airs.len()
    );
    std::fs::write(root.join("lab/results/research/round1_reach.json"), json).expect("write round1 json");
    println!("starts {} routed {routed}", airs.len());
}
