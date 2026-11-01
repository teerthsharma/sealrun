pub fn hash(seed: u64, x: i64, y: i64) -> u64 {
    let h = splitmix(splitmix(seed) ^ (x as u64));
    splitmix(h ^ (y as u64))
}

fn splitmix(mut z: u64) -> u64 {
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    z ^ (z >> 31)
}

#[cfg(test)]
mod tests {
    use super::hash;

    #[test]
    fn rng_same_input_same_output() {
        assert_eq!(hash(1, 2, 3), hash(1, 2, 3));
        let mut all = Vec::with_capacity(30_000);
        for seed in 1..=3u64 {
            for x in 0..100i64 {
                for y in 0..100i64 {
                    all.push(hash(seed, x, y));
                }
            }
        }
        all.sort_unstable();
        all.dedup();
        assert_eq!(all.len(), 30_000);
        assert_ne!(hash(1, 5, 5), hash(2, 5, 5));
    }
}
