use sealrun_world::gen::world;

const SEED_7_DIGEST: u64 = 0x7a2f_4571_d348_d00d;

fn fnv1a(bytes: &[u8]) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for &b in bytes {
        h ^= u64::from(b);
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    h
}

#[test]
fn seed_7_world_digest_is_pinned() {
    let w = world(7, 64, 64);
    let mut bytes = w.grid.to_bytes();
    for v in [w.start.0, w.start.1, w.goal.0, w.goal.1] {
        bytes.extend_from_slice(&v.to_le_bytes());
    }
    let digest = fnv1a(&bytes);
    assert_eq!(
        digest, SEED_7_DIGEST,
        "seed 7 world digest is {digest:#018x}, pinned value is {SEED_7_DIGEST:#018x}"
    );
}
