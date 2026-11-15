"""Small-sample statistics shown next to observed ratios. A 95% Wilson interval makes 'only 4 tests' visible as a number."""
import math


def wilson(k: int, n: int, z: float = 1.96):
    """95% Wilson score interval for k successes in n trials, as (low, high) fractions. None when n == 0."""
    if not n:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def interval_text(k: int, n: int, t) -> str:
    """Plain sentence about what k of n can and cannot tell us."""
    ci = wilson(k, n)
    if ci is None:
        return ""
    lo, hi = round(ci[0] * 100), round(ci[1] * 100)
    return t("With {n} tests, the true ignition rate could be anywhere from about {lo}% to {hi}% (95% interval).", n=n, lo=lo, hi=hi)
