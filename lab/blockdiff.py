def diff(a: dict, b: dict) -> dict:
    changed = [(p, a[p], b[p]) for p in a if p in b and a[p] != b[p]]
    added = [(p, b[p]) for p in b if p not in a]
    missing = [(p, a[p]) for p in a if p not in b]
    return {"changed": sorted(changed), "added": sorted(added), "missing": sorted(missing)}
