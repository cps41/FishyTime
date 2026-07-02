from dataclasses import dataclass


@dataclass(frozen=True)
class WaterBody:
    name: str
    usgs_site_id: str | None
    lat: float
    lon: float
    notes: str


WATERS: list[WaterBody] = [
    WaterBody(
        name="South Platte River (Cheesman Canyon / Deckers)",
        usgs_site_id="06701900",
        lat=39.259990,
        lon=-105.221938,
        notes="Gauge is daily-values only, no continuous feed and no water temp sensor.",
    ),
    WaterBody(
        name="Clear Creek",
        usgs_site_id="06719505",
        lat=39.753056,
        lon=-105.234722,
        notes="Continuous discharge and gage height available.",
    ),
    WaterBody(
        name="Boulder Creek",
        usgs_site_id="06727000",
        lat=40.006375,
        lon=-105.330825,
        notes="Gauge is at Orodell (canyon mouth), the actual trout water.",
    ),
    WaterBody(
        name="Chatfield Reservoir",
        usgs_site_id=None,
        lat=39.5486,
        lon=-105.0653,
        notes="No usable USGS gauge exists for this water; streamflow always unavailable.",
    ),
    WaterBody(
        name="Cherry Creek Reservoir",
        usgs_site_id="06713000",
        lat=39.653611,
        lon=-104.862500,
        notes="Gauge is below the dam (outflow), used as a reservoir proxy signal.",
    ),
]
