from datetime import datetime

from fishytime.config import WATERS
from fishytime.models import MoonInfo, StreamflowReading, WeatherReading
from fishytime.scoring import score_conditions

CLEAR_CREEK = next(w for w in WATERS if w.name == "Clear Creek")
CHATFIELD = next(w for w in WATERS if w.name == "Chatfield Reservoir")


def _neutral_moon() -> MoonInfo:
    return MoonInfo(
        moon_illumination_pct=50.0,
        sunrise=datetime(2026, 7, 2, 5, 45),
        sunset=datetime(2026, 7, 2, 20, 30),
        is_dawn_dusk_window=True,
    )


def test_ideal_conditions_outscore_poor_conditions():
    ideal_flow = StreamflowReading(
        discharge_cfs=130, gage_height_ft=4.1, water_temp_c=14.4,
        flow_trend_pct_per_day=1.0, observed_at=None,
    )
    ideal_weather = WeatherReading(
        temp_f=65, wind_speed_mph=5, sky_cover_pct=70,
        precip_probability_pct=10, pressure_trend="falling",
    )
    ideal = score_conditions(CLEAR_CREEK, ideal_flow, ideal_weather, _neutral_moon())

    poor_flow = StreamflowReading(
        discharge_cfs=400, gage_height_ft=6.0, water_temp_c=24.0,
        flow_trend_pct_per_day=45.0, observed_at=None,
    )
    poor_weather = WeatherReading(
        temp_f=90, wind_speed_mph=30, sky_cover_pct=10,
        precip_probability_pct=80, pressure_trend="rising",
    )
    poor = score_conditions(CLEAR_CREEK, poor_flow, poor_weather, _neutral_moon())

    assert ideal.total_score > poor.total_score
    # Stocking is always unavailable in Stage 1 (deferred), so it's the one
    # expected caveat even when every other input is present.
    assert ideal.caveats == ["Recent stocking: stocking data not available yet (deferred to a later stage)"]
    assert poor.caveats == ideal.caveats


def test_missing_streamflow_degrades_gracefully():
    weather = WeatherReading(
        temp_f=65, wind_speed_mph=5, sky_cover_pct=70,
        precip_probability_pct=10, pressure_trend="falling",
    )

    result = score_conditions(CHATFIELD, None, weather, _neutral_moon())

    assert isinstance(result.total_score, float)
    assert "No live gauge data available for this water." in result.caveats
    assert any(f.missing for f in result.factors)


def test_missing_everything_still_returns_a_result():
    result = score_conditions(CHATFIELD, None, None, _neutral_moon())

    assert isinstance(result.total_score, float)
    assert "No live gauge data available for this water." in result.caveats
    assert "No weather data available for this water." in result.caveats
    missing_factors = [f for f in result.factors if f.missing]
    assert len(missing_factors) == 7  # everything but moon phase
