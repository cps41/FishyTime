from fishytime.config import WaterBody


def get_recent_stocking(water: WaterBody) -> bool | None:
    """Deferred to a later stage: CPW's stocking report is an HTML table with no API.

    Always returns None so score_conditions has a stable parameter slot to fill
    in once a scraper exists.
    """
    return None
