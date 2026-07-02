from datetime import date
from unittest.mock import patch

from fishytime.config import WATERS
from fishytime.models import StreamflowReading
from fishytime.pipeline import run_pipeline


@patch("fishytime.pipeline.snowpack.get_snowpack", return_value=None)
@patch("fishytime.pipeline.stocking.get_recent_stocking", return_value=None)
@patch("fishytime.pipeline.weather_source.get_forecast", return_value=None)
@patch("fishytime.pipeline.usgs.get_streamflow", return_value=None)
def test_run_pipeline_degrades_gracefully_when_every_source_is_down(*_mocks):
    results = run_pipeline(date(2026, 7, 4))

    assert len(results) == len(WATERS)
    for result in results:
        assert result.caveats


@patch("fishytime.pipeline.snowpack.get_snowpack", return_value=None)
@patch("fishytime.pipeline.stocking.get_recent_stocking", return_value=None)
@patch("fishytime.pipeline.weather_source.get_forecast", return_value=None)
def test_run_pipeline_sorts_by_score_descending(_weather_mock, _stocking_mock, _snowpack_mock):
    def fake_streamflow(water):
        if water.name == "Clear Creek":
            return StreamflowReading(
                discharge_cfs=100, gage_height_ft=3, water_temp_c=14.4,
                flow_trend_pct_per_day=1, observed_at=None,
            )
        return None

    with patch("fishytime.pipeline.usgs.get_streamflow", side_effect=fake_streamflow):
        results = run_pipeline(date(2026, 7, 4))

    scores = [r.total_score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0].water_name == "Clear Creek"
