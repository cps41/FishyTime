import responses

from fishytime.data_sources import weather
from tests.util import load_fixture

LAT, LON = 39.753056, -105.234722


@responses.activate
def test_get_forecast_happy_path():
    responses.add(responses.GET, f"https://api.weather.gov/points/{LAT},{LON}", json=load_fixture("nws_points"))
    responses.add(responses.GET, "https://api.weather.gov/gridpoints/BOU/57,40/forecast", json=load_fixture("nws_forecast"))
    responses.add(responses.GET, "https://api.weather.gov/gridpoints/BOU/57,40", json=load_fixture("nws_gridpoint_raw"))
    responses.add(responses.GET, "https://api.weather.gov/gridpoints/BOU/57,40/stations", json=load_fixture("nws_stations"))
    responses.add(
        responses.GET,
        "https://api.weather.gov/stations/K4BM/observations",
        json=load_fixture("nws_observations_null_pressure"),
    )
    responses.add(
        responses.GET,
        "https://api.weather.gov/stations/KAPA/observations",
        json=load_fixture("nws_observations_falling_pressure"),
    )

    reading = weather.get_forecast(LAT, LON)

    assert reading is not None
    assert reading.temp_f == 68
    assert reading.wind_speed_mph == 5.0
    assert reading.sky_cover_pct == 65
    assert reading.precip_probability_pct == 20
    assert reading.pressure_trend == "falling"


@responses.activate
def test_get_forecast_returns_none_when_points_lookup_fails():
    # No responses registered -> ConnectionError, must be swallowed.
    assert weather.get_forecast(LAT, LON) is None


@responses.activate
def test_get_forecast_degrades_sky_cover_and_pressure_independently():
    responses.add(responses.GET, f"https://api.weather.gov/points/{LAT},{LON}", json=load_fixture("nws_points"))
    responses.add(responses.GET, "https://api.weather.gov/gridpoints/BOU/57,40/forecast", json=load_fixture("nws_forecast"))
    # gridpoint (sky cover) and stations both fail -> no mocks registered for them

    reading = weather.get_forecast(LAT, LON)

    assert reading is not None
    assert reading.temp_f == 68
    assert reading.sky_cover_pct is None
    assert reading.pressure_trend == "unknown"
