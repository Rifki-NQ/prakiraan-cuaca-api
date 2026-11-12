import logging
import os
import zoneinfo

from dotenv import load_dotenv

from prakiraan_cuaca_api.exceptions import ConfigError

logger = logging.getLogger(__name__)

load_dotenv()


APP_LOG_LEVEL = logging.INFO
GLOBAL_RATE_LIMIT = "30/minute"  # global rate limit configuration used by slowapi


def _get_api_timezone() -> zoneinfo.ZoneInfo:
    """
    Return the api timezone, when API_TIMEZONE is not provided in .env,
    it will return the default Asia/Jakarta timezone.
    """
    api_timezone = os.getenv("API_TIMEZONE") or "Asia/Jakarta"
    try:
        return zoneinfo.ZoneInfo(api_timezone)
    except zoneinfo.ZoneInfoNotFoundError:
        raise ConfigError(f"Invalid API_TIMEZONE: {api_timezone}")


# API_TIMEZONE is used as the API today and tomorrow reference
API_TIMEZONE = _get_api_timezone()


def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ConfigError(f"Missing required environment variable: {key}")
    elif not value:
        raise ConfigError(f"Required environment cannot be empty string: {key}")
    return value


ETL_DATABASE_URL = get_required_env("ETL_DATABASE_URL")
