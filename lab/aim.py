def best_order(rows):
    numbered = [row for row in rows if row["diamonds"] is not None]
    if not numbered:
        return {"lever": None, "reason": "not run"}
    counts = [row["diamonds"] for row in numbered]
    top = max(counts)
    if min(counts) == top:
        return {"lever": False, "diamonds": top, "reason": "all orders equal"}
    first = next(row for row in numbered if row["diamonds"] == top)
    return {"lever": True, "order": first["order"], "diamonds": top, "mean": sum(counts) / len(counts)}
