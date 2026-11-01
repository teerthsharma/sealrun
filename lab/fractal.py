import math
import statistics


def variogram(heights, lags):
    out = []
    for lag in lags:
        sq = []
        for (x, z), h in heights.items():
            for nxt in ((x + lag, z), (x, z + lag)):
                if nxt in heights:
                    sq.append((h - heights[nxt]) ** 2)
        if not sq:
            raise ValueError(f"no pairs at lag {lag}")
        out.append((lag, sum(sq) / len(sq) / 2))
    return out


def hurst(heights, lags):
    pairs = variogram(heights, lags)
    fit = statistics.linear_regression(
        [math.log(lag) for lag, _ in pairs], [math.log(g) for _, g in pairs]
    )
    return fit.slope / 2
