# SOURCE: https://en.wikipedia.org/wiki/Euler_characteristic "the Euler characteristic χ of its surface is χ = V − E + F"
# Hatcher, Algebraic Topology (2002), Theorem 2.44 (Euler characteristic as alternating sum of cell counts).


def cell_counts(cells):
    verts, edges, faces = set(), set(), set()
    for x, y in cells:
        faces.add((x, y))
        verts.update({(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)})
        edges.update({("h", x, y), ("h", x, y + 1), ("v", x, y), ("v", x + 1, y)})
    return len(verts), len(edges), len(faces)


def euler(cells):
    v, e, f = cell_counts(cells)
    return v - e + f
