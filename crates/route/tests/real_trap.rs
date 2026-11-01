use sealrun_route::baseline::bfs;
use sealrun_route::metric::Tool;
use sealrun_route::plan::plan;
use sealrun_route::state::{moves, Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};

fn trap() -> Grid {
    let mut g = Grid::new(3, 1);
    g.set(0, 0, Tile::Tree);
    g.set(2, 0, Tile::Stone);
    g
}

fn done(s: &State) -> bool {
    s.inv.furnace && s.inv.pick >= Tool::Stone
}

fn replay(grid: &Grid, start: State, route: &[Move]) -> (u64, State) {
    let mut cur = start;
    let mut ticks = 0;
    for m in route {
        let (_, next, cost) = moves(grid, &cur)
            .into_iter()
            .find(|(mm, _, _)| mm == m)
            .expect("move is legal here");
        ticks += cost;
        cur = next;
    }
    (ticks, cur)
}

#[test]
fn planner_beats_move_counter_on_wall_trap() {
    let grid = trap();
    let start = State { pos: (1, 0), inv: Inv::EMPTY };
    let goal = (1, 0);

    let (bfs_ticks, bfs_route) = bfs(&grid, start, goal, done, 1_000_000).expect("bfs route");
    assert_eq!(bfs_ticks, 573, "bfs route {bfs_route:?}");
    assert_eq!(bfs_route.len(), 19, "bfs route {bfs_route:?}");
    let (replayed, end) = replay(&grid, start, &bfs_route);
    assert_eq!(replayed, bfs_ticks);
    assert!(done(&end));

    let (plan_ticks, plan_route) = plan(&grid, start, goal, done).expect("plan route");
    assert_eq!(plan_ticks, 485, "plan route {plan_route:?}");
    assert_eq!(plan_route.len(), 19, "plan route {plan_route:?}");
    let (replayed, end) = replay(&grid, start, &plan_route);
    assert_eq!(replayed, plan_ticks);
    assert!(done(&end));

    assert!(plan_ticks < bfs_ticks);
}
