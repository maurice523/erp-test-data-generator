import os
from dataclasses import dataclass
import pandas as pd
import psycopg
from dotenv import load_dotenv, find_dotenv
from order_generator.extract.const import SQL_BLOCK
from order_generator.order_schema import ORDER_SCHEMA


load_dotenv(find_dotenv())


@dataclass(frozen=True)
class OrderDataset:
    merged: pd.DataFrame


QUERY_INPUT_BIND_NAMES = ORDER_SCHEMA.query_bind_names
COLUMN_NAME_ALIASES = ORDER_SCHEMA.column_name_aliases


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in the environment or .env file.")
    return database_url


def build_bind_params(
    user_input_params: dict[str, object],
) -> dict[str, object]:
    return {
        bind_name: blank_to_none(user_input_params[bind_name])
        for bind_name in QUERY_INPUT_BIND_NAMES
    }


def blank_to_none(value: object) -> object:
    """Omitted request fields arrive as "". Postgres keeps '' distinct from
    NULL, so blanks become NULL to switch the filter off."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def cursor_to_dataframe(query_cursor: psycopg.Cursor) -> pd.DataFrame:
    columns = [normalize_column_name(column[0]) for column in query_cursor.description]
    rows = query_cursor.fetchall()
    return pd.DataFrame.from_records(rows, columns=columns)


def normalize_column_name(column_name: str) -> str:
    return COLUMN_NAME_ALIASES.get(column_name.upper(), column_name)


def fetch_order_data(
    user_input_params: dict[str, object],
) -> tuple[OrderDataset, dict[str, object]]:
    with psycopg.connect(get_database_url()) as connection:

        with connection.cursor() as cursor:
            bind_params = build_bind_params(user_input_params)

            cursor.execute(SQL_BLOCK, bind_params)
            merged = cursor_to_dataframe(cursor)

    dataset = OrderDataset(merged=merged)

    return dataset, user_input_params
