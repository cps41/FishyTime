import math
from datetime import date as date_type

from astral import LocationInfo, moon
from astral.sun import sun

from fishytime.models import MoonInfo

LUNAR_CYCLE_DAYS = 29.53059
COLORADO_TIMEZONE = "America/Denver"


def get_moon_info(lat: float, lon: float, target_date: date_type) -> MoonInfo:
    # All configured waters are in Colorado, so the timezone is fixed. Without
    # it, astral resolves `date` against UTC day boundaries, which can return
    # a sunset that falls before sunrise once converted to local time.
    location = LocationInfo(latitude=lat, longitude=lon, timezone=COLORADO_TIMEZONE)
    sun_times = sun(location.observer, date=target_date, tzinfo=location.tzinfo)

    phase_days = moon.phase(target_date)
    illumination_pct = (1 - math.cos(2 * math.pi * phase_days / LUNAR_CYCLE_DAYS)) / 2 * 100

    return MoonInfo(
        moon_illumination_pct=illumination_pct,
        sunrise=sun_times["sunrise"],
        sunset=sun_times["sunset"],
        is_dawn_dusk_window=True,
    )
