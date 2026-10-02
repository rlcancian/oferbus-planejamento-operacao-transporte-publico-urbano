from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence

from .demand import passengers_per_minute, original_curve, adjust_curve_legacy
from .model import TripObservation


@dataclass(frozen=True)
class RenewalIndexResult:
    original: tuple[float, ...]
    adjusted: tuple[float, ...]
    mean: float


def travel_time_curve_legacy(
    trips: Sequence[TripObservation], *, start_minute: int | None = None, preserve_sentinel_bug: bool = True
) -> list[float]:
    """Port of ``MPROCEDI.Calcula_Org_Tmp`` for one direction.

    The source uses -1 for a missing observed travel time and -2 as an artificial
    boundary sentinel. In the 2008c code the final-sentinel repair tests
    ``Flag(Qui) = 2`` rather than ``-2``. This has two observable consequences:
    a trailing missing value is not repaired, and a legitimate final travel time
    of exactly 2 minutes is overwritten by the preceding value.
    ``preserve_sentinel_bug=True`` reproduces both effects; False applies the
    strongly suggested ``-2`` correction.
    """
    if not trips:
        raise ValueError("at least one observed trip is required")
    start = trips[0].minute if start_minute is None else start_minute
    end = trips[-1].minute
    total = end - start + 1
    if total < 1:
        raise ValueError("trip times must be nondecreasing")

    # 1-based fixed-array style buffers.
    n = len(trips)
    flag = [0] * (max(402, n + 4))
    hour = [0] * len(flag)
    qui = 0

    for cont in range(1, n + 1):
        obs = trips[cont - 1]
        flag[cont] = -1 if obs.travel_time == 0 else int(obs.travel_time)
        if flag[cont] > -1:
            if cont > 1 and flag[1] == -1:
                qui += 1
                flag[1] = -2
                hour[1] = start
            qui += 1
            flag[qui] = flag[cont]
            hour[qui] = obs.minute
        if cont == n and flag[n] == -1:
            qui += 1
            flag[qui] = -2
            hour[qui] = obs.minute

    if qui == 0:
        raise ValueError("legacy TPV interpolation has no valid travel-time observation")
    if flag[1] == -2:
        if qui < 2:
            raise ValueError("legacy TPV interpolation cannot repair an all-missing series")
        flag[1] = flag[2]
    # Deliberate source divergence switch: code says '= 2'; intended sentinel is -2.
    if (flag[qui] == 2) if preserve_sentinel_bug else (flag[qui] == -2):
        if qui < 2:
            raise ValueError("legacy TPV interpolation has insufficient boundary data")
        flag[qui] = flag[qui - 1]

    out = [0.0] * (total + 2)
    if qui == 1:
        # The original procedure does not explicitly fill this degenerate case.
        # Characterization policy: expose it rather than silently fabricate a curve.
        raise ValueError("legacy TPV interpolation requires at least two compacted points")

    for cont in range(2, qui + 1):
        aux_f = hour[1] if cont == 2 else hour[cont - 1] + 1
        denom = hour[cont] - hour[cont - 1]
        if denom == 0:
            raise ZeroDivisionError("legacy TPV interpolation would divide by zero")
        for minute in range(aux_f, hour[cont] + 1):
            aux_a = (minute - hour[cont]) / denom
            idx = minute - start + 1
            if 1 <= idx <= total:
                out[idx] = flag[cont] + (flag[cont] - flag[cont - 1]) * aux_a
    return out


def travel_time_curves_legacy(
    trips: Sequence[TripObservation], *, adjustment_level: int, start_minute: int | None = None,
    preserve_sentinel_bug: bool = True,
) -> tuple[list[float], list[float]]:
    original = travel_time_curve_legacy(
        trips, start_minute=start_minute, preserve_sentinel_bug=preserve_sentinel_bug
    )
    adjusted = adjust_curve_legacy(original, adjustment_level)
    return original, adjusted


def renewal_index_curves_legacy(
    trips: Sequence[TripObservation], *, demand_original: Sequence[float], adjustment_level: int,
    constant_ir: float | None = None,
) -> RenewalIndexResult:
    """Reconstruct the IR branch of ``Realiza_Ajuste_De_Curvas``.

    ``constant_ir`` corresponds to ``CodIndiceRenova = 0``.  When omitted,
    passenger counts in the critical section are converted to an observed IR
    curve as ``demand / critical-section-passengers`` and clamped to IR >= 1.
    """
    total = len(demand_original) - 2
    if total <= 0:
        raise ValueError("demand curve must be a 1-based series with a spare cell")

    original = [0.0] * (total + 2)
    if constant_ir is not None:
        for i in range(1, total + 1):
            original[i] = float(constant_ir)
        mean = float(constant_ir)
    else:
        ppm_critical = passengers_per_minute(trips, critical=True)
        ptc = original_curve(trips, ppm_critical)
        if len(ptc) < total + 2:
            ptc.extend([0.0] * (total + 2 - len(ptc)))
        acc = 0.0
        for i in range(1, total + 1):
            ir = 1.0 if ptc[i] == 0 else float(demand_original[i]) / float(ptc[i])
            if ir < 1.0:
                ir = 1.0
            original[i] = ir
            acc += ir
        mean = acc / total

    adjusted = adjust_curve_legacy(original, adjustment_level)
    return RenewalIndexResult(tuple(original), tuple(adjusted), mean)
