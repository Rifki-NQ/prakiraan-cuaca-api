from collections.abc import AsyncGenerator, AsyncIterable
from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import Row, Table
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from prakiraan_cuaca_api.config import get_required_env
from prakiraan_cuaca_api.exceptions import (
    DBNotInitializedError,
    EmptyQueryResultError,
    InvalidDatetimeRangeError,
)
from prakiraan_cuaca_api.models.contexts import ETLDBContext
from prakiraan_cuaca_api.query import ETLQuery
from tests.infra.fake_data.fake_etl_data import (
    FAKE_ETL_DATA_INFO,
    FAKE_FORECAST_LOCATION_DATA,
    FAKE_WEATHER_FORECAST_DATA,
)
from tests.infra.fake_etl_query import FakeETLQuery
from tests.infra.utils import drop_all_tables, get_tables_name

pytestmark = pytest.mark.integration


load_dotenv()
etl_db_url = get_required_env("ETL_DATABASE_URL")
test_db_url = get_required_env("TEST_DATABASE_URL")


FAKE_ADM4_CODE = "fake_adm4_code"


@pytest.fixture
def etl_query() -> ETLQuery:
    """
    Return ETLQuery object with fake url, setup and close methods should
    be patched as mock object for testing purpose
    """
    return ETLQuery(etl_db_url="fake etl db url")


@pytest_asyncio.fixture
async def etl_engine() -> AsyncGenerator[AsyncEngine]:
    """Used only by seeded_etl_query() fixture"""
    etl_engine = create_async_engine(etl_db_url)
    yield etl_engine
    await etl_engine.dispose()


@pytest_asyncio.fixture
async def seeded_etl_query(etl_engine: AsyncEngine) -> AsyncGenerator[ETLQuery]:
    """
    Return an object of ETLQuery, with the internal function:
    _get_etl_db() patched with FakeETLQuery._get_fake_etl_db().

    The reason why ETLQuery._get_etl_db() gets patched is because
    FakeETLQuery uses it's own database, with the tables schema reflected from the production db
    and data seeded using predictable, hardcoded fake data.
    """
    etl_query = ETLQuery(etl_db_url=etl_db_url)
    fake_etl_query = FakeETLQuery()
    try:
        await fake_etl_query.setup_fake_etl_db(
            fake_etl_db_url=test_db_url, prod_etl_db_engine=etl_engine
        )
        # seed/fill the fake db with fake data
        await fake_etl_query.seed_fake_location_table(FAKE_FORECAST_LOCATION_DATA)
        await fake_etl_query.seed_fake_forecast_table(FAKE_WEATHER_FORECAST_DATA)
        with patch.object(
            etl_query, "_get_etl_db", return_value=fake_etl_query._get_fake_etl_db()
        ):
            yield etl_query
    finally:
        # drop all tables then dispose the fake_etl_query engine
        fake_etl_query_engine = fake_etl_query._get_fake_etl_db().engine
        await drop_all_tables(fake_etl_query_engine)
        await fake_etl_query_engine.dispose()


@pytest_asyncio.fixture
async def prod_etl_query() -> AsyncGenerator[ETLQuery]:
    """Yield an object of ETLQuery, connected with actual production database."""
    # warning: do not drop the tables
    # since this is production database!
    etl_query = ETLQuery(etl_db_url=etl_db_url)
    async with etl_query:
        yield etl_query


class TestAsAsyncContextManager:
    class FakeError(Exception):
        """Fake error exception for testing purpose"""

    async def test_setup_and_close_methods_called(self, etl_query: ETLQuery) -> None:
        with (
            patch.object(etl_query, "_setup_etl_db") as mock_setup_method,
            patch.object(etl_query, "_close_etl_db") as mock_close_method,
        ):
            async with etl_query:
                pass
        mock_setup_method.assert_awaited_once()
        mock_close_method.assert_awaited_once()

    async def test_close_method_called_when_error_raised(
        self, etl_query: ETLQuery
    ) -> None:
        with (
            patch.object(etl_query, "_setup_etl_db"),
            patch.object(etl_query, "_close_etl_db") as mock_close_method,
            pytest.raises(self.FakeError),
        ):
            async with etl_query:
                raise self.FakeError()
        mock_close_method.assert_awaited_once()


class TestGetForecastByRange:
    async def test_returned_type_and_total_rows(
        self,
        seeded_etl_query: ETLQuery,
    ) -> None:
        """
        Test that get_forecast_by_range() method return AsyncIterable,
        with total rows of 24, based on the given dt_range
        """
        dt_range = (
            FAKE_ETL_DATA_INFO["oldest_forecast_datetime"],
            FAKE_ETL_DATA_INFO["newest_forecast_datetime"],
        )
        results = seeded_etl_query.get_forecast_by_range(
            adm4_code=FAKE_ETL_DATA_INFO["adm4_code"],
            datetime_range=dt_range,
            limit=None,
        )
        assert isinstance(results, AsyncIterable)
        assert len([r async for r in results]) == 24

    async def test_first_row_value(
        self,
        seeded_etl_query: ETLQuery,
    ) -> None:
        dt_range = (
            # only query the first row
            FAKE_ETL_DATA_INFO["oldest_forecast_datetime"],
            FAKE_ETL_DATA_INFO["oldest_forecast_datetime"],
        )
        results = [
            r
            async for r in seeded_etl_query.get_forecast_by_range(
                adm4_code=FAKE_ETL_DATA_INFO["adm4_code"],
                datetime_range=dt_range,
                limit=None,
            )
        ]
        assert len(results) == 1, "results should only return 1 row of forecast data!"
        # this should be True, since the seeded data comes from FAKE_WEATHER_FORECAST_DATA
        assert results[0]._asdict() == FAKE_WEATHER_FORECAST_DATA[0]

    async def test_empty_result_error(
        self,
        seeded_etl_query: ETLQuery,
    ) -> None:
        dt_range = (
            # deliberately a range with no matching weather forecast,
            # i.e. no forecast_datetime falls between these two dates
            # in the mocked_data
            datetime(2026, 8, 10, 0, 0, 0),
            datetime(2026, 8, 11, 0, 0, 0),
        )
        # this does not raises EmptyQueryResultError
        # since this return only the AsyncIterable object
        results = seeded_etl_query.get_forecast_by_range(
            adm4_code=FAKE_ADM4_CODE, datetime_range=dt_range, limit=None
        )
        with pytest.raises(EmptyQueryResultError) as exc_info:
            # this raises because the AsyncIterable is iterated or consumed
            [r async for r in results]
        assert exc_info.value.query.get("adm4_code") == FAKE_ADM4_CODE
        assert exc_info.value.query.get("start_dt") == dt_range[0].strftime(
            "%d-%m-%Y %H:%M:%S"
        )
        assert exc_info.value.query.get("end_dt") == dt_range[1].strftime(
            "%d-%m-%Y %H:%M:%S"
        )

    @pytest.mark.parametrize(
        "limit, expected_total_rows",
        [
            (None, 24),  # when limit == None, all rows are returned
            (2, 2),
        ],
    )
    async def test_limit_param(
        self, seeded_etl_query: ETLQuery, limit: int | None, expected_total_rows: int
    ) -> None:
        """
        Test if the returned rows is trimmed when limit != None.
        """
        dt_range = (
            FAKE_ETL_DATA_INFO["oldest_forecast_datetime"],
            FAKE_ETL_DATA_INFO["newest_forecast_datetime"],
        )
        results = seeded_etl_query.get_forecast_by_range(
            adm4_code=FAKE_ETL_DATA_INFO["adm4_code"],
            datetime_range=dt_range,
            limit=limit,
        )
        assert len([r async for r in results]) == expected_total_rows


class TestGetForecastLocation:
    async def test_returned_type_and_value(self, seeded_etl_query: ETLQuery) -> None:
        result = await seeded_etl_query.get_forecast_location(
            adm4_code=FAKE_ETL_DATA_INFO["adm4_code"]
        )
        assert isinstance(result, Row)
        assert result._asdict() == FAKE_FORECAST_LOCATION_DATA

    async def test_empty_result_error(self, seeded_etl_query: ETLQuery) -> None:
        with pytest.raises(EmptyQueryResultError) as exec_info:
            await seeded_etl_query.get_forecast_location(adm4_code=FAKE_ADM4_CODE)
        assert exec_info.value.query["adm4_code"] == FAKE_ADM4_CODE


@pytest.mark.parametrize(
    "start_dt", [datetime(2020, 2, 2, 1, 1, 1), datetime(2020, 2, 3)]
)
async def test_invalid_datetime_range(start_dt: datetime) -> None:
    """InvalidDatetimeRangeError should be raised when start_dt is greater than end_dt"""
    end_dt = datetime(2020, 2, 2)
    etl_query = ETLQuery(etl_db_url=etl_db_url)
    datetime_range = (start_dt, end_dt)
    with pytest.raises(InvalidDatetimeRangeError) as exc_info:
        etl_query.get_forecast_by_range(
            adm4_code="fake adm4_code", datetime_range=datetime_range, limit=None
        )
    assert exc_info.value.start_dt == start_dt
    assert exc_info.value.end_dt == end_dt


def test_get_etl_db_before_setup_etl_db() -> None:
    etl_query = ETLQuery(etl_db_url=etl_db_url)
    with pytest.raises(DBNotInitializedError):
        etl_query._get_etl_db()


@pytest.mark.prod_db
def test_db_attributes_after_setup_etl_db(prod_etl_query: ETLQuery) -> None:
    db = prod_etl_query._get_etl_db()
    assert db is not None
    assert isinstance(db, ETLDBContext)
    assert isinstance(db.engine, AsyncEngine)
    assert isinstance(db.location_table, Table)
    assert isinstance(db.forecast_table, Table)
    assert db.location_table.name == "forecast_location"
    assert db.forecast_table.name == "weather_forecast"


@pytest.mark.prod_db
async def test_setup_etl_db_create_tables_in_db(prod_etl_query: ETLQuery) -> None:
    db = prod_etl_query._get_etl_db()
    table_names_from_db = await get_tables_name(db.engine)
    assert db.location_table.name in table_names_from_db
    assert db.forecast_table.name in table_names_from_db
