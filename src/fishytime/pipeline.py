from datetime import date

from fishytime.config import WATERS
from fishytime.data_sources import moon, snowpack, stocking, usgs
from fishytime.data_sources import weather as weather_source
from fishytime.models import ScoreResult
from fishytime.scoring import score_conditions


def run_pipeline(target_date: date) -> list[ScoreResult]:
    """Score every configured water body for target_date, ranked best first.

    A broken fetcher for one water body never aborts the whole run -- it just
    degrades that water's score_conditions inputs to None, which scoring.py
    turns into caveats.
    """
    results = []
    for water in WATERS:
        try:
            streamflow = usgs.get_streamflow(water)
        except Exception:
            streamflow = None
        try:
            weather = weather_source.get_forecast(water.lat, water.lon)
        except Exception:
            weather = None

        moon_info = moon.get_moon_info(water.lat, water.lon, target_date)
        recent_stocking = stocking.get_recent_stocking(water)
        recent_snowpack = snowpack.get_snowpack(water)

        result = score_conditions(water, streamflow, weather, moon_info, recent_stocking, recent_snowpack)
        results.append(result)

    results.sort(key=lambda r: r.total_score, reverse=True)
    return results
