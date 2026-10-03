from __future__ import annotations
from typing import Sequence
from .model import TripObservation


def _value(t: TripObservation, critical: bool) -> int:
    return t.critical_passengers if critical else t.passengers


def passengers_per_minute(trips: Sequence[TripObservation], *, critical: bool = False) -> list[float]:
    """Port of MPROCEDI.Calcula_Passageiros_Por_Minuto.

    Returns a 1-based vector: index 0 is unused. A zero-valued sentinel is appended
    internally to reproduce the legacy fixed-array behavior on the last observation.
    """
    n = len(trips)
    if n < 2:
        raise ValueError("legacy algorithm requires at least two observed trips")
    t = [TripObservation(0, 0, 0, 0), *trips, TripObservation(0, 0, 0, 0)]
    out = [0.0] * (n + 2)
    cont = 2
    while cont <= n:
        diff = t[cont].minute - t[cont - 1].minute
        if diff > 0:
            next_diff = t[cont + 1].minute - t[cont].minute
            if next_diff > 0:
                out[cont] = _value(t[cont], critical) / diff
                cont += 1
            else:
                out[cont] = (_value(t[cont], critical) + _value(t[cont + 1], critical)) / diff
                if cont + 1 < len(out):
                    out[cont + 1] = out[cont]
                cont += 2
        else:
            cont2 = 0
            diff = 0
            passengers = 0
            while diff == 0 and cont + cont2 <= n:
                cont2 += 1
                diff = ((t[cont].minute - t[cont - 1].minute) +
                        (t[cont + cont2].minute - t[cont + cont2 - 1].minute))
                # This intentionally mirrors the source assignment rather than accumulation.
                passengers = _value(t[cont], critical) + _value(t[cont + cont2], critical)
            result = 0.0 if diff == 0 else passengers / diff
            for k in range(cont, min(cont + cont2, n) + 1):
                out[k] = result
            cont += cont2 + 1

    diff = t[n].minute - t[n - 1].minute
    if diff == 0:
        cont2 = n
        diff = 0
        passengers = 0
        while diff == 0 and cont2 > 1:
            cont2 -= 1
            diff = t[cont2].minute - t[cont2 - 1].minute
            passengers += _value(t[cont2], critical)
        if cont2 != n and diff != 0:
            for k in range(cont2, n + 1):
                out[k] = passengers / diff
    return out


def original_curve(trips: Sequence[TripObservation], ppm: Sequence[float]) -> list[float]:
    """Port of MPROCEDI.Calcula_Curva_Original, returned as a 1-based minute series."""
    n = len(trips)
    if n < 2:
        raise ValueError("legacy algorithm requires at least two observed trips")
    start = trips[0].minute
    end = trips[-1].minute
    total = end - start + 1
    out = [0.0] * (total + 2)
    if trips[1].minute - trips[0].minute > 0:
        for minute in range(trips[0].minute, trips[1].minute + 1):
            out[minute - start + 1] = ppm[2]
    else:
        out[1] = ppm[1]
    for cont in range(3, n + 1):
        cur = trips[cont - 1]
        prev = trips[cont - 2]
        if cur.minute - prev.minute > 0:
            for minute in range(prev.minute + 1, cur.minute + 1):
                out[minute - start + 1] = ppm[cont]
    return out


def adjust_curve_legacy(curve: Sequence[float], level: int) -> list[float]:
    """Faithful 1-based port of MPROCEDI.Ajusta_Uma_Curva for one direction."""
    if level < 0:
        raise ValueError("level must be >= 0")
    total = len(curve) - 2 if len(curve) >= 2 and curve[-1] == 0 else len(curve) - 1
    # normalize to 1-based buffer with one spare cell because legacy writes total+1.
    c = [0.0] * (max(total + 12, 1460))
    for i in range(1, min(total, len(curve) - 1) + 1):
        c[i] = float(curve[i])
    out = [0.0] * len(c)

    cont = 5
    while cont + 5 < total:
        out[cont] = sum(c[cont - 4: cont + 6]) / 10.0
        cont += 10
    if cont + 5 >= total:
        denom = total - cont + 5
        if denom <= 0:
            raise ValueError("curve too short for legacy adjustment")
        s = sum(c[cont - 4: total + 1])
        out[cont] = s / denom
        if cont + 10 <= 1440:
            out[cont + 10] = out[cont]

    previous = [0.0] * 20
    point = 5
    for window_edge in range(0, level):
        for j in range(window_edge + 1, 1, -1):
            previous[j] = previous[j - 1]
        previous[1] = out[point]
        s = sum(previous[2:window_edge + 2])
        for j in range(0, window_edge + 1):
            s += out[point + j * 10]
        out[point] = s / (window_edge * 2 + 1)
        point += 10

    middle_count = (total // 10) - (level * 2)
    for _ in range(max(0, middle_count)):
        for j in range(level + 1, 1, -1):
            previous[j] = previous[j - 1]
        previous[1] = out[point]
        s = sum(previous[2:level + 2])
        for j in range(0, level + 1):
            s += out[point + j * 10]
        out[point] = s / (level * 2 + 1 if level > 0 else 1)
        point += 10

    for window_edge in range(level - 1, -1, -1):
        for j in range(window_edge + 1, 1, -1):
            previous[j] = previous[j - 1]
        previous[1] = out[point]
        s = sum(previous[2:window_edge + 2])
        for j in range(0, window_edge + 1):
            s += out[point + j * 10]
        out[point] = s / (window_edge * 2 + 1)
        point += 10

    for i in range(1, 5):
        out[i] = out[5]
    cont = 5
    while cont + 10 <= total:
        inc = (out[cont + 10] - out[cont]) / 10.0
        for j in range(cont + 1, cont + 10):
            out[j] = out[cont] + inc * (j - cont)
        cont += 10
    if cont + 10 > total:
        for j in range(cont + 1, total + 2):
            out[j] = out[cont]
    return out[: total + 2]


def correct_adjusted_curve_legacy(curve: Sequence[float], original_sum: float, first_point: int) -> list[float]:
    """Port of MPROCEDI.Corrige_Curva_Ajustada."""
    out = list(curve)
    total = len(out) - 2
    calc = sum(out[2: total + 1])
    if abs(original_sum - (calc + first_point)) > 2:
        if calc == 0:
            raise ZeroDivisionError("legacy correction would divide by zero")
        factor = (original_sum - int(first_point)) / calc
        for i in range(2, total + 1):
            out[i] *= factor
        out[1] = out[2]
    return out


def robust_maximum_legacy(curve: Sequence[float]) -> float:
    """Port of MPROCEDI.Calcula_Maxi_Por_Medias for one direction."""
    total = len(curve) - 2
    maximum = 0.0
    for i in range(1, total + 1):
        if i == 1 or i == total:
            mean = curve[i]
        elif i == 2 or i == total - 1:
            mean = (curve[i - 1] + curve[i] + curve[i + 1]) / 3.0
        elif i == 3 or i == total - 2:
            mean = sum(curve[i - 2:i + 3]) / 5.0
        else:
            mean = sum(curve[i - 3:i + 4]) / 7.0
        maximum = max(maximum, mean)
    return maximum
