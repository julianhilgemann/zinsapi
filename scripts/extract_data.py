from __future__ import annotations

import argparse

from app.services.bundesbank_client import fetch_csv_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Bundesbank CSV")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    csv_text = fetch_csv_text()
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(csv_text)
    else:
        print(csv_text)


if __name__ == "__main__":
    main()
