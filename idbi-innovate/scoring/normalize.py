"""Value coercion + normalization helpers for the scoring engine (pure stdlib)."""


def num(row, key):
    """Return a float for row[key], or None if missing/blank."""
    v = row.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def avail(row, source):
    """True if `<source>_available` flag is set."""
    v = row.get(f"{source}_available")
    return str(v) == "1"


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def lin(x, lo, hi):
    """Map x in [lo,hi] -> [0,100], clamped. Handles inverted ranges (lo>hi)."""
    if x is None:
        return None
    if hi == lo:
        return 50.0
    t = (x - lo) / (hi - lo)
    return clamp(t, 0.0, 1.0) * 100.0


def log_norm(x, lo, hi):
    """Like lin() but on a log scale — right for money/counts spanning orders of magnitude."""
    import math
    if x is None or x <= 0:
        return None
    lo = max(lo, 1e-9)
    hi = max(hi, lo * 1.0001)
    t = (math.log(x) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return clamp(t, 0.0, 1.0) * 100.0


def wmean(pairs):
    """Weighted mean of [(value, weight), ...] ignoring None values. Returns None if empty."""
    num_, den = 0.0, 0.0
    for v, w in pairs:
        if v is None:
            continue
        num_ += v * w
        den += w
    if den == 0:
        return None
    return num_ / den
