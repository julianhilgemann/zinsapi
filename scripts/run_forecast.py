from __future__ import annotations

import argparse

from app.services.pipeline import build_forecast_table


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Bundesbank forecast pipeline")
    parser.add_argument("--horizon", type=int, default=12)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    table = build_forecast_table(horizon=args.horizon)
    csv_text = table.to_csv(index=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(csv_text)
    else:
        print(csv_text)


if __name__ == "__main__":
    main()
