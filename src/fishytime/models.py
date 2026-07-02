from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class StreamflowReading:
    discharge_cfs: float | None
    gage_height_ft: float | None
    water_temp_c: float | None
    flow_trend_pct_per_day: float | None
    observed_at: datetime | None
    is_daily_only: bool = False


@dataclass
class WeatherReading:
    temp_f: float | None
    wind_speed_mph: float | None
    sky_cover_pct: float | None
    precip_probability_pct: float | None
    pressure_trend: Literal["rising", "falling", "steady", "unknown"]


@dataclass
class MoonInfo:
    moon_illumination_pct: float
    sunrise: datetime
    sunset: datetime
    is_dawn_dusk_window: bool


@dataclass
class FactorScore:
    name: str
    value: float
    weight: float
    reason: str
    missing: bool = False

    @property
    def contribution(self) -> float:
        return self.value * self.weight


@dataclass
class ScoreResult:
    water_name: str
    total_score: float
    factors: list[FactorScore] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)
