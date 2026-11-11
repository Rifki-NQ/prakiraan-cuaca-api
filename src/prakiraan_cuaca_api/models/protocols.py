from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import Any, Protocol, Self

from sqlalchemy import Row


class ETLQueryProtocol(Protocol):
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...
    async def get_forecast_by_range(
        self,
        adm4_code: str,
        datetime_range: tuple[datetime, datetime],
        limit: int | None,
    ) -> Sequence[Row[Any]]: ...
    async def get_forecast_location(self, adm4_code: str) -> Row[Any]: ...
