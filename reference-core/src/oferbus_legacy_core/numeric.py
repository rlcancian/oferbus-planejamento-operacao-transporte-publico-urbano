import math


def vb_int(x: float) -> int:
    """VB Int(): floor toward -infinity."""
    return math.floor(x)


def legacy_round_gt_half(x: float) -> int:
    """OferBus idiom: Int(x), add one only when fractional part > .5."""
    base = vb_int(x)
    return base + (1 if x - base > 0.5 else 0)


def vb_bankers_round(x: float) -> int:
    """Nearest-integer, ties-to-even conversion used for implicit Integer fields.

    This is distinct from OferBus's many explicit ``Int`` + ``> .5`` idioms.
    """
    lo = math.floor(x)
    frac = x - lo
    if frac < 0.5:
        return lo
    if frac > 0.5:
        return lo + 1
    return lo if lo % 2 == 0 else lo + 1
