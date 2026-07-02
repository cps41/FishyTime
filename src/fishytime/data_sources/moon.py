import math
from datetime import date as date_type
from datetime import timezone

from astral import LocationInfo, moon
from astral.sun import sun

from fishytime.models import MoonInfo
from fishytime.timezones import LOCAL_TZ, LOCAL_TZ_NAME

LUNAR_CYCLE_DAYS = 29.53059


def get_moon_info(lat: float, lon: float, target_date: date_type) -> MoonInfo:
    # Astral needs the LOCAL calendar date to pick the correct sunrise/sunset --
    # UTC day boundaries would silently shift which day's events come back (this
    # previously produced a sunset before sunrise). The result is then
    # normalized to UTC for storage; callers convert back to local for display.
    location = LocationInfo(latitude=lat, longitude=lon, timezone=LOCAL_TZ_NAME)
    sun_times = sun(location.observer, date=target_date, tzinfo=LOCAL_TZ)

    phase_days = moon.phase(target_date)
    illumination_pct = (1 - math.cos(2 * math.pi * phase_days / LUNAR_CYCLE_DAYS)) / 2 * 100

    return MoonInfo(
        moon_illumination_pct=illumination_pct,
        sunrise=sun_times["sunrise"].astimezone(timezone.utc),
        sunset=sun_times["sunset"].astimezone(timezone.utc),
        is_dawn_dusk_window=True,
    )
