from __future__ import annotations

import os

os.environ.setdefault(
    "BUNDESBANK_LOCAL_CSV",
    "data/sample/BBIN1.M.D0.ECB.ECBMIN.EUR.ME.sample.csv",
)

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def main() -> None:
    client = TestClient(app)
    response = client.get("/forecast")
    print(f"STATUS: {response.status_code}")
    lines = response.text.splitlines()
    print("OUTPUT (first 15 lines):")
    for line in lines[:15]:
        print(line)


if __name__ == "__main__":
    main()
