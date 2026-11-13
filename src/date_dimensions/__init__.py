"""Date and time fields for analytics and Excel."""

from calendar import monthrange
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

__all__ = ["time_features", "time_features_excel"]

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def time_features(
    value: datetime | str | int | float,
    *,
    unit: str | None = None,
    include_cn_calendar: bool = False,
) -> dict[str, object]:
    """Return analytical fields in Asia/Shanghai local time.

    Numeric timestamps require unit="s" or unit="ms". Naive datetimes and
    strings without an offset are interpreted as Shanghai local time.
    """
    shanghai = ZoneInfo("Asia/Shanghai")
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        value = value.strip()
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        dt = datetime.fromisoformat(value)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if unit == "s":
            dt = _EPOCH + timedelta(seconds=value)
        elif unit == "ms":
            dt = _EPOCH + timedelta(milliseconds=value)
        else:
            raise ValueError("Numeric timestamps require unit='s' or unit='ms'")
    else:
        raise TypeError("Expected a numeric timestamp, ISO date/time string, or datetime")

    if dt.utcoffset() is None:
        dt = dt.replace(tzinfo=shanghai)
    dt = dt.astimezone(shanghai)

    date = dt.date()
    iso = date.isocalendar()
    weekday = date.weekday()
    is_weekend = weekday >= 5
    days_in_month = monthrange(dt.year, dt.month)[1]
    minutes = dt.hour * 60 + dt.minute
    seconds = minutes * 60 + dt.second
    hour_floor = dt.replace(minute=0, second=0, microsecond=0)

    result = {
        "dt": dt,
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "quarter": (dt.month - 1) // 3 + 1,
        "dayofweek": weekday,
        "day_name": _WEEKDAYS[weekday],
        "is_weekend": int(is_weekend),
        "iso_year": iso.year,
        "weekofyear": iso.week,
        "dayofyear": (date - date.replace(month=1, day=1)).days + 1,
        "date_only": date,
        "hour_floor": hour_floor,
        "15min_floor": hour_floor.replace(minute=dt.minute // 15 * 15),
        "week_start": date - timedelta(days=weekday),
        "month_start": date.replace(day=1),
        "seconds_of_day": seconds,
        "minutes_of_day": minutes,
        "day_progress": seconds / 86_400,
        "week_progress": (weekday * 86_400 + seconds) / (7 * 86_400),
        "is_month_start": int(dt.day == 1),
        "is_month_end": int(dt.day == days_in_month),
        "days_in_month": days_in_month,
        "days_to_month_end": days_in_month - dt.day,
        "month_progress": dt.day / days_in_month,
        "is_payday_zone": int(dt.day in (10, 15, 25)),
        "ten_day_period": ("上旬", "中旬", "下旬")[min((dt.day - 1) // 10, 2)],
        "is_holiday": None,
        "is_workday": None,
        "is_in_lieu": None,
        "is_makeup_workday": None,
        "holiday_name": None,
    }

    if include_cn_calendar:
        try:
            import chinese_calendar
        except ModuleNotFoundError as exc:
            if exc.name != "chinese_calendar":
                raise
            raise ModuleNotFoundError(
                "Install date-dimensions[cn] to enable the mainland China calendar"
            ) from exc

        is_holiday, holiday_name = chinese_calendar.get_holiday_detail(date)
        is_workday = not is_holiday
        result.update(
            is_holiday=int(is_holiday),
            is_workday=int(is_workday),
            is_in_lieu=int(chinese_calendar.is_in_lieu(date)),
            is_makeup_workday=int(is_weekend and is_workday),
            holiday_name=holiday_name if is_holiday else None,
        )

    return result


def time_features_excel(
    value: datetime | str | int | float,
    *,
    unit: str | None = None,
    include_cn_calendar: bool = False,
) -> dict[str, object]:
    """Return Excel-ready values, with 是/否 flags and naive local datetimes."""
    result = time_features(value, unit=unit, include_cn_calendar=include_cn_calendar)
    for field, field_value in result.items():
        if field.startswith("is_") and field_value is not None:
            result[field] = "是" if field_value else "否"
        elif isinstance(field_value, datetime):
            result[field] = field_value.replace(tzinfo=None)

    return result
