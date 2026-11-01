"""Turn a saved quotient_polytope.json row into (n, family) for first_ticket_classes.classes."""


def row_to_family(row):
    return len(row["tickets"]), [frozenset(s) for s in row["family"]]
