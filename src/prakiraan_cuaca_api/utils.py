from collections.abc import AsyncIterable
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import Row

from prakiraan_cuaca_api.models.data_models import DatetimeModel


def setup_datetime(
    timezone: ZoneInfo, timedelta: timedelta | None = None
) -> DatetimeModel:
    """
    Return DatetimeModel with datetime.now(),
    add datetime.now() with timedelta if not None.
    """
    if timedelta is None:
        return DatetimeModel(datetime.now(tz=timezone))
    return DatetimeModel(datetime.now(tz=timezone) + timedelta)


async def merge_forecasts(
    forecasts_iterable: AsyncIterable[Row[Any]], limit: int
) -> list[dict[str, str | int | float | datetime | None]]:
    """
    Iterate over the forecasts_iterable, append it to a list then return
    the list after either the iterable is exhausted
    or when the limit reaches 0.
    """
    merged: list[dict[str, str | int | float | datetime | None]] = []
    async for forecast in forecasts_iterable:
        if limit == 0:
            break
        merged.append(forecast._asdict())
        limit -= 1
    return merged
