from __future__ import annotations

import csv
import io
from typing import Tuple

import duckdb
import pandas as pd


_TIME_TOKENS = ("time", "period", "zeit", "date", "datum")
_VALUE_TOKENS = ("value", "wert", "obs_value", "observation")


def _find_header_index(lines: list[str]) -> int:
    for idx, line in enumerate(lines[:80]):
        lowered = line.lower()
        if any(token in lowered for token in _TIME_TOKENS) and (
            "," in line or ";" in line or "\t" in line
        ):
            return idx
    return 0


def _read_csv_with_header(text: str) -> pd.DataFrame:
    text = text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines:
        return pd.DataFrame()

    first_line = lines[0]
    if "TIME_PERIOD" in first_line and "OBS_VALUE" in first_line:
        sep = ";" if ";" in first_line else ","
        return pd.read_csv(io.StringIO(text), sep=sep, engine="python")

    header_idx = _find_header_index(lines)
    sample = lines[header_idx] if header_idx < len(lines) else first_line
    try:
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = None

    return pd.read_csv(
        io.StringIO(text),
        skiprows=header_idx,
        sep=delimiter,
        engine="python",
    )


def _pick_columns(df: pd.DataFrame) -> Tuple[str, str]:
    columns = list(df.columns)
    if not columns:
        raise ValueError("No columns found in CSV")

    def find_col(tokens: Tuple[str, ...]) -> str | None:
        for col in columns:
            lower = str(col).lower()
            if any(tok in lower for tok in tokens):
                return col
        return None

    time_col = find_col(_TIME_TOKENS) or columns[0]
    value_col = find_col(_VALUE_TOKENS) or (columns[1] if len(columns) > 1 else columns[0])

    return time_col, value_col


def _quote_ident(name: str) -> str:
    escaped = str(name).replace('"', '""')
    return f'"{escaped}"'


def _clean_with_duckdb(df: pd.DataFrame, time_col: str, value_col: str) -> pd.DataFrame:
    con = duckdb.connect(":memory:")
    con.register("raw", df)

    time_ident = _quote_ident(time_col)
    value_ident = _quote_ident(value_col)

    query = f"""
        SELECT
            TRIM(CAST({time_ident} AS VARCHAR)) AS timestamp,
            CAST(REPLACE(TRIM(CAST({value_ident} AS VARCHAR)), ',', '.') AS DOUBLE) AS value
        FROM raw
        WHERE {value_ident} IS NOT NULL
          AND TRIM(CAST({value_ident} AS VARCHAR)) != ''
    """
    cleaned = con.execute(query).df()
    con.close()
    return cleaned


def _parse_periods(ts: pd.Series) -> pd.Series:
    ts_str = ts.astype(str).str.strip()
    if ts_str.str.match(r"^\d{4}-\d{2}$").all():
        return pd.PeriodIndex(ts_str, freq="M")
    if ts_str.str.match(r"^\d{4}-\d{2}-\d{2}$").all():
        return pd.to_datetime(ts_str).dt.to_period("D")
    if ts_str.str.match(r"^\d{4}$").all():
        return pd.PeriodIndex(ts_str, freq="A")

    parsed = pd.to_datetime(ts_str, errors="coerce")
    if parsed.notna().all():
        return parsed.dt.to_period("M")

    # Fallback: try YYYYMM
    if ts_str.str.match(r"^\d{6}$").all():
        parsed = pd.to_datetime(ts_str, format="%Y%m")
        return parsed.dt.to_period("M")

    raise ValueError("Unable to parse timestamps into periods")


def load_time_series(csv_text: str) -> pd.DataFrame:
    raw_df = _read_csv_with_header(csv_text)
    if raw_df.empty:
        raise ValueError("CSV content is empty or unreadable")

    time_col, value_col = _pick_columns(raw_df)
    cleaned = _clean_with_duckdb(raw_df, time_col, value_col)

    cleaned = cleaned.dropna(subset=["timestamp", "value"]).copy()
    cleaned["period"] = _parse_periods(cleaned["timestamp"])
    cleaned["value"] = cleaned["value"].astype(float)

    cleaned = cleaned.sort_values("period").drop_duplicates("period")
    return cleaned[["period", "value"]].reset_index(drop=True)
