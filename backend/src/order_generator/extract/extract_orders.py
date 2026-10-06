import re
from dataclasses import dataclass
import pandas as pd
from order_generator import d1
from order_generator.extract.const import SQL_BLOCK
from order_generator.order_schema import ORDER_SCHEMA


@dataclass(frozen=True)
class OrderDataset:
    merged: pd.DataFrame


QUERY_INPUT_BIND_NAMES = ORDER_SCHEMA.query_bind_names
COLUMN_NAME_ALIASES = ORDER_SCHEMA.column_name_aliases

NAMED_PARAM = re.compile(r":([A-Za-z_]\w*)")


def to_positional(sql: str, bind_names: tuple[str, ...]) -> str:
    """D1 accepts only ``?N`` parameters, so ``:name`` in query.sql becomes
    ``?N``, where N is the name's 1-based position in ``bind_names``."""
    positions = {name: index for index, name in enumerate(bind_names, start=1)}

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in positions:
            raise KeyError(f"query.sql uses :{name}, which is not a query bind name.")
        return f"?{positions[name]}"

    return NAMED_PARAM.sub(replace, sql)


POSITIONAL_SQL = to_positional(SQL_BLOCK, QUERY_INPUT_BIND_NAMES)


def build_bind_params(
    user_input_params: dict[str, object],
) -> list[object]:
    return [
        blank_to_none(user_input_params[bind_name])
        for bind_name in QUERY_INPUT_BIND_NAMES
    ]


def blank_to_none(value: object) -> object:
    """Omitted request fields arrive as "". SQL keeps '' distinct from NULL,
    so blanks become NULL to switch the filter off."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def result_to_dataframe(result: d1.Result) -> pd.DataFrame:
    columns = [normalize_column_name(column) for column in result.columns]
    return pd.DataFrame.from_records(result.rows, columns=columns)


def normalize_column_name(column_name: str) -> str:
    return COLUMN_NAME_ALIASES.get(column_name.upper(), column_name)


def fetch_order_data(
    user_input_params: dict[str, object],
) -> tuple[OrderDataset, dict[str, object]]:
    bind_params = build_bind_params(user_input_params)
    merged = result_to_dataframe(d1.query(POSITIONAL_SQL, bind_params))

    dataset = OrderDataset(merged=merged)

    return dataset, user_input_params
