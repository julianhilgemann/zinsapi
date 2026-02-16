from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller


@dataclass(frozen=True)
class ForecastResult:
    order: Tuple[int, int, int]
    forecast: pd.Series
    conf_int: pd.DataFrame
    metadata: dict


def determine_integration_order(series: pd.Series, max_d: int = 2, alpha: float = 0.05) -> int:
    series = series.dropna()
    if len(series) < 10:
        return 1

    for d in range(max_d + 1):
        test_series = series.diff(d).dropna() if d > 0 else series
        if len(test_series) < 10:
            continue
        try:
            p_value = adfuller(test_series, autolag="AIC")[1]
        except Exception:
            p_value = 1.0
        if p_value < alpha:
            return d

    return max_d


def _rmse(errors: Iterable[float]) -> float:
    errors = list(errors)
    if not errors:
        return float("inf")
    return math.sqrt(float(np.mean(np.square(errors))))


def select_arima_order(
    series: pd.Series, d: int, max_p: int = 3, max_q: int = 3
) -> Tuple[Tuple[int, int, int], float]:
    series = series.dropna()
    n = len(series)
    min_train = max(24, d + 2)

    if n < min_train + 3:
        return (1, d, 1), float("inf")

    eval_points = min(12, n - min_train)
    start_idx = n - eval_points

    best_order = (1, d, 1)
    best_rmse = float("inf")

    warnings.filterwarnings("ignore")

    for p in range(max_p + 1):
        for q in range(max_q + 1):
            order = (p, d, q)
            errors = []
            for idx in range(start_idx, n):
                train = series.iloc[:idx]
                test_value = series.iloc[idx]
                if len(train) < min_train:
                    continue
                try:
                    model = ARIMA(
                        train,
                        order=order,
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit()
                    pred = float(model.forecast(1).iloc[0])
                    errors.append(test_value - pred)
                except Exception:
                    errors = []
                    break
            score = _rmse(errors)
            if score < best_rmse:
                best_rmse = score
                best_order = order

    return best_order, best_rmse


def fit_and_forecast(series: pd.Series, horizon: int = 12) -> ForecastResult:
    series = series.dropna()
    d = determine_integration_order(series)
    order, cv_rmse = select_arima_order(series, d)

    model = ARIMA(
        series,
        order=order,
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit()

    prediction = model.get_forecast(steps=horizon)
    forecast = prediction.predicted_mean
    conf_int = prediction.conf_int()
    conf_int.columns = ["lower", "upper"]

    metadata = {
        "order": order,
        "aic": float(model.aic) if model.aic is not None else None,
        "bic": float(model.bic) if model.bic is not None else None,
        "llf": float(model.llf) if model.llf is not None else None,
        "nobs": int(model.nobs) if model.nobs is not None else None,
        "cv_rmse": float(cv_rmse) if cv_rmse is not None else None,
        "horizon": int(horizon),
    }

    return ForecastResult(order=order, forecast=forecast, conf_int=conf_int, metadata=metadata)
