from dataclasses import dataclass
from typing import Any

from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from prakiraan_cuaca_api.exceptions import DBNotInitializedError


@dataclass(frozen=True, slots=True)
class FakeETLDBContext:
    engine: AsyncEngine
    forecast_table: Table
    location_table: Table


class FakeETLQuery:
    def __init__(self) -> None:
        self._fake_etl_db: FakeETLDBContext | None = None

    async def setup_fake_etl_db(
        self, fake_etl_db_url: str, prod_etl_db_engine: AsyncEngine
    ) -> None:
        """
        Setup the fake etl db by copying the schema from the prod or original
        etl db into the fake etl database.
        """
        engine = create_async_engine(fake_etl_db_url, pool_pre_ping=True)
        try:
            metadata = MetaData()
            async with prod_etl_db_engine.connect() as conn:
                # this copy the prod db schema into the metadata object
                await conn.run_sync(metadata.reflect)
            async with engine.begin() as conn:
                # this creates the loaded prod db schema into the fake db
                await conn.run_sync(metadata.create_all)
        except BaseException:
            await engine.dispose()
            raise
        self._fake_etl_db = FakeETLDBContext(
            engine,
            metadata.tables["weather_forecast"],
            metadata.tables["forecast_location"],
        )

    async def seed_fake_forecast_table(self, mocked_data: list[dict[str, Any]]) -> None:
        db = self._get_fake_etl_db()
        async with db.engine.begin() as conn:
            stmt = insert(db.forecast_table).on_conflict_do_nothing()
            await conn.execute(stmt, mocked_data)

    async def seed_fake_location_table(self, mocked_data: dict[str, Any]) -> None:
        db = self._get_fake_etl_db()
        async with db.engine.begin() as conn:
            stmt = insert(db.location_table).values(mocked_data)
            await conn.execute(stmt)

    def _get_fake_etl_db(self) -> FakeETLDBContext:
        """get the db attributes, can be called after setup_fake_etl_db()."""
        if self._fake_etl_db is None:
            raise DBNotInitializedError("setup_fake_etl_db() has not called yet")
        return self._fake_etl_db
