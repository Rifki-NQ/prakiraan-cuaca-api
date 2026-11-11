from dataclasses import dataclass, field
from datetime import datetime


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
