use sealrun_route::baseline::bfs;
use sealrun_route::plan::plan;
use sealrun_route::state::{moves, Inv, Move, State};
use sealrun_world::grid::{Grid, Tile};

#[test]
fn guard_crop_edge_wall() {
    let air = Grid::new(3, 3);
    for y in 0..3 {
        for x in 0..3 {
            let s = State { pos: (x, y), inv: Inv::EMPTY };
            for (m, _, _) in moves(&air, &s) {
                if let Move::Walk(p) | Move::Mine(p) = m {
                    assert!(p.0 < 3 && p.1 < 3, "{m:?} from {:?} leaves the grid", s.pos);
                }
            }
        }
    }

    let origin = State { pos: (0, 0), inv: Inv::EMPTY };
    let mut walks: Vec<(u32, u32)> = moves(&air, &origin)
        .into_iter()
        .filter_map(|(m, _, _)| match m {
            Move::Walk(p) => Some(p),
            _ => None,
        })
        .collect();
    walks.sort();
    assert_eq!(walks, vec![(0, 1), (1, 0)]);

    let one = Grid::new(1, 1);
    let wood = |s: &State| s.inv.wood >= 1;
    assert_eq!(plan(&one, origin, (0, 0), wood), None);
    assert_eq!(bfs(&one, origin, (0, 0), wood, 10_000), None);

    let mut two = Grid::new(2, 1);
    two.set(1, 0, Tile::Tree);
    assert_eq!(plan(&two, origin, (0, 0), wood), Some((60, vec![Move::Mine((1, 0))])));
}
