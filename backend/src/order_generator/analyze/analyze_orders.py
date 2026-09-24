from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from order_generator.extract.extract_orders import OrderDataset
from order_generator.order_schema import (
    ORDER_SCHEMA,
    FieldSpec,
    OrderSchema,
)


@dataclass(frozen=True)
class DistributionSpec:
    target_fields: tuple[str, ...]
    given_fields: tuple[str, ...]


@dataclass(frozen=True)
class OrderProfile:
    schema: OrderSchema
    params: dict[str, object]
    frequencies: dict[str, pd.DataFrame]
    distributions: dict[DistributionSpec, pd.DataFrame]
    line_count_distribution: pd.DataFrame


@dataclass(frozen=True)
class OrderAnalysisResult:
    dataset: OrderDataset
    profile: OrderProfile


def frequency_table(dataframe: pd.DataFrame, field: str) -> pd.DataFrame:
    values = dataframe[field]
    counts = values.value_counts(dropna=False).rename("support_count")
    total_count = len(values)
    result = counts.reset_index()
    result.columns = [field, "support_count"]
    result["probability"] = (
        result["support_count"] / total_count if total_count else 0
    )
    return result


def unique_order_rows(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> pd.DataFrame:
    return merged.drop_duplicates(subset=[schema.order_key]).copy()


def validate_order_key(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> None:
    order_keys = merged[schema.order_key]
    if (
        order_keys.isna().any()
        or order_keys.astype("string").str.strip().eq("").any()
    ):
        raise ValueError(f"order key contains missing values: {schema.order_key}")


def validate_order_level_values(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> None:
    if merged.empty:
        return

    order_fields = [field.column for field in schema.fields_at_level("order")]
    grouped = merged.groupby(schema.order_key, dropna=False)
    inconsistent_fields = [
        field
        for field in order_fields
        if (grouped[field].nunique(dropna=False) > 1).any()
    ]
    if inconsistent_fields:
        raise ValueError(
            "fields declared as order-level vary within an order: "
            f"{', '.join(sorted(inconsistent_fields))}"
        )


def build_frequencies(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> dict[str, pd.DataFrame]:
    order_rows = unique_order_rows(merged, schema)
    frequencies: dict[str, pd.DataFrame] = {}
    for field in schema.fields:
        if field.level == "key":
            continue
        source = order_rows if field.level == "order" else merged
        frequencies[field.column] = frequency_table(source, field.column)
    return frequencies


def required_value_mask(
    dataframe: pd.DataFrame,
    field: FieldSpec,
) -> pd.Series:
    values = dataframe[field.column]
    mask = values.notna()
    if field.value_kind == "string":
        mask &= values.astype("string").str.strip().ne("")
    return mask


def filter_required_target_values(
    dataframe: pd.DataFrame,
    target_fields: tuple[str, ...],
    schema: OrderSchema = ORDER_SCHEMA,
) -> pd.DataFrame:
    filtered = dataframe
    for field_name in target_fields:
        field = schema.field_map[field_name]
        if field.required:
            filtered = filtered[required_value_mask(filtered, field)]
    return filtered


def probability_table(
    dataframe: pd.DataFrame,
    distribution: DistributionSpec,
) -> pd.DataFrame:
    fields = [*distribution.given_fields, *distribution.target_fields]
    working = dataframe[fields].copy()
    grouped = working.groupby(fields, dropna=False).size().reset_index(
        name="support_count"
    )

    if distribution.given_fields:
        grouped["given_count"] = grouped.groupby(
            list(distribution.given_fields),
            dropna=False,
        )["support_count"].transform("sum")
        grouped["probability"] = grouped["support_count"] / grouped["given_count"]
        sort_fields = [*distribution.given_fields, "support_count"]
        ascending = [True] * len(distribution.given_fields) + [False]
        return grouped.sort_values(sort_fields, ascending=ascending).reset_index(
            drop=True
        )

    total_count = grouped["support_count"].sum()
    grouped["probability"] = (
        grouped["support_count"] / total_count if total_count else 0
    )
    return grouped.sort_values("support_count", ascending=False).reset_index(
        drop=True
    )


def build_distributions(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> dict[DistributionSpec, pd.DataFrame]:
    order_rows = unique_order_rows(merged, schema)
    distributions: dict[DistributionSpec, pd.DataFrame] = {}
    for group in schema.sampling_groups:
        source = order_rows if group.level == "order" else merged
        source = filter_required_target_values(
            source,
            group.target_fields,
            schema,
        )
        for given_fields in group.conditioning_options:
            distribution = DistributionSpec(
                target_fields=group.target_fields,
                given_fields=given_fields,
            )
            distributions[distribution] = probability_table(source, distribution)
    return distributions


def build_line_count_distribution(
    merged: pd.DataFrame,
    schema: OrderSchema = ORDER_SCHEMA,
) -> pd.DataFrame:
    line_counts = (
        merged.groupby(schema.order_key, dropna=False).size().rename("line_count")
    )
    counts = line_counts.value_counts().sort_index().rename("support_count")
    total_orders = counts.sum()
    result = counts.reset_index()
    result.columns = ["line_count", "support_count"]
    result["probability"] = (
        result["support_count"] / total_orders if total_orders else 0
    )
    return result


def build_order_profile(
    dataset: OrderDataset,
    user_input_params: dict[str, object],
    *,
    schema: OrderSchema = ORDER_SCHEMA,
) -> OrderProfile:
    merged = dataset.merged
    validate_order_key(merged, schema)
    validate_order_level_values(merged, schema)

    profile_params = {
        field: value
        for field, value in user_input_params.items()
        if value != "" and field in schema.expected_columns
    }

    return OrderProfile(
        schema=schema,
        params=profile_params,
        frequencies=build_frequencies(merged, schema),
        distributions=build_distributions(merged, schema),
        line_count_distribution=build_line_count_distribution(merged, schema),
    )


def analyze_orders(
    dataset: OrderDataset,
    user_input_params: dict[str, object],
    *,
    schema: OrderSchema = ORDER_SCHEMA,
) -> OrderAnalysisResult:
    profile = build_order_profile(
        dataset,
        user_input_params=user_input_params,
        schema=schema,
    )
    return OrderAnalysisResult(dataset=dataset, profile=profile)
