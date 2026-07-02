from fishytime.config import WaterBody


def get_snowpack(water: WaterBody) -> float | None:
    """Deferred to a later stage: value for summer Front Range trout is questionable.

    Always returns None so score_conditions has a stable parameter slot to fill
    in later if runoff-season scoring is added.
    """
    return None
