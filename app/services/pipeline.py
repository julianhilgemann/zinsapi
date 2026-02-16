from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.services.bundesbank_client import fetch_csv_text
from app.services.transformer import load_time_series
from app.services.forecast import fit_and_forecast
from app.config import SETTINGS


def _write_intermediate(
    csv_text: str, ts_df: pd.DataFrame, forecast_df: pd.DataFrame, output: pd.DataFrame, metadata: dict
) -> None:
    if not SETTINGS.write_intermediate:
        return

    cache_dir = Path(SETTINGS.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    (cache_dir / "raw.csv").write_text(csv_text, encoding="utf-8")

    cleaned = ts_df.copy()
    cleaned["timestamp"] = cleaned["period"].astype(str)
    cleaned.drop(columns=["period"]).to_csv(cache_dir / "clean.csv", index=False)

    forecast_df.to_csv(cache_dir / "forecast.csv", index=False)
    output.to_csv(cache_dir / "output.csv", index=False)

    (cache_dir / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True), encoding="utf-8"
    )


def build_forecast_table(horizon: int = 12) -> pd.DataFrame:
    csv_text = fetch_csv_text()
    ts_df = load_time_series(csv_text)

    if ts_df.empty:
        raise ValueError("No time series data available after cleaning")

    forecast_result = fit_and_forecast(ts_df["value"], horizon=horizon)

    freq = ts_df["period"].dt.freq
    if freq is None:
        freq = "M"

    last_period = ts_df["period"].iloc[-1]
    future_periods = pd.period_range(start=last_period + 1, periods=horizon, freq=freq)

    actuals = pd.DataFrame(
        {
            "timestamp": ts_df["period"].astype(str),
            "value": ts_df["value"].astype(float),
            "type": "ACT",
            "lower": None,
            "upper": None,
        }
    )

    forecast = pd.DataFrame(
        {
            "timestamp": future_periods.astype(str),
            "value": forecast_result.forecast.astype(float).values,
            "type": "FCT",
            "lower": forecast_result.conf_int["lower"].astype(float).values,
            "upper": forecast_result.conf_int["upper"].astype(float).values,
        }
    )

    output = pd.concat([actuals, forecast], ignore_index=True)

    metadata = dict(forecast_result.metadata)
    metadata["source_ts_id"] = SETTINGS.series_ts_id
    metadata["source_url"] = (
        f"{SETTINGS.api_base}/data/{SETTINGS.flow_ref}/{SETTINGS.series_key}"
        f"?format={SETTINGS.api_format}&detail={SETTINGS.api_detail}"
    )
    metadata["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    output["meta_order"] = ",".join(str(x) for x in metadata.get("order", []))
    output["meta_aic"] = metadata.get("aic")
    output["meta_bic"] = metadata.get("bic")
    output["meta_llf"] = metadata.get("llf")
    output["meta_nobs"] = metadata.get("nobs")
    output["meta_cv_rmse"] = metadata.get("cv_rmse")
    output["meta_horizon"] = metadata.get("horizon")
    output["meta_source_ts_id"] = metadata.get("source_ts_id")
    output["meta_source_url"] = metadata.get("source_url")
    output["meta_generated_at_utc"] = metadata.get("generated_at_utc")

    base_cols = ["timestamp", "value", "type", "lower", "upper"]
    meta_cols = [
        "meta_order",
        "meta_aic",
        "meta_bic",
        "meta_llf",
        "meta_nobs",
        "meta_cv_rmse",
        "meta_horizon",
        "meta_source_ts_id",
        "meta_source_url",
        "meta_generated_at_utc",
    ]
    output = output[base_cols + meta_cols]
    _write_intermediate(
        csv_text=csv_text,
        ts_df=ts_df,
        forecast_df=forecast,
        output=output,
        metadata=metadata,
    )
    return output
