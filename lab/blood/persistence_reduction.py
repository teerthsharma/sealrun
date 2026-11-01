# SOURCE: https://en.wikipedia.org/wiki/Persistent_homology "bringing of the filtered complex to its canonical form by upper-triangular matrices"
"""Z/2 column reduction of a filtered boundary matrix.

Pairing rule from Edelsbrunner, Letscher and Zomorodian, Discrete Comput. Geom. 28 (2002) 511-533.
Simplices are sorted vertex tuples in filtration order; list index is the birth time.
"""


def reduce(simplices):
    # ponytail: plain column reduction, no clearing or twist; worst case cubic in simplex count
    index = {s: i for i, s in enumerate(simplices)}
    columns = [
        {index[s[:k] + s[k + 1:]] for k in range(len(s))} if len(s) > 1 else set()
        for s in simplices
    ]
    pivot_col = {}
    for j, col in enumerate(columns):
        while col and max(col) in pivot_col:
            col ^= columns[pivot_col[max(col)]]
        if col:
            pivot_col[max(col)] = j
    pairs = [(len(simplices[i]) - 1, i, j) for i, j in sorted(pivot_col.items())]
    essential = [
        (len(simplices[j]) - 1, j)
        for j, col in enumerate(columns)
        if not col and j not in pivot_col
    ]
    return sorted(pairs), sorted(essential)
