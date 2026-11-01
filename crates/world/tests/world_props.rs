use sealrun_world::gen::world;
use sealrun_world::grid::Tile;

#[test]
fn every_seed_has_start_wood_iron_goal() {
    for (w, h) in [(64u32, 64u32), (8, 8)] {
        for seed in 0..100u64 {
            let wd = world(seed, w, h);
            let (sx, sy) = wd.start;
            let (gx, gy) = wd.goal;
            assert!(sx < w && sy < h, "seed {seed} {w}x{h}: start {:?} out of bounds", wd.start);
            assert!(gx < w && gy < h, "seed {seed} {w}x{h}: goal {:?} out of bounds", wd.goal);
            assert!(wd.grid.get(sx, sy).is_open(), "seed {seed} {w}x{h}: start is not open");
            assert_ne!(wd.start, wd.goal, "seed {seed} {w}x{h}: start equals goal");

            let mut goals = Vec::new();
            let (mut trees, mut irons) = (0, 0);
            for y in 0..h {
                for x in 0..w {
                    match wd.grid.get(x, y) {
                        Tile::Goal => goals.push((x, y)),
                        Tile::Tree => trees += 1,
                        Tile::Iron => irons += 1,
                        _ => {}
                    }
                }
            }
            assert_eq!(goals, vec![wd.goal], "seed {seed} {w}x{h}: Goal tiles do not match goal");
            assert!(trees >= 1, "seed {seed} {w}x{h}: no Tree");
            assert!(irons >= 1, "seed {seed} {w}x{h}: no Iron");

            assert_eq!(world(seed, w, h), wd, "seed {seed} {w}x{h}: world is not deterministic");
        }
    }
}
