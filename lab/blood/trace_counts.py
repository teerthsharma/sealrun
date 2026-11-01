# SOURCE: https://en.wikipedia.org/wiki/Trace_monoid "defined as the reflexive transitive closure of"
from itertools import product


def trace_key(word, independent):
    seen = {word}
    frontier = [word]
    while frontier:
        w = frontier.pop()
        for i in range(len(w) - 1):
            if (w[i], w[i + 1]) in independent:
                v = w[:i] + (w[i + 1], w[i]) + w[i + 2:]
                if v not in seen:
                    seen.add(v)
                    frontier.append(v)
    return min(seen)


def count_by_length(alphabet, independent, max_length):
    return [
        len({trace_key(w, independent) for w in product(alphabet, repeat=n)})
        for n in range(max_length + 1)
    ]


def series_coefficients(poly, max_length):
    out = []
    for k in range(max_length + 1):
        s = 1 if k == 0 else 0
        for j in range(1, min(k, len(poly) - 1) + 1):
            s -= poly[j] * out[k - j]
        out.append(s)
    return out
