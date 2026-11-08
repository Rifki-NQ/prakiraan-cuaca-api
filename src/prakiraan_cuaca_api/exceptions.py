from datetime import datetime


class AppError(Exception):
    pass


class QueryError(AppError):
    pass


class ConfigError(RuntimeError):
    """Misconfigured environment. Not recoverable at runtime."""


class InvalidDatetimeRangeError(QueryError):
    """Raised when the start datetime is greater than the end datetime"""

    def __init__(self, start_dt: datetime, end_dt: datetime) -> None:
        self.start_dt = start_dt
        self.end_dt = end_dt
        super().__init__(
            f"Error: start_dt ({start_dt}) cannot be greater than end_dt ({end_dt})"
        )


class EmptyQueryResultError(QueryError):
    """Raised when the query return zero result"""

    def __init__(self, message: str, query: dict[str, str]) -> None:
        self.message = message
        self.query = query
        super().__init__(message)


class DBNotInitializedError(QueryError):
    """Raised when the setup_db() has not called"""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Error: {message}")
