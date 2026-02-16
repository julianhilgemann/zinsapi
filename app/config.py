from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_base: str = os.getenv("BUNDESBANK_API_BASE", "https://api.statistiken.bundesbank.de/rest")
    series_ts_id: str = os.getenv("BUNDESBANK_TS_ID", "BBIN1.M.D0.ECB.ECBMIN.EUR.ME")
    flow_ref: str = os.getenv("BUNDESBANK_FLOW_REF", "BBIN1")
    series_key: str = os.getenv("BUNDESBANK_SERIES_KEY", "M.D0.ECB.ECBMIN.EUR.ME")
    api_format: str = os.getenv("BUNDESBANK_FORMAT", "sdmx_csv")
    api_detail: str = os.getenv("BUNDESBANK_DETAIL", "dataonly")
    cache_dir: str = os.getenv("BUNDESBANK_CACHE_DIR", "data/cache")
    local_csv_path: str | None = os.getenv("BUNDESBANK_LOCAL_CSV")
    allow_sample_fallback: bool = os.getenv("ALLOW_SAMPLE_FALLBACK", "false").lower() == "true"
    write_intermediate: bool = os.getenv("WRITE_INTERMEDIATE", "true").lower() == "true"
    sample_csv_path: str = os.getenv(
        "BUNDESBANK_SAMPLE_CSV",
        "data/sample/BBIN1.M.D0.ECB.ECBMIN.EUR.ME.sample.csv",
    )
    request_timeout_s: int = int(os.getenv("BUNDESBANK_TIMEOUT", "30"))


SETTINGS = Settings()
