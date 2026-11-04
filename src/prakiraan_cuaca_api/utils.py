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
    forecasts_iterable: AsyncIterable[Row[Any]],
) -> list[dict[str, str | int | float | datetime | None]]:
    """
    Return a list of forecast dicts from the forecasts_iterable.
    """
    return [f._asdict() async for f in forecasts_iterable]
