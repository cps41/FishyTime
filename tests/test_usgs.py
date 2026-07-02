import responses

from fishytime.config import WaterBody
from fishytime.data_sources import usgs
from tests.util import load_fixture

BASE = usgs.BASE_URL


@responses.activate
def test_get_streamflow_continuous():
    water = WaterBody(name="Clear Creek", usgs_site_id="06719505", lat=39.753056, lon=-105.234722, notes="")
    responses.add(responses.GET, f"{BASE}/latest-continuous/items", json=load_fixture("usgs_latest_continuous"))
    responses.add(responses.GET, f"{BASE}/continuous/items", json=load_fixture("usgs_continuous_history"))

    reading = usgs.get_streamflow(water)

    assert reading is not None
    assert reading.discharge_cfs == 130
    assert reading.gage_height_ft == 4.10
    assert reading.water_temp_c is None
    assert reading.is_daily_only is False
    assert reading.flow_trend_pct_per_day == 15.0


@responses.activate
def test_get_streamflow_falls_back_to_daily():
    water = WaterBody(name="South Platte", usgs_site_id="06701900", lat=39.259990, lon=-105.221938, notes="")
    responses.add(responses.GET, f"{BASE}/latest-continuous/items", json=load_fixture("usgs_empty"))
    responses.add(responses.GET, f"{BASE}/latest-daily/items", json=load_fixture("usgs_latest_daily"))

    reading = usgs.get_streamflow(water)

    assert reading is not None
    assert reading.discharge_cfs == 255
    assert reading.is_daily_only is True
    assert reading.flow_trend_pct_per_day is None


def test_get_streamflow_no_gauge_returns_none():
    water = WaterBody(name="Chatfield Reservoir", usgs_site_id=None, lat=39.5486, lon=-105.0653, notes="")

    assert usgs.get_streamflow(water) is None


@responses.activate
def test_get_streamflow_request_failure_returns_none():
    water = WaterBody(name="Clear Creek", usgs_site_id="06719505", lat=39.753056, lon=-105.234722, notes="")
    # No responses registered -> requests raises ConnectionError, which _get_items must swallow.

    assert usgs.get_streamflow(water) is None
