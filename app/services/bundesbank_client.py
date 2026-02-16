from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import requests

from app.config import SETTINGS


def _build_api_url() -> str:
    return (
        f"{SETTINGS.api_base}/data/{SETTINGS.flow_ref}/{SETTINGS.series_key}"
        f"?format={SETTINGS.api_format}&detail={SETTINGS.api_detail}"
    )


def _build_direct_csv_url() -> str:
    return (
        "https://www.bundesbank.de/statistic-rmi/StatisticDownload"
        f"?tsId={SETTINGS.series_ts_id}"
        "&mode=its"
        "&its_csvFormat=en"
        "&its_currency=default"
        "&its_dateFormat=default"
    )


def _maybe_cache(text: str, filename: str) -> None:
    if os.getenv("CACHE_BB_DOWNLOAD", "false").lower() != "true":
        return
    cache_dir = Path(SETTINGS.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / filename).write_text(text, encoding="utf-8")


def _read_local_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def fetch_csv_text() -> str:
    """Fetch CSV text from Bundesbank REST API or fallback sources.

    Priority:
    1) Local CSV if BUNDESBANK_LOCAL_CSV is set
    2) Bundesbank REST API (sdmx_csv)
    3) Direct CSV download (statistic-rmi)
    4) Sample CSV (if ALLOW_SAMPLE_FALLBACK=true)
    """
    if SETTINGS.local_csv_path:
        return _read_local_file(SETTINGS.local_csv_path)

    last_error: Optional[Exception] = None

    api_url = _build_api_url()
    try:
        resp = requests.get(api_url, timeout=SETTINGS.request_timeout_s)
        resp.raise_for_status()
        _maybe_cache(resp.text, f"{SETTINGS.series_ts_id}.api.csv")
        return resp.text
    except Exception as exc:  # pragma: no cover - network-dependent
        last_error = exc

    direct_url = _build_direct_csv_url()
    try:
        resp = requests.get(direct_url, timeout=SETTINGS.request_timeout_s)
        resp.raise_for_status()
        _maybe_cache(resp.text, f"{SETTINGS.series_ts_id}.direct.csv")
        return resp.text
    except Exception as exc:  # pragma: no cover - network-dependent
        last_error = exc

    if SETTINGS.allow_sample_fallback and Path(SETTINGS.sample_csv_path).exists():
        return _read_local_file(SETTINGS.sample_csv_path)

    if last_error is None:
        raise RuntimeError("Failed to fetch Bundesbank CSV: unknown error")
    raise RuntimeError("Failed to fetch Bundesbank CSV") from last_error
