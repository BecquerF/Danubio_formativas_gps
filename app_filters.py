from typing import Any, List, Sequence

import pandas as pd


def sanitize_dropdown_values(current_values: Any, valid_values: Sequence[str]) -> List[str]:
    if not current_values:
        return []

    if isinstance(current_values, str):
        current_values = [current_values]

    valid_set = {str(value) for value in valid_values}
    return [str(value) for value in current_values if str(value) in valid_set]


def build_filter_options(data: Any, column_name: str, current_values: Any) -> tuple[list[dict[str, str]], list[str]]:
    values = data[column_name].dropna().astype(str)
    valid_values = sorted({str(value) for value in values if str(value).strip()})
    options = [{"label": value, "value": value} for value in valid_values]
    filtered_values = sanitize_dropdown_values(current_values, valid_values)
    return options, filtered_values


def normalize_report_date(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return fallback

    if isinstance(value, pd.Timestamp):
        dt = value
    else:
        dt = pd.to_datetime(value, errors="coerce", dayfirst=True)

    if pd.isna(dt):
        return fallback

    return pd.Timestamp(dt).normalize()
