use crate::rng::hash;

fn lattice(seed: u64, gx: i64, gy: i64) -> i128 {
    i128::from((hash(seed, gx, gy) >> 48) as u32)
}

pub fn value_noise(seed: u64, x: i64, y: i64, scale: u32) -> u32 {
    assert!(scale > 0, "value_noise: scale must be non-zero");
    let step = i64::from(scale);
    let (gx, gy) = (x.div_euclid(step), y.div_euclid(step));
    let fx = i128::from(x.rem_euclid(step));
    let fy = i128::from(y.rem_euclid(step));
    let s = i128::from(step);
    let a = lattice(seed, gx, gy);
    let b = lattice(seed, gx.wrapping_add(1), gy);
    let c = lattice(seed, gx, gy.wrapping_add(1));
    let d = lattice(seed, gx.wrapping_add(1), gy.wrapping_add(1));
    let top = a * (s - fx) + b * fx;
    let bottom = c * (s - fx) + d * fx;
    ((top * (s - fy) + bottom * fy) / (s * s)) as u32
}

#[cfg(test)]
mod tests {
    use super::value_noise;
    use crate::rng::hash;

    #[test]
    fn noise_is_smooth_and_bounded() {
        let seed = 7;
        let scale = 16;
        let max_step = 65535 / 16 + 1;
        let mut seen = Vec::new();
        for x in -100..100i64 {
            for y in -100..100i64 {
                let v = value_noise(seed, x, y, scale);
                assert!(v <= 65535);
                assert_eq!(v, value_noise(seed, x, y, scale));
                assert!(v.abs_diff(value_noise(seed, x + 1, y, scale)) <= max_step);
                assert!(v.abs_diff(value_noise(seed, x, y + 1, scale)) <= max_step);
                seen.push(v);
            }
        }
        seen.sort_unstable();
        seen.dedup();
        assert!(seen.len() >= 100);
        for gx in -6..=6i64 {
            for gy in -6..=6i64 {
                let expected = (hash(seed, gx, gy) >> 48) as u32;
                assert_eq!(value_noise(seed, gx * 16, gy * 16, scale), expected);
            }
        }
    }
}
