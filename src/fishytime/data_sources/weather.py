import re

import requests

from fishytime.models import WeatherReading

USER_AGENT = "FishyTime (github.com/carlypsills/FishyTime, carlypsills@gmail.com)"
HEADERS = {"Accept": "application/geo+json", "User-Agent": USER_AGENT}
TIMEOUT_S = 10
PRESSURE_TREND_THRESHOLD_PA = 100
MAX_STATIONS_TO_TRY = 5


def _get_json(url: str, params: dict | None = None) -> dict | None:
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT_S)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError):
        return None


def _parse_wind_speed(wind_speed: str | None) -> float | None:
    if not wind_speed:
        return None
    match = re.search(r"\d+(\.\d+)?", wind_speed)
    return float(match.group()) if match else None


def _get_sky_cover(grid_id: str, grid_x: int, grid_y: int) -> float | None:
    data = _get_json(f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}")
    if data is None:
        return None
    values = data.get("properties", {}).get("skyCover", {}).get("values", [])
    if not values:
        return None
    return values[0].get("value")


def _get_pressure_trend(stations_url: str) -> str:
    data = _get_json(stations_url)
    if data is None:
        return "unknown"
    station_ids = [
        f["properties"]["stationIdentifier"]
        for f in data.get("features", [])
        if f.get("properties", {}).get("stationIdentifier")
    ]

    for station_id in station_ids[:MAX_STATIONS_TO_TRY]:
        obs_data = _get_json(
            f"https://api.weather.gov/stations/{station_id}/observations", params={"limit": 5}
        )
        if obs_data is None:
            continue
        readings = []
        for feature in obs_data.get("features", []):
            props = feature.get("properties", {})
            pressure = (props.get("barometricPressure") or {}).get("value")
            timestamp = props.get("timestamp")
            if pressure is not None and timestamp is not None:
                readings.append((timestamp, pressure))
        if len(readings) >= 2:
            readings.sort(key=lambda r: r[0])
            delta = readings[-1][1] - readings[0][1]
            if delta > PRESSURE_TREND_THRESHOLD_PA:
                return "rising"
            if delta < -PRESSURE_TREND_THRESHOLD_PA:
                return "falling"
            return "steady"

    return "unknown"


def get_forecast(lat: float, lon: float) -> WeatherReading | None:
    """Fetch the current forecast/conditions for a point.

    Returns None if the core forecast couldn't be retrieved. Sky cover and
    pressure trend degrade independently (missing -> None / "unknown") since
    they come from separate requests that can fail without invalidating the
    rest of the reading.
    """
    points = _get_json(f"https://api.weather.gov/points/{lat},{lon}")
    if points is None:
        return None
    props = points.get("properties", {})
    forecast_url = props.get("forecast")
    grid_id, grid_x, grid_y = props.get("gridId"), props.get("gridX"), props.get("gridY")
    stations_url = props.get("observationStations")
    if not forecast_url:
        return None

    forecast_data = _get_json(forecast_url)
    periods = (forecast_data or {}).get("properties", {}).get("periods", [])
    if not periods:
        return None
    period = periods[0]

    sky_cover = _get_sky_cover(grid_id, grid_x, grid_y) if grid_id else None
    pressure_trend = _get_pressure_trend(stations_url) if stations_url else "unknown"

    return WeatherReading(
        temp_f=period.get("temperature"),
        wind_speed_mph=_parse_wind_speed(period.get("windSpeed")),
        sky_cover_pct=sky_cover,
        precip_probability_pct=(period.get("probabilityOfPrecipitation") or {}).get("value"),
        pressure_trend=pressure_trend,
    )
