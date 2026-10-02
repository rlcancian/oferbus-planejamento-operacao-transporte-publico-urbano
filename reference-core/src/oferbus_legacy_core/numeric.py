import math

def vb_int(x: float) -> int:
    """VB Int(): floor toward -infinity."""
    return math.floor(x)

def legacy_round_gt_half(x: float) -> int:
    """OferBus idiom: Int(x), add one only when fractional part > .5."""
    base = vb_int(x)
    return base + (1 if x - base > 0.5 else 0)
