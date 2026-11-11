from dataclasses import dataclass
from datetime import datetime
from typing import Self

from pydantic import BaseModel, model_validator

from prakiraan_cuaca_api.config import ETL_DATABASE_URL
from prakiraan_cuaca_api.query import ETLQuery

# this should only creates the ETLQuery object once
# because python only runs a module once per process
etl_query = ETLQuery(ETL_DATABASE_URL)  # singleton


def get_etl_query() -> ETLQuery:
    """Get a shared instance of ETLQuery."""
    return etl_query


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
