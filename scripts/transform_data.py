from __future__ import annotations

import argparse

from app.services.bundesbank_client import fetch_csv_text
from app.services.transformer import load_time_series


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform Bundesbank CSV into clean time series")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    csv_text = fetch_csv_text()
    ts_df = load_time_series(csv_text)
    csv_out = ts_df.assign(timestamp=ts_df["period"].astype(str)).drop(columns=["period"]).to_csv(
        index=False
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(csv_out)
    else:
        print(csv_out)


if __name__ == "__main__":
    main()
