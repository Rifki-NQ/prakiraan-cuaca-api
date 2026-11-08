import os
import zoneinfo

from dotenv import load_dotenv

from prakiraan_cuaca_api.exceptions import ConfigError

load_dotenv()


def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ConfigError(f"Missing required environment variable: {key}")
    elif not value:
        raise ConfigError(f"Required environment cannot be empty string: {key}")
    return value


def get_api_timezone() -> zoneinfo.ZoneInfo:
    api_timezone = get_required_env("API_TIMEZONE")
    try:
        return zoneinfo.ZoneInfo(api_timezone)
    except zoneinfo.ZoneInfoNotFoundError:
        raise ConfigError(f"Invalid API_TIMEZONE: {api_timezone}")


ETL_DATABASE_URL = get_required_env("ETL_DATABASE_URL")
API_TIMEZONE = get_api_timezone()
