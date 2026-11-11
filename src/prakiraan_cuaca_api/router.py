from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request
from fastapi.openapi import docs
from fastapi.responses import HTMLResponse

from prakiraan_cuaca_api.config import API_TIMEZONE
from prakiraan_cuaca_api.deps import (
    DatetimeRangeQueryModel,
    ForecastParamsModel,
    get_etl_query,
)
from prakiraan_cuaca_api.models.domain_model import ForecastModel, LocationModel
from prakiraan_cuaca_api.models.protocols import ETLQueryProtocol
from prakiraan_cuaca_api.utils import merge_forecasts, setup_datetime

router = APIRouter()


Adm4CodeParam = Annotated[
    str, Path(pattern=r"^\d{2}\.\d{2}\.\d{2}\.\d{4}$", examples=["32.16.21.2003"])
]


def get_forecast_params(
    adm4_code: Adm4CodeParam,
    limit: Annotated[int, Query(gt=0)] | None = None,
) -> ForecastParamsModel:
    return ForecastParamsModel(adm4_code, limit)


EtlQuery = Annotated[ETLQueryProtocol, Depends(get_etl_query)]
ForecastParams = Annotated[ForecastParamsModel, Depends(get_forecast_params)]
DatetimeRangeQuery = Annotated[DatetimeRangeQueryModel, Query()]


@router.get("/")
@router.get("/documentation")
async def get_docs(request: Request) -> HTMLResponse:
    """Get auto generated documentation."""
    return docs.get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"{request.app.title} - Swagger UI",
    )


@router.get("/{adm4_code}")
async def get_forecast_location(
    etl_query: EtlQuery, adm4_code: Adm4CodeParam
) -> LocationModel:
    """
    Get forecast location information.

    Path Parameters:
        `adm4_code`: Indonesia's administrative area code,
                   down to the village level
    """
    return LocationModel.model_validate(
        (await etl_query.get_forecast_location(adm4_code))._asdict()
    )


@router.get("/{adm4_code}/today")
async def get_today_forecast(
    etl_query: EtlQuery, forecast_params: ForecastParams
) -> list[ForecastModel]:
    """
    Get today forecast, which based on the API_TIMEZONE value in project environment (.env).

    Path Parameters:
        `adm4_code`: Indonesia's administrative area code that defines
                   which village forecasts to get

    Query Parameters:
        `limit`: no limit by default, when it's given, the returned forecasts
               will be trimmed up to the given limit
    """
    forecasts_iterable = etl_query.get_forecast_by_range(
        forecast_params.adm4_code,
        setup_datetime(API_TIMEZONE).full_day(),
        forecast_params.limit,
    )
    return await merge_forecasts(forecasts_iterable)


@router.get("/{adm4_code}/tomorrow")
async def get_tomorrow_forecast(
    etl_query: EtlQuery, forecast_params: ForecastParams
) -> list[ForecastModel]:
    """
    Get tomorrow forecast, which based on the API_TIMEZONE value in project environment (.env).

    Path Parameters:
        `adm4_code`: Indonesia's administrative area code that defines
                   which village's weather forecast to get

    Query Parameters:
        `limit (optional)`: no limit by default, when it's given, the returned forecasts
                          will be trimmed up to the given limit
    """
    forecasts_iterable = etl_query.get_forecast_by_range(
        forecast_params.adm4_code,
        setup_datetime(API_TIMEZONE, timedelta(days=1)).full_day(),
        forecast_params.limit,
    )
    return await merge_forecasts(forecasts_iterable)


@router.get("/{adm4_code}/range")
async def get_forecast_range(
    etl_query: EtlQuery,
    forecast_params: ForecastParams,
    dt_range_query: DatetimeRangeQuery,
) -> list[ForecastModel]:
    """
    Get forecasts from start to end range,
    the start and end value can be either datetime or date type.

    Path Parameters:
        `adm4_code`: Indonesia's administrative area code that defines
                   which village's weather forecast to get

    Query Parameters:
        `start`: define the start range of the forecast, can be either datetime or date type
        `end`: define the end range of the forecast, can be either datetime or data type
        `limit (optional)`: no limit by default, when it's given, the returned forecasts
                          will be trimmed up to the given limit
    """
    forecasts_iterable = etl_query.get_forecast_by_range(
        forecast_params.adm4_code,
        (dt_range_query.start, dt_range_query.end),
        forecast_params.limit,
    )
    return await merge_forecasts(forecasts_iterable)
