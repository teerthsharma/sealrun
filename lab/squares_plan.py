def plan(squares, orders):
    return [[(sx + dx, sz + dz) for sx, sz in squares for dx, dz in order] for order in orders]
