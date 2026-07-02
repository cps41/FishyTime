from datetime import date

from fishytime.data_sources import moon


def test_get_moon_info_returns_sane_values():
    info = moon.get_moon_info(39.753056, -105.234722, date(2026, 7, 2))

    assert 0.0 <= info.moon_illumination_pct <= 100.0
    assert info.sunrise < info.sunset
    assert info.is_dawn_dusk_window is True
