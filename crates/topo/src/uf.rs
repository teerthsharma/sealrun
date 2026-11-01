pub struct UnionFind {
    parent: Vec<usize>,
    rank: Vec<u8>,
    sets: usize,
}

impl UnionFind {
    pub fn new(n: usize) -> Self {
        Self {
            parent: (0..n).collect(),
            rank: vec![0; n],
            sets: n,
        }
    }

    pub fn find(&mut self, mut x: usize) -> usize {
        while self.parent[x] != x {
            self.parent[x] = self.parent[self.parent[x]];
            x = self.parent[x];
        }
        x
    }

    pub fn union(&mut self, a: usize, b: usize) -> bool {
        let (mut ra, mut rb) = (self.find(a), self.find(b));
        if ra == rb {
            return false;
        }
        if self.rank[ra] < self.rank[rb] {
            std::mem::swap(&mut ra, &mut rb);
        }
        self.parent[rb] = ra;
        if self.rank[ra] == self.rank[rb] {
            self.rank[ra] += 1;
        }
        self.sets -= 1;
        true
    }

    pub fn sets(&self) -> usize {
        self.sets
    }
}

#[cfg(test)]
mod tests {
    use super::UnionFind;

    fn naive_components(n: usize, joins: &[(usize, usize)]) -> usize {
        let mut label: Vec<usize> = (0..n).collect();
        let mut changed = true;
        while changed {
            changed = false;
            for &(a, b) in joins {
                let m = label[a].min(label[b]);
                if label[a] != m || label[b] != m {
                    label[a] = m;
                    label[b] = m;
                    changed = true;
                }
            }
        }
        label.sort_unstable();
        label.dedup();
        label.len()
    }

    #[test]
    fn union_find_counts_sets() {
        let mut uf = UnionFind::new(10);
        assert!(uf.union(0, 1));
        assert!(uf.union(1, 2));
        assert!(uf.union(3, 4));
        assert!(!uf.union(2, 0));
        assert!(!uf.union(9, 9));
        assert_eq!(uf.sets(), 7);

        let mut state: u64 = 0x9E37_79B9_7F4A_7C15;
        let mut next = move |m: usize| {
            state = state
                .wrapping_mul(6_364_136_223_846_793_005)
                .wrapping_add(1_442_695_040_888_963_407);
            ((state >> 33) as usize) % m
        };
        for round in 0..50usize {
            let n = 200;
            let joins: Vec<(usize, usize)> = (0..round * 4).map(|_| (next(n), next(n))).collect();
            let mut uf = UnionFind::new(n);
            for &(a, b) in &joins {
                uf.union(a, b);
            }
            assert_eq!(uf.sets(), naive_components(n, &joins), "round {round}");
        }
    }
}
