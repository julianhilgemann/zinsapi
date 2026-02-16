from __future__ import annotations

import argparse

from app.services.bundesbank_client import fetch_csv_text
from app.services.transformer import load_time_series
from app.services.forecast import fit_and_forecast


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ARIMA forecast on Bundesbank series")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    csv_text = fetch_csv_text()
    ts_df = load_time_series(csv_text)
    result = fit_and_forecast(ts_df["value"], horizon=args.horizon)

    forecast_df = result.forecast.reset_index(drop=True).to_frame(name="forecast")
    csv_out = forecast_df.to_csv(index=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(csv_out)
    else:
        print(csv_out)


if __name__ == "__main__":
    main()
