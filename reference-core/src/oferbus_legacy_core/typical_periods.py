from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .demand import adjust_curve_legacy


@dataclass(frozen=True)
class TypicalPeriodsResult:
    curve: tuple[float, ...]
    boundaries: tuple[int, ...]  # 1-based minute indices
    thresholds: tuple[float, ...]
    number_of_bands: int
    semantic_variant: str


def _truncate_2(x: float) -> float:
    # Inputs are non-negative in this domain; VB Int(x*100)/100 is floor.
    return int(x * 100.0) / 100.0


def _typical_periods(
    original_curve: Sequence[float], adjusted_for_crossings: Sequence[float], *, number_of_bands: int,
    min_period_minutes: int = 30, semantic_variant: str,
) -> TypicalPeriodsResult:
    total = min(len(original_curve), len(adjusted_for_crossings)) - 2
    if total < 2:
        raise ValueError("curve is too short")
    if number_of_bands < 1:
        raise ValueError("number_of_bands must be >= 1")

    work = [0.0] * (total + 2)
    for i in range(1, total + 1):
        work[i] = _truncate_2(float(adjusted_for_crossings[i]))
    maximum = max(work[1: total + 1], default=0.0)
    thresholds = [_truncate_2((k * maximum) / number_of_bands) for k in range(1, number_of_bands + 1)]

    boundaries = [1]
    for minute in range(2, total):
        for threshold in thresholds[:-1]:
            prev = work[minute - 1]
            cur = work[minute]
            crossed = (prev > threshold and cur < threshold) or (prev < threshold and cur > threshold)
            if crossed:
                boundaries.append(minute)
                # Exact port: a new boundary <=30 min from the previous one is discarded.
                if len(boundaries) > 1 and boundaries[-1] - boundaries[-2] <= min_period_minutes:
                    boundaries.pop()
    boundaries.append(total)

    out = [0.0] * (total + 2)
    first_a, first_b = boundaries[0], boundaries[1]
    mean = sum(original_curve[first_a:first_b + 1]) / (first_b - first_a + 1)
    for i in range(first_a, first_b + 1):
        out[i] = mean

    for k in range(2, len(boundaries)):
        a = boundaries[k - 1] + 1
        b = boundaries[k]
        if b < a:
            continue
        mean = sum(original_curve[a:b + 1]) / (b - a + 1)
        for i in range(a, b + 1):
            out[i] = mean

    return TypicalPeriodsResult(tuple(out), tuple(boundaries), tuple(thresholds), number_of_bands, semantic_variant)


def typical_periods_code_2008(
    original_curve: Sequence[float], *, period_adjustment: int, min_period_minutes: int = 30,
) -> TypicalPeriodsResult:
    """2008c code semantics.

    ``Realiza_Ajuste_De_Curvas`` temporarily forces MDV adjustment level 2 and
    ``Calcula_Periodos_Tipicos`` uses ``AjustePeriodo * 2`` horizontal bands.
    """
    adjusted = adjust_curve_legacy(original_curve, 2)
    return _typical_periods(
        original_curve, adjusted, number_of_bands=period_adjustment * 2,
        min_period_minutes=min_period_minutes, semantic_variant="code-2008c",
    )


def typical_periods_manual_2005(
    original_curve: Sequence[float], *, degree: int, min_period_minutes: int = 30,
) -> TypicalPeriodsResult:
    """Documented Manual-2005 semantics, kept separate from 2008c code.

    The manual states an intermediate MDV degree 3 and a number of horizontal
    bands equal to the selected degree (2..9).  This function is therefore a
    documentation-derived reconstruction, not a claim that 2008c executes it.
    """
    if not 2 <= degree <= 9:
        raise ValueError("Manual 2005 documents degree in [2, 9]")
    adjusted = adjust_curve_legacy(original_curve, 3)
    return _typical_periods(
        original_curve, adjusted, number_of_bands=degree,
        min_period_minutes=min_period_minutes, semantic_variant="manual-2005",
    )
