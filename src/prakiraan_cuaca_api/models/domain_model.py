from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel


@dataclass
class DatetimeModel:
    """
    Automatically fills non init attribute from current_datetime

    non init fields:
        current_datetime_start: datetime = replace current_datetime time to 00:00:00
        current_datetime_end: datetime = replace current_datetime time to 23:59:59
    """

    current_datetime: datetime
    current_datetime_start: datetime = field(init=False)
    current_datetime_end: datetime = field(init=False)

    def __post_init__(self) -> None:
        self.current_datetime = self.current_datetime.replace(tzinfo=None)
        self.current_datetime_start = self.current_datetime.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.current_datetime_end = self.current_datetime.replace(
            hour=23, minute=59, second=59, microsecond=0
        )

    def full_day(self) -> tuple[datetime, datetime]:
        """Return a tuple of self.current_datetime_start and self.current_datetime_end"""
        return (self.current_datetime_start, self.current_datetime_end)


class LocationModel(BaseModel):
    adm1: int
    adm2: int
    adm3: int
    adm4: int
    adm4_code: str  # native adm4 code
    provinsi: str
    kotkab: str
    kecamatan: str
    desa: str
    lon: float
    lat: float
    timezone: str


class ForecastModel(BaseModel):
    forecast_datetime: datetime  # datetime for the weather forecast
    analysis_datetime: datetime  # datetime for the forecast analysis
    adm4_code: str  # district level four code, the forecast location
    temperature: int  # temperature in celcius
    total_cloud_coverage: int | None  # percentage unit
    total_precipitation: float | None  # mm unit
    weather_description: str | None
    weather_description_eng: str | None
    wind_direction_degree: int | None
    wind_direction_compass: str | None  # direction from
    wind_direction_compass_to: str | None  # direction to
    wind_speed: float | None  # km/h unit
    humidity: int | None  # percentage
    visibility: int | None  # meters unit
