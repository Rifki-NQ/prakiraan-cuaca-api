import logging
from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import Any, Self

from sqlalchemy import (
    MetaData,
    Row,
    between,
    select,
)
from sqlalchemy.ext.asyncio import create_async_engine

from prakiraan_cuaca_api.exceptions import (
    DBNotInitializedError,
    EmptyQueryResultError,
    InvalidDatetimeRangeError,
)
from prakiraan_cuaca_api.models.contexts import ETLDBContext

logger = logging.getLogger(__name__)


class ETLQuery:
    def __init__(self, etl_db_url: str) -> None:
        self.etl_db_url = etl_db_url
        self._etl_db: ETLDBContext | None = None

    async def _setup_etl_db(self) -> None:
        """Should only be called in __aenter__() (as async context manager)"""
        if self._etl_db is not None:
            logger.warning("setup_etl_db() is already called")
            return
        engine = create_async_engine(self.etl_db_url, pool_pre_ping=True)
        try:
            metadata = MetaData()
            async with engine.begin() as conn:
                await conn.run_sync(metadata.reflect)
                await conn.run_sync(metadata.create_all)
        except BaseException:
            await engine.dispose()
            raise
        self._etl_db = ETLDBContext(
            engine=engine,
            location_table=metadata.tables["forecast_location"],
            forecast_table=metadata.tables["weather_forecast"],
        )
        logger.debug("setup_etl_db() executed")

    async def _close_etl_db(self) -> None:
        """Should only be called in __aexit__() (as async context manager)"""
        if self._etl_db is None:
            logger.warning("etl db is already closed")
            return
        try:
            await self._get_etl_db().engine.dispose()
        finally:
            self._etl_db = None
            logger.debug("etl db closed")

    async def __aenter__(self) -> Self:
        await self._setup_etl_db()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._close_etl_db()

    async def get_forecast_by_range(
        self,
        adm4_code: str,
        datetime_range: tuple[datetime, datetime],
        limit: int | None,
    ) -> Sequence[Row[Any]]:
        """
        Return a sequence of weather forecast rows if the range is valid,
        EmptyQueryResultError will be raised if the query returned empty rows.
        """
        start_dt, end_dt = datetime_range
        if start_dt > end_dt:
            raise InvalidDatetimeRangeError(start_dt, end_dt)
        db = self._get_etl_db()
        async with db.engine.connect() as conn:
            stmt = (
                select(db.forecast_table)
                .where(
                    db.forecast_table.c.adm4_code == adm4_code,
                    between(db.forecast_table.c.forecast_datetime, start_dt, end_dt),
                )
                .order_by(db.forecast_table.c.forecast_datetime)
                .limit(limit)
            )
            result = (await conn.execute(stmt)).all()
        if not result:
            raise EmptyQueryResultError(
                "Forecast not found",
                {
                    "adm4_code": adm4_code,
                    "start_dt": start_dt.strftime("%d-%m-%Y %H:%M:%S"),
                    "end_dt": end_dt.strftime("%d-%m-%Y %H:%M:%S"),
                },
            )
        return result

    async def get_forecast_location(self, adm4_code: str) -> Row[Any]:
        """
        Return forecast location based on the given adm4_code,
        raise error if there is more than one row result,
        because adm4_code is meant to be unique code.
        """
        db = self._get_etl_db()
        async with db.engine.connect() as conn:
            stmt = select(db.location_table).where(
                db.location_table.c.adm4_code == adm4_code
            )
            result = (await conn.execute(stmt)).one_or_none()
        if result is None:
            raise EmptyQueryResultError("Location not found", {"adm4_code": adm4_code})
        return result

    def _get_etl_db(self) -> ETLDBContext:
        """get the db attributes, can be called after setup_etl_db()."""
        if self._etl_db is None:
            raise DBNotInitializedError("setup_etl_db() has not called yet")
        return self._etl_db
