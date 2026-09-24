from __future__ import annotations

from copy import deepcopy
from math import ceil
import random
from typing import Any

import pandas as pd

from order_generator.analyze.analyze_orders import (
    DistributionSpec,
    OrderAnalysisResult,
    OrderProfile,
)
from order_generator.generate.const import DEFAULT_ORDER_COUNT
from order_generator.order_schema import (
    GeneratedLevel,
    OrderSchema,
    SamplingGroupSpec,
)

def sample_weighted_row(dataframe: pd.DataFrame) -> pd.Series:
    weights = dataframe["probability"].tolist()
    selected_position = random.choices(range(len(dataframe)), weights=weights, k=1)[0]
    return dataframe.iloc[selected_position]


def sample_group(
    profile: OrderProfile,
    group: SamplingGroupSpec,
    context: dict[str, Any],
) -> dict[str, Any]:
    for given_fields in group.conditioning_options:
        distribution = DistributionSpec(
            target_fields=group.target_fields,
            given_fields=given_fields,
        )
        table = profile.distributions[distribution]
        if table.empty:
            continue

        candidates = table
        for field in given_fields:
            candidates = candidates[candidates[field] == context[field]]
        if candidates.empty:
            continue

        selected_row = sample_weighted_row(candidates)
        sampled_values = {
            field: selected_row[field] for field in group.target_fields
        }
        return sampled_values

    raise ValueError(
        f"cannot generate sampling group because no valid candidates exist: "
        f"{group.name}"
    )


def set_nested_value(
    output: dict[str, Any],
    path: tuple[str, ...],
    value: Any,
) -> None:
    current = output
    for part in path[:-1]:
        current = current.setdefault(part, {})
    current[path[-1]] = value


def apply_output_defaults(
    output: dict[str, Any],
    schema: OrderSchema,
    level: GeneratedLevel,
) -> None:
    for default in schema.output_defaults:
        if default.level == level:
            set_nested_value(
                output,
                default.output_path,
                deepcopy(default.value),
            )


def apply_sampled_values(
    output: dict[str, Any],
    sampled_values: dict[str, Any],
    schema: OrderSchema,
) -> None:
    for field_name, value in sampled_values.items():
        field = schema.field_map[field_name]
        if field.output_path is None:
            continue

        if pd.isna(value):
            value = deepcopy(field.default)
        elif field.value_kind == "integer":
            value = int(value)
        elif field.value_kind == "boolean":
            value = value == "Y"

        set_nested_value(
            output,
            field.output_path,
            value,
        )


def sample_line_count(
    profile: OrderProfile,
    min_lines: int | None = None,
) -> int:
    if min_lines is not None:
        return random.randint(min_lines, ceil(min_lines * 1.5))

    selected_row = sample_weighted_row(profile.line_count_distribution)
    return int(selected_row["line_count"])


def generate_line(
    *,
    profile: OrderProfile,
    order_context: dict[str, Any],
    quantity_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    schema = profile.schema
    line: dict[str, Any] = {}
    apply_output_defaults(line, schema, "line")
    context = dict(order_context)

    for group in schema.groups_at_level("line"):
        if group.target_fields == ("quantity",) and quantity_range is not None:
            sampled_values = {"quantity": random.randint(*quantity_range)}
        else:
            sampled_values = sample_group(profile, group, context)
        context.update(sampled_values)
        apply_sampled_values(line, sampled_values, schema)

    return line


def generate_order(
    profile: OrderProfile,
    *,
    min_lines: int | None = None,
    quantity_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    schema = profile.schema
    order: dict[str, Any] = {}
    apply_output_defaults(order, schema, "order")
    context: dict[str, Any] = {}

    for group in schema.groups_at_level("order"):
        sampled_values = sample_group(profile, group, context)
        context.update(sampled_values)
        apply_sampled_values(order, sampled_values, schema)

    lines = [
        generate_line(
            profile=profile,
            order_context=context,
            quantity_range=quantity_range,
        )
        for _ in range(sample_line_count(profile, min_lines))
    ]
    set_nested_value(order, schema.line_output_path, lines)
    return order


def generate_orders(
    analysis_result: OrderAnalysisResult,
    order_count: str,
    *,
    min_lines: str = "",
    min_quantity: str = "",
    max_quantity: str = "",
) -> list[dict[str, Any]]:
    number_of_orders = int(order_count or DEFAULT_ORDER_COUNT)
    minimum_lines = int(min_lines) if min_lines else None
    quantity_range = None
    if min_quantity or max_quantity:
        minimum_quantity = int(min_quantity or 0)
        maximum_quantity = (
            ceil(minimum_quantity * 1.5)
            if not max_quantity
            else int(max_quantity)
        )
        quantity_range = (minimum_quantity, maximum_quantity)

    return [
        generate_order(
            analysis_result.profile,
            min_lines=minimum_lines,
            quantity_range=quantity_range,
        )
        for _ in range(number_of_orders)
    ]
