use sealrun_cli::{air_starts_by_distance, centre_start, race, tally};
use sealrun_world::grid::Grid;

const FIXTURE: &[u8] = include_bytes!("../../route/tests/fixtures/rs_seed7_spawn.grid");

fn seed7() -> Grid {
    Grid::from_bytes(FIXTURE).expect("fixture decodes")
}

#[test]
fn centre_race_reproduces_saved_ticks() {
    let g = seed7();
    let start = centre_start(&g).expect("fixture has a start");
    let r = race(&g, start, 100_000);
    assert_eq!(r.plan_ticks, Some(538));
    assert_eq!(r.bfs_ticks, Some(912));
}

#[test]
fn twenty_starts_at_100k_have_zero_losses() {
    let g = seed7();
    let starts: Vec<_> = air_starts_by_distance(&g).into_iter().take(20).collect();
    let t = tally(&g, &starts, 100_000);
    assert_eq!(t.starts, 20);
    assert_eq!(t.losses, 0, "planner must never be slower or miss a start bfs routes");
    assert_eq!(t.wins + t.ties + t.planner_only + t.neither + t.bfs_only, 20);
}

#[test]
fn starts_are_air_and_nearest_centre_first() {
    let g = seed7();
    let starts = air_starts_by_distance(&g);
    assert_eq!(starts.len(), 1417, "fixture has 1417 air cells");
    assert_eq!(starts[0], centre_start(&g).unwrap());
}
