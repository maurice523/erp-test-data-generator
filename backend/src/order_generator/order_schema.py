"""Shared contract for extracted columns, analysis, and generated order output.

When the query output changes, update ``query.sql`` and this schema together.
Register each column with a ``FieldSpec``, then place generated fields in one
sampling group. Analysis and generation derive their behavior from these
definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FieldLevel = Literal["key", "order", "line"]
GeneratedLevel = Literal["order", "line"]
ValueKind = Literal["string", "integer", "boolean"]


@dataclass(frozen=True)
class FieldSpec:
    column: str
    level: FieldLevel
    output_path: tuple[str, ...] | None
    value_kind: ValueKind = "string"
    query_bind: bool = False
    required: bool = False
    default: object = None


@dataclass(frozen=True)
class SamplingGroupSpec:
    name: str
    level: GeneratedLevel
    target_fields: tuple[str, ...]
    conditioning_options: tuple[tuple[str, ...], ...] = ((),)


@dataclass(frozen=True)
class OutputDefaultSpec:
    level: GeneratedLevel
    output_path: tuple[str, ...]
    value: object


@dataclass(frozen=True)
class OrderSchema:
    order_key: str
    line_output_path: tuple[str, ...]
    fields: tuple[FieldSpec, ...]
    sampling_groups: tuple[SamplingGroupSpec, ...]
    output_defaults: tuple[OutputDefaultSpec, ...]

    @property
    def field_map(self) -> dict[str, FieldSpec]:
        return {field.column: field for field in self.fields}

    @property
    def expected_columns(self) -> frozenset[str]:
        return frozenset(self.field_map)

    @property
    def column_name_aliases(self) -> dict[str, str]:
        return {column.upper(): column for column in self.expected_columns}

    @property
    def query_bind_names(self) -> tuple[str, ...]:
        return tuple(field.column for field in self.fields if field.query_bind)

    def fields_at_level(self, level: FieldLevel) -> tuple[FieldSpec, ...]:
        return tuple(field for field in self.fields if field.level == level)

    def groups_at_level(
        self,
        level: GeneratedLevel,
    ) -> tuple[SamplingGroupSpec, ...]:
        return tuple(group for group in self.sampling_groups if group.level == level)


ORDER_SCHEMA = OrderSchema(
    order_key="orderNo",
    line_output_path=("lines",),
    fields=(
        FieldSpec(
            column="orderNo",
            level="key",
            output_path=None,
            query_bind=True,
            required=True,
        ),
        FieldSpec(
            column="customerNo",
            level="order",
            output_path=("customerNo",),
            required=True,
        ),
        FieldSpec(
            column="poNumber",
            level="order",
            output_path=("poNumber",),
            required=True,
        ),
        FieldSpec(
            column="externalRefNo",
            level="order",
            output_path=("externalRefNo",),
            default="",
        ),
        FieldSpec(
            column="id",
            level="order",
            output_path=("contact", "id"),
            value_kind="integer",
            required=True,
            default=0,
        ),
        FieldSpec(
            column="emailAddress",
            level="order",
            output_path=("contact", "emailAddress"),
            required=True,
        ),
        FieldSpec(
            column="shipViaCode",
            level="order",
            output_path=("shipViaCode",),
            query_bind=True,
            required=True,
        ),
        FieldSpec(
            column="address1",
            level="order",
            output_path=("shipToAddress", "address1"),
            required=True,
        ),
        FieldSpec(
            column="address2",
            level="order",
            output_path=("shipToAddress", "address2"),
            required=True,
        ),
        FieldSpec(
            column="address3",
            level="order",
            output_path=("shipToAddress", "address3"),
            default="",
        ),
        FieldSpec(
            column="address4",
            level="order",
            output_path=("shipToAddress", "address4"),
            default="",
        ),
        FieldSpec(
            column="city",
            level="order",
            output_path=("shipToAddress", "city"),
            required=True,
        ),
        FieldSpec(
            column="state",
            level="order",
            output_path=("shipToAddress", "state"),
            required=True,
        ),
        FieldSpec(
            column="zipCode",
            level="order",
            output_path=("shipToAddress", "zipCode"),
            required=True,
        ),
        FieldSpec(
            column="countryCode",
            level="order",
            output_path=("shipToAddress", "countryCode"),
            query_bind=True,
            required=True,
        ),
        FieldSpec(
            column="partNo",
            level="line",
            output_path=("partNo",),
            required=True,
        ),
        FieldSpec(
            column="quantity",
            level="line",
            output_path=("quantity",),
            value_kind="integer",
            default=1,
        ),
        FieldSpec(
            column="type",
            level="line",
            output_path=("configuration", "type"),
            query_bind=True,
            required=True,
        ),
        FieldSpec(
            column="proofRequested",
            level="line",
            output_path=("configuration", "proofRequested"),
            value_kind="boolean",
            default=False,
        ),
    ),
    sampling_groups=(
        SamplingGroupSpec(
            name="order_header",
            level="order",
            target_fields=(
                "customerNo",
                "poNumber",
                "externalRefNo",
                "id",
                "emailAddress",
                "address1",
                "address2",
                "address3",
                "address4",
                "city",
                "state",
                "zipCode",
                "countryCode",
            ),
        ),
        SamplingGroupSpec(
            name="shipping_method",
            level="order",
            target_fields=("shipViaCode",),
            conditioning_options=(("countryCode",), ()),
        ),
        SamplingGroupSpec(
            name="line_type",
            level="line",
            target_fields=("type",),
            conditioning_options=(("countryCode",), ()),
        ),
        SamplingGroupSpec(
            name="line_product",
            level="line",
            target_fields=("partNo",),
            conditioning_options=(
                ("countryCode", "type"),
                ("type",),
                ("countryCode",),
                (),
            ),
        ),
        SamplingGroupSpec(
            name="line_quantity",
            level="line",
            target_fields=("quantity",),
            conditioning_options=(
                ("countryCode", "type", "partNo"),
                ("type", "partNo"),
                ("partNo",),
                ("type",),
                ("countryCode",),
                (),
            ),
        ),
        SamplingGroupSpec(
            name="line_proof",
            level="line",
            target_fields=("proofRequested",),
            conditioning_options=(
                ("countryCode", "type", "partNo"),
                ("type", "partNo"),
                ("partNo",),
                ("type",),
                ("countryCode",),
                (),
            ),
        ),
    ),
    output_defaults=(
        OutputDefaultSpec(
            level="order",
            output_path=("attachments",),
            value=[],
        ),
        OutputDefaultSpec(
            level="line",
            output_path=("configuration", "allowShipEarly"),
            value=None,
        ),
        OutputDefaultSpec(
            level="line",
            output_path=("configuration", "decorations"),
            value=None,
        ),
        OutputDefaultSpec(
            level="line",
            output_path=("configuration", "locations"),
            value=[],
        ),
    ),
)
