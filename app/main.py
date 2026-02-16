from __future__ import annotations

from fastapi import FastAPI, Response

from app.services.pipeline import build_forecast_table

app = FastAPI(title="Zinskompass Forecast API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/forecast", response_class=Response)
def forecast() -> Response:
    table = build_forecast_table(horizon=12)
    csv_text = table.to_csv(index=False)
    return Response(content=csv_text, media_type="text/csv")
