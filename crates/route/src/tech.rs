use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Item {
    Wood,
    Table,
    WoodPickaxe,
    Stone,
    StonePickaxe,
    Iron,
    Furnace,
    IronPickaxe,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum TechError {
    Cycle,
}

pub fn tree() -> Vec<(Item, Vec<Item>)> {
    use Item::*;
    vec![
        (Wood, vec![]),
        (Table, vec![Wood]),
        (WoodPickaxe, vec![Wood, Table]),
        (Stone, vec![WoodPickaxe]),
        (StonePickaxe, vec![Wood, Stone, Table]),
        (Iron, vec![StonePickaxe]),
        (Furnace, vec![Stone, Table]),
        (IronPickaxe, vec![Wood, Iron, Furnace, Table]),
    ]
}

pub fn order(rules: &[(Item, Vec<Item>)]) -> Result<Vec<Item>, TechError> {
    let mut pending: BTreeMap<Item, BTreeSet<Item>> = BTreeMap::new();
    for (item, needs) in rules {
        pending.entry(*item).or_default().extend(needs);
        for need in needs {
            pending.entry(*need).or_default();
        }
    }
    let total = pending.len();
    let mut ready: BTreeSet<Item> = pending
        .iter()
        .filter(|(_, needs)| needs.is_empty())
        .map(|(item, _)| *item)
        .collect();
    let mut out = Vec::with_capacity(total);
    while let Some(next) = ready.pop_first() {
        out.push(next);
        pending.remove(&next);
        for (item, needs) in pending.iter_mut() {
            if needs.remove(&next) && needs.is_empty() {
                ready.insert(*item);
            }
        }
    }
    if out.len() == total {
        Ok(out)
    } else {
        Err(TechError::Cycle)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tech_order_respects_needs() {
        let rules = tree();
        let sorted = order(&rules).expect("the tree has no loop");
        assert_eq!(sorted, order(&rules).unwrap());

        let mut unique = sorted.clone();
        unique.sort();
        unique.dedup();
        assert_eq!(unique.len(), rules.len());

        for (item, needs) in &rules {
            let at = sorted.iter().position(|x| x == item).unwrap();
            for need in needs {
                let before = sorted.iter().position(|x| x == need).unwrap();
                assert!(before < at, "{need:?} must come before {item:?}");
            }
        }

        let loop_rules = vec![
            (Item::Stone, vec![Item::StonePickaxe]),
            (Item::StonePickaxe, vec![Item::Stone]),
        ];
        assert_eq!(order(&loop_rules), Err(TechError::Cycle));
    }
}
