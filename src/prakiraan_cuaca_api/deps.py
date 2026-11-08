"""
Creates then stores objects that is meant to be singleton,
because python only run a module once per process.
"""

from prakiraan_cuaca_api.config import ETL_DATABASE_URL
from prakiraan_cuaca_api.query import ETLQuery

etl_query = ETLQuery(ETL_DATABASE_URL)
