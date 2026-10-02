from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Sequence

@dataclass(frozen=True)
class ForecastResult:
    annual_means: tuple[float, ...]
    forecasts: tuple[float, float, float]  # parabola, logarithmic, exponential
    mse: tuple[float, float, float]
    best_model: int  # 1..3, matching legacy storage


def _solve3(a: list[list[float]], b: list[float]) -> list[float]:
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("singular normal equations")
        m[col], m[pivot] = m[pivot], m[col]
        p = m[col][col]
        for j in range(col, 4):
            m[col][j] /= p
        for r in range(3):
            if r == col:
                continue
            f = m[r][col]
            for j in range(col, 4):
                m[r][j] -= f * m[col][j]
    return [m[i][3] for i in range(3)]


def fit_forecasts_legacy(monthly_oldest_to_newest: Sequence[float]) -> ForecastResult:
    """Reconstructs the >=3 complete-year regression branch of Previsao_Da_Demanda.

    This function intentionally excludes the legacy <=2-year special branch and monthly
    seasonal selection, which remain separate reconstruction tasks.
    """
    if len(monthly_oldest_to_newest) < 36:
        raise ValueError("this reconstructed branch requires >= 36 monthly observations")
    n_years = len(monthly_oldest_to_newest) // 12
    data = list(monthly_oldest_to_newest[-12 * n_years:])
    mr = [sum(data[12*i:12*(i+1)]) / 12.0 for i in range(n_years)]
    if any(y <= 0 for y in mr):
        raise ValueError("legacy log/exponential fits require positive annual means")
    x = [float(i) for i in range(1, n_years + 1)]
    n = float(n_years)
    s1 = sum(x); s2 = sum(v*v for v in x); s3 = sum(v**3 for v in x); s4 = sum(v**4 for v in x)
    sy = sum(mr); sxy = sum(i*y for i, y in zip(x, mr)); sx2y = sum(i*i*y for i, y in zip(x, mr))

    # y = a*x^2 + b*x + c
    a, b, c = _solve3([[s2, s1, n], [s3, s2, s1], [s4, s3, s2]], [sy, sxy, sx2y])
    next_x = n_years + 1.0
    f_par = a * next_x**2 + b * next_x + c
    mse_par = sum((y - (a*i*i + b*i + c))**2 for i, y in zip(x, mr)) / n_years

    logs = [math.log(i) for i in x]
    sli = sum(logs); sli2 = sum(v*v for v in logs); smrl = sum(y*l for y, l in zip(mr, logs))
    # Preserve the algebra of the VB source, including its coefficient naming/order.
    coef4 = (sli * smrl - sy * sli2) / (sli**2 - n * sli2)
    coef3 = (sy - n * coef4) / sli
    f_log = coef3 * math.log(next_x) + coef4
    mse_log = sum((coef3 * math.log(i) + coef4 - y)**2 for i, y in zip(x, mr)) / n_years

    slmr = sum(math.log(y) for y in mr)
    silmr = sum(i * math.log(y) for i, y in zip(x, mr))
    coef5 = math.exp((s1 * silmr - s2 * slmr) / ((s1**2) - n * s2))
    coef6 = (slmr - n * math.log(coef5)) / s1
    f_exp = coef5 * math.exp(next_x * coef6)
    mse_exp = sum((coef5 * math.exp(i * coef6) - y)**2 for i, y in zip(x, mr)) / n_years

    mses = (mse_par, mse_log, mse_exp)
    best = min(range(3), key=lambda i: mses[i]) + 1
    return ForecastResult(tuple(mr), (f_par, f_log, f_exp), mses, best)
