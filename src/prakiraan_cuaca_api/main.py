import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from prakiraan_cuaca_api.config import API_TIMEZONE, APP_LOG_LEVEL
from prakiraan_cuaca_api.deps import etl_query
from prakiraan_cuaca_api.router import router
from prakiraan_cuaca_api.utils import register_exception_handlers

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    # create folder for logs if not exists
    LOGS_FOLDER = Path("logs")
    LOGS_FOLDER.mkdir(exist_ok=True)

    logging.basicConfig(
        level=APP_LOG_LEVEL,
        format="%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                filename=Path(LOGS_FOLDER / "bot_server.log"),
                maxBytes=10_000_000,
                backupCount=5,
                encoding="utf-8",
            ),
        ],
    )

    # supress loggers from dependencies
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)


@asynccontextmanager
async def app_setup_and_teardown(app: FastAPI) -> AsyncGenerator[None]:
    logger.info(f"Current API Timezone: {API_TIMEZONE}")
    async with etl_query:
        yield


setup_logging()
app = FastAPI(lifespan=app_setup_and_teardown)
app.include_router(router)
register_exception_handlers(app)


def main() -> None:
    # reload=True because the project is still in development
    # TODO: change reload to False when the project is finished
    uvicorn.run(
        "prakiraan_cuaca_api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
