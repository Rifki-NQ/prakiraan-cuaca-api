import asyncio
import logging
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import Row

from prakiraan_cuaca_api.exceptions import AppError, EmptyQueryResultError
from prakiraan_cuaca_api.models.domain_model import DatetimeModel, ForecastModel

logger = logging.getLogger(__name__)


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


async def convert_forecasts(
    forecasts: Sequence[Row[Any]],
) -> list[ForecastModel]:
    """
    Convert all forecast rows into ForecastModel while
    appending it into a new list.
    """
    converted: list[ForecastModel] = []
    for forecast in forecasts:
        converted.append(ForecastModel.model_validate(forecast))
        # yield control to the event loop for each conversion
        await asyncio.sleep(0)
    return converted


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EmptyQueryResultError)
    async def empty_query_result_handler(
        request: Request, exc: EmptyQueryResultError
    ) -> JSONResponse:
        logger.debug(f"EmptyQueryResultError, detail: {exc!r}")
        return JSONResponse(
            status_code=404,
            content={
                "message": exc.message,
                "queries": {k: v for k, v in exc.query.items()},
            },
        )

    @app.exception_handler(AppError)
    async def unhandled_app_error_handler(
        request: Request, exc: AppError
    ) -> JSONResponse:
        logger.error(f"Unexpected app error, detail: {exc!r}", exc_info=exc)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"Unexpected error, detail: {exc!r}", exc_info=exc)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
