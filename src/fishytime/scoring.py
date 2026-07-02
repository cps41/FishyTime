from fishytime.config import WaterBody
from fishytime.models import FactorScore, MoonInfo, ScoreResult, StreamflowReading, WeatherReading


def _triangular_goodness(x: float, low: float, peak: float, high: float) -> float:
    """0 at/outside [low, high], rising linearly to 1 at peak."""
    if x <= low or x >= high:
        return 0.0
    if x <= peak:
        return (x - low) / (peak - low)
    return (high - x) / (high - peak)


def _water_temp_factor(streamflow: StreamflowReading | None) -> FactorScore:
    if streamflow is None or streamflow.water_temp_c is None:
        return FactorScore(
            name="Water temperature",
            value=0.0,
            weight=3,
            reason="no water temp data available for this gauge",
            missing=True,
        )
    temp_f = streamflow.water_temp_c * 9 / 5 + 32
    goodness = _triangular_goodness(temp_f, low=45, peak=58, high=70)
    quality = "ideal" if goodness > 0.8 else "workable" if goodness > 0.3 else "poor"
    return FactorScore(
        name="Water temperature",
        value=goodness * 2 - 1,
        weight=3,
        reason=f"water temp {temp_f:.0f}°F ({quality} for trout)",
    )


def _flow_trend_factor(streamflow: StreamflowReading | None) -> FactorScore:
    if streamflow is None or streamflow.flow_trend_pct_per_day is None:
        return FactorScore(
            name="Flow trend",
            value=0.0,
            weight=2,
            reason="no flow trend data (daily-only gauge or no gauge)",
            missing=True,
        )
    trend = streamflow.flow_trend_pct_per_day
    abs_trend = abs(trend)
    if abs_trend <= 5:
        value, desc = 1.0, "stable"
    elif abs_trend <= 15:
        value, desc = 0.3, "mildly changing"
    elif abs_trend <= 30:
        value, desc = -0.3, "unsettled"
    else:
        value, desc = -1.0, "spiking"
    return FactorScore(name="Flow trend", value=value, weight=2, reason=f"flow {trend:+.1f}%/day ({desc})")


def _pressure_trend_factor(weather: WeatherReading | None) -> FactorScore:
    if weather is None or weather.pressure_trend == "unknown":
        return FactorScore(
            name="Barometric pressure",
            value=0.0,
            weight=2,
            reason="pressure trend unavailable",
            missing=True,
        )
    mapping = {
        "falling": (1.0, "falling pressure (often triggers a bite before a front)"),
        "steady": (0.6, "steady pressure"),
        "rising": (-0.7, "rising pressure (post-frontal, often slower)"),
    }
    value, reason = mapping[weather.pressure_trend]
    return FactorScore(name="Barometric pressure", value=value, weight=2, reason=reason)


def _wind_factor(weather: WeatherReading | None) -> FactorScore:
    if weather is None or weather.wind_speed_mph is None:
        return FactorScore(name="Wind", value=0.0, weight=1, reason="no wind data", missing=True)
    wind = weather.wind_speed_mph
    if wind <= 8:
        value = 1.0
    elif wind <= 15:
        value = 0.3
    elif wind <= 20:
        value = -0.3
    else:
        value = -1.0
    return FactorScore(name="Wind", value=value, weight=1, reason=f"wind {wind:.0f} mph")


def _precip_factor(weather: WeatherReading | None) -> FactorScore:
    if weather is None or weather.precip_probability_pct is None:
        return FactorScore(name="Precipitation", value=0.0, weight=1, reason="no precip data", missing=True)
    precip = weather.precip_probability_pct
    if precip <= 20:
        value, desc = 0.6, "low chance of rain"
    elif precip <= 60:
        value, desc = 0.2, "moderate chance of rain"
    else:
        value, desc = -0.6, "high chance of rain"
    return FactorScore(name="Precipitation", value=value, weight=1, reason=f"{precip:.0f}% precip ({desc})")


def _sky_cover_factor(weather: WeatherReading | None) -> FactorScore:
    if weather is None or weather.sky_cover_pct is None:
        return FactorScore(name="Sky cover", value=0.0, weight=1, reason="no sky cover data", missing=True)
    sky_cover = weather.sky_cover_pct
    if sky_cover >= 40:
        value, desc = 0.8, "overcast (low light favors trout feeding)"
    else:
        value, desc = 0.0, "mostly clear (bright, tougher bite)"
    return FactorScore(name="Sky cover", value=value, weight=1, reason=f"{sky_cover:.0f}% cloud cover ({desc})")


def _stocking_factor(stocking: bool | None) -> FactorScore:
    if stocking is None:
        return FactorScore(
            name="Recent stocking",
            value=0.0,
            weight=1,
            reason="stocking data not available yet (deferred to a later stage)",
            missing=True,
        )
    if stocking:
        return FactorScore(name="Recent stocking", value=1.0, weight=1, reason="recently stocked")
    return FactorScore(name="Recent stocking", value=0.0, weight=1, reason="no recent stocking recorded")


def _moon_factor(moon: MoonInfo) -> FactorScore:
    distance_from_quarter = abs(moon.moon_illumination_pct - 50) / 50
    return FactorScore(
        name="Moon phase",
        value=distance_from_quarter,
        weight=0.5,
        reason=(
            f"moon illumination {moon.moon_illumination_pct:.0f}%, "
            f"best window {moon.sunrise:%H:%M}-{moon.sunset:%H:%M} (dawn/dusk)"
        ),
    )


def score_conditions(
    water: WaterBody,
    streamflow: StreamflowReading | None,
    weather: WeatherReading | None,
    moon: MoonInfo,
    stocking: bool | None = None,
    snowpack: float | None = None,
) -> ScoreResult:
    """Pure, deterministic scoring: no I/O, missing inputs degrade to a neutral
    contribution plus a caveat rather than raising."""
    factors = [
        _water_temp_factor(streamflow),
        _flow_trend_factor(streamflow),
        _pressure_trend_factor(weather),
        _wind_factor(weather),
        _precip_factor(weather),
        _sky_cover_factor(weather),
        _stocking_factor(stocking),
        _moon_factor(moon),
    ]

    caveats = [f"{f.name}: {f.reason}" for f in factors if f.missing]
    if streamflow is None:
        caveats.insert(0, "No live gauge data available for this water.")
    if weather is None:
        caveats.insert(0, "No weather data available for this water.")

    total_score = round(sum(f.contribution for f in factors), 2)
    return ScoreResult(water_name=water.name, total_score=total_score, factors=factors, caveats=caveats)
