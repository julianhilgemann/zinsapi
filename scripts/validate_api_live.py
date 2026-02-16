from __future__ import annotations

import os

# Ensure we use live download
os.environ.pop("BUNDESBANK_LOCAL_CSV", None)
os.environ["ALLOW_SAMPLE_FALLBACK"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services.bundesbank_client import fetch_csv_text  # noqa: E402
from app.services.forecast import fit_and_forecast  # noqa: E402
from app.services.pipeline import build_forecast_table  # noqa: E402
from app.config import SETTINGS  # noqa: E402
from app.services.transformer import load_time_series  # noqa: E402


def main() -> None:
    print("Download: started")
    csv_text = fetch_csv_text()
    print("Download: done")

    print("Extraction: started")
    line_count = len(csv_text.splitlines())
    print(f"Extraction: done (lines={line_count})")

    print("Transformation: started")
    ts_df = load_time_series(csv_text)
    print(f"Transformation: done (rows={len(ts_df)})")

    print("Forecast: started")
    result = fit_and_forecast(ts_df["value"], horizon=12)
    print(f"Forecast: done (order={result.order})")

    print("Output: started")
    output = build_forecast_table(horizon=12)
    print(f"Output: done (rows={len(output)})")

    if SETTINGS.write_intermediate:
        print("Intermediates: started")
        cache_dir = SETTINGS.cache_dir
        expected = [
            "raw.csv",
            "clean.csv",
            "forecast.csv",
            "output.csv",
            "model_metadata.json",
        ]
        for name in expected:
            path = f"{cache_dir}/{name}"
            print(f"Intermediates: wrote {path}")

    print("API: started")
    client = TestClient(app)
    response = client.get("/forecast")
    print(f"API Status: {response.status_code}")
    print("API Output (first 15 lines):")
    lines = response.text.splitlines()
    for line in lines[:15]:
        print(line)


if __name__ == "__main__":
    main()
