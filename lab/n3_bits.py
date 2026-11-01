import math


def bits_lost(n_orders, n_classes):
    if n_classes <= 0 or n_classes > n_orders:
        raise ValueError("need 0 < n_classes <= n_orders")
    return math.log2(n_orders / n_classes)


def exact_loss(sizes):
    if not sizes or any(s <= 0 for s in sizes):
        raise ValueError("sizes must be a non-empty list of positive counts")
    n = sum(sizes)
    return sum(s / n * math.log2(s) for s in sizes)
