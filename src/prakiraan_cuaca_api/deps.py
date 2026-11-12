from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Self

from fastapi import Depends, Path, Query
from pydantic import BaseModel, model_validator

from prakiraan_cuaca_api.config import ETL_DATABASE_URL
from prakiraan_cuaca_api.models.protocols import ETLQueryProtocol
from prakiraan_cuaca_api.query import ETLQuery

# this should only creates the ETLQuery object once
# because python only runs a module once per process
etl_query = ETLQuery(ETL_DATABASE_URL)  # singleton


def get_etl_query() -> ETLQuery:
    """Get a shared instance of ETLQuery."""
    return etl_query


def get_forecast_params(
    adm4_code: Adm4CodeParam,
    limit: Annotated[int, Query(gt=0)] | None = None,
) -> ForecastParamsModel:
    return ForecastParamsModel(adm4_code, limit)


@dataclass(frozen=True, slots=True)
class ForecastParamsModel:
    adm4_code: str
    limit: int | None


class DatetimeRangeQueryModel(BaseModel):
    model_config = {"extra": "forbid"}

    start: datetime
    end: datetime

    @model_validator(mode="after")
    def end_must_be_grater_or_equal_to_start(self) -> Self:
        if self.start > self.end:
            raise ValueError("end must be grater or equal to start")
        return self


Adm4CodeParam = Annotated[
    str, Path(pattern=r"^\d{2}\.\d{2}\.\d{2}\.\d{4}$", examples=["32.16.21.2003"])
]
EtlQuery = Annotated[ETLQueryProtocol, Depends(get_etl_query)]
ForecastParams = Annotated[ForecastParamsModel, Depends(get_forecast_params)]
DatetimeRangeQuery = Annotated[DatetimeRangeQueryModel, Query()]
