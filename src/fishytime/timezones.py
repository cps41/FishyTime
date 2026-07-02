from zoneinfo import ZoneInfo

# All configured waters are in Colorado, so a single fixed local timezone
# is used to display times to a human. Everything stored internally
# (StreamflowReading.observed_at, MoonInfo.sunrise/sunset) is UTC.
LOCAL_TZ_NAME = "America/Denver"
LOCAL_TZ = ZoneInfo(LOCAL_TZ_NAME)
