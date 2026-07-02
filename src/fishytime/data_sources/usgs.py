from datetime import datetime, timezone

import requests

from fishytime.config import WaterBody
from fishytime.models import StreamflowReading

BASE_URL = "https://api.waterdata.usgs.gov/ogcapi/v0/collections"
HEADERS = {"Accept": "application/geo+json"}
TIMEOUT_S = 10

PARAM_DISCHARGE = "00060"
PARAM_GAGE_HEIGHT = "00065"
PARAM_WATER_TEMP = "00010"


def _get_items(collection: str, params: dict) -> list[dict]:
    """Fetch feature properties from an OGC API collection. Returns [] on any failure."""
    try:
        resp = requests.get(
            f"{BASE_URL}/{collection}/items",
            params=params,
            headers=HEADERS,
            timeout=TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return []
    return [feature["properties"] for feature in data.get("features", [])]


def _latest_value(properties: list[dict], parameter_code: str) -> tuple[float, datetime] | None:
    matches = [p for p in properties if p.get("parameter_code") == parameter_code]
    if not matches:
        return None
    latest = max(matches, key=lambda p: p["time"])
    try:
        value = float(latest["value"])
    except (KeyError, TypeError, ValueError):
        return None
    observed_at = datetime.fromisoformat(latest["time"])
    return value, observed_at


def _flow_trend_pct_per_day(site_id: str) -> float | None:
    """Percent change in discharge over the last 2 days of continuous readings, or None."""
    properties = _get_items(
        "continuous",
        {"monitoring_location_id": site_id, "parameter_code": PARAM_DISCHARGE, "time": "P2D"},
    )
    readings = []
    for p in properties:
        try:
            readings.append((datetime.fromisoformat(p["time"]), float(p["value"])))
        except (KeyError, TypeError, ValueError):
            continue
    if len(readings) < 2:
        return None
    readings.sort(key=lambda r: r[0])
    earliest_time, earliest_value = readings[0]
    latest_time, latest_value = readings[-1]
    elapsed_days = (latest_time - earliest_time).total_seconds() / 86400
    if elapsed_days <= 0 or earliest_value == 0:
        return None
    return ((latest_value - earliest_value) / earliest_value) * 100 / elapsed_days


def get_streamflow(water: WaterBody) -> StreamflowReading | None:
    """Fetch the latest streamflow reading for a water body.

    Returns None if the water body has no configured gauge, or if every
    request failed. A gauge that responds but lacks some parameters (e.g. no
    water temp sensor) still returns a StreamflowReading with those fields
    set to None.
    """
    if water.usgs_site_id is None:
        return None

    site_id = f"USGS-{water.usgs_site_id}"
    is_daily_only = False

    properties = _get_items("latest-continuous", {"monitoring_location_id": site_id})
    discharge = _latest_value(properties, PARAM_DISCHARGE)
    if discharge is None:
        properties = _get_items("latest-daily", {"monitoring_location_id": site_id})
        discharge = _latest_value(properties, PARAM_DISCHARGE)
        is_daily_only = True

    if discharge is None:
        return None

    gage_height = _latest_value(properties, PARAM_GAGE_HEIGHT)
    water_temp = _latest_value(properties, PARAM_WATER_TEMP)

    return StreamflowReading(
        discharge_cfs=discharge[0],
        gage_height_ft=gage_height[0] if gage_height else None,
        water_temp_c=water_temp[0] if water_temp else None,
        flow_trend_pct_per_day=None if is_daily_only else _flow_trend_pct_per_day(site_id),
        observed_at=discharge[1],
        is_daily_only=is_daily_only,
    )
