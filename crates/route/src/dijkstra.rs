use std::cmp::Reverse;
use std::collections::BinaryHeap;

pub fn shortest(adj: &[Vec<(usize, u64)>], src: usize) -> Vec<Option<u64>> {
    let mut dist = vec![None; adj.len()];
    let mut heap = BinaryHeap::new();
    dist[src] = Some(0);
    heap.push(Reverse((0u64, src)));
    while let Some(Reverse((d, u))) = heap.pop() {
        if dist[u] != Some(d) {
            continue;
        }
        for &(v, w) in &adj[u] {
            // Distances above u64::MAX are not representable and are skipped.
            let Some(nd) = d.checked_add(w) else { continue };
            if dist[v].is_none_or(|old| nd < old) {
                dist[v] = Some(nd);
                heap.push(Reverse((nd, v)));
            }
        }
    }
    dist
}

#[cfg(test)]
mod tests {
    use super::shortest;

    struct Lcg(u64);

    impl Lcg {
        fn next(&mut self) -> u64 {
            self.0 = self
                .0
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            self.0 >> 33
        }

        fn below(&mut self, m: u64) -> u64 {
            self.next() % m
        }
    }

    fn bellman_ford(adj: &[Vec<(usize, u64)>], src: usize) -> Vec<Option<u64>> {
        let n = adj.len();
        let mut dist: Vec<Option<u64>> = vec![None; n];
        dist[src] = Some(0);
        for _ in 1..n.max(1) {
            let mut changed = false;
            for u in 0..n {
                let Some(du) = dist[u] else { continue };
                for &(v, w) in &adj[u] {
                    let Some(nd) = du.checked_add(w) else { continue };
                    if dist[v].is_none_or(|old| nd < old) {
                        dist[v] = Some(nd);
                        changed = true;
                    }
                }
            }
            if !changed {
                break;
            }
        }
        dist
    }

    #[test]
    fn dijkstra_matches_bellman_ford() {
        let mut rng = Lcg(12345);
        let (mut unreachable, mut zero_edges) = (0usize, 0usize);
        for case in 0..200 {
            let n = 1 + rng.below(30) as usize;
            let density = rng.below(100);
            let mut adj = vec![Vec::new(); n];
            for u in 0..n {
                for v in 0..n {
                    if rng.below(100) < density {
                        let w = rng.below(101);
                        zero_edges += (w == 0) as usize;
                        adj[u].push((v, w));
                    }
                }
            }
            for src in 0..n {
                let expected = bellman_ford(&adj, src);
                unreachable += expected.iter().filter(|d| d.is_none()).count();
                assert_eq!(shortest(&adj, src), expected, "case {case} src {src}");
            }
        }
        assert!(unreachable > 0 && zero_edges > 0);
    }
}
