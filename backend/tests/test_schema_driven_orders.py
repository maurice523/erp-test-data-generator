from dataclasses import replace
import random
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd

from order_generator.analyze.analyze_orders import analyze_orders
from order_generator.extract.const import SQL_BLOCK
from order_generator.extract.extract_orders import (
    QUERY_INPUT_BIND_NAMES,
    OrderDataset,
)
from order_generator.generate.generate_orders import (
    generate_orders,
)
from order_generator.order_schema import (
    ORDER_SCHEMA,
    FieldSpec,
)
from order_generator.request.request_parse import (
    GenerateOrdersRequest,
    request_to_query_params,
)


def sample_dataframe() -> pd.DataFrame:
    rows = [
        {
            "orderNo": "O1",
            "customerNo": "C1",
            "poNumber": "PO-C1",
            "externalRefNo": "EXT-C1",
            "id": "101",
            "emailAddress": "one@example.com",
            "shipViaCode": "UPS",
            "address1": "Customer One",
            "address2": "1 Main Street",
            "address3": None,
            "address4": None,
            "city": "Boston",
            "state": "MA",
            "zipCode": "02108",
            "countryCode": "US",
            "partNo": "PART-A",
            "quantity": 2,
            "type": "STANDARD",
            "proofRequested": "N",
        },
        {
            "orderNo": "O1",
            "customerNo": "C1",
            "poNumber": "PO-C1",
            "externalRefNo": "EXT-C1",
            "id": "101",
            "emailAddress": "one@example.com",
            "shipViaCode": "UPS",
            "address1": "Customer One",
            "address2": "1 Main Street",
            "address3": None,
            "address4": None,
            "city": "Boston",
            "state": "MA",
            "zipCode": "02108",
            "countryCode": "US",
            "partNo": "PART-B",
            "quantity": 4,
            "type": "STANDARD",
            "proofRequested": "Y",
        },
        {
            "orderNo": "O2",
            "customerNo": "C2",
            "poNumber": "PO-C2",
            "externalRefNo": "EXT-C2",
            "id": "202",
            "emailAddress": "two@example.com",
            "shipViaCode": "FEDEX",
            "address1": "Customer Two",
            "address2": "2 King Street",
            "address3": None,
            "address4": None,
            "city": "Toronto",
            "state": "ON",
            "zipCode": "M5H 2N2",
            "countryCode": "CA",
            "partNo": "PART-C",
            "quantity": 3,
            "type": "CUSTOM",
            "proofRequested": "N",
        },
    ]
    return pd.DataFrame(rows, columns=[field.column for field in ORDER_SCHEMA.fields])


class SqlResourceTests(unittest.TestCase):
    def test_llm_request_uses_empty_strings_for_omitted_fields(self) -> None:
        request = GenerateOrdersRequest()

        self.assertTrue(
            all(value == "" for value in request.model_dump().values())
        )

    def test_sql_resource_is_loaded_for_d1_execution(self) -> None:
        self.assertTrue(SQL_BLOCK.startswith("WITH"))
        self.assertFalse(SQL_BLOCK.endswith(";"))
        self.assertIn(":shipViaCode", SQL_BLOCK)

    def test_quantity_is_not_an_extraction_parameter(self) -> None:
        request = GenerateOrdersRequest(
            shipViaCode="UPS-GND",
            orderNo="",
            type="SAMPLE",
            countryCode="US",
            minQuantity="9",
            maxQuantity="12",
            orderCount="1",
            minLines="2",
        )

        self.assertNotIn("quantity", request_to_query_params(request))
        self.assertNotIn("minQuantity", request_to_query_params(request))
        self.assertNotIn("maxQuantity", request_to_query_params(request))
        self.assertNotIn("quantity", QUERY_INPUT_BIND_NAMES)
        self.assertNotIn(":quantity", SQL_BLOCK)


class SchemaDrivenGenerationTests(unittest.TestCase):
    def test_header_relationships_and_line_conditions_are_preserved(self) -> None:
        dataframe = sample_dataframe()
        analysis = analyze_orders(OrderDataset(merged=dataframe), {})
        random.seed(7)

        orders = generate_orders(analysis, "4")

        expected_headers = {
            (
                row.customerNo,
                row.poNumber,
                row.externalRefNo,
                int(row.id),
                row.emailAddress,
                row.address1,
                row.address2,
                row.city,
                row.state,
                row.zipCode,
                row.countryCode,
            )
            for row in dataframe.drop_duplicates("orderNo").itertuples()
        }
        valid_shipping = {
            (row.countryCode, row.shipViaCode)
            for row in dataframe.drop_duplicates("orderNo").itertuples()
        }
        valid_products = {
            (row.countryCode, row.type, row.partNo)
            for row in dataframe.itertuples()
        }

        for order in orders:
            address = order["shipToAddress"]
            header = (
                order["customerNo"],
                order["poNumber"],
                order["externalRefNo"],
                order["contact"]["id"],
                order["contact"]["emailAddress"],
                address["address1"],
                address["address2"],
                address["city"],
                address["state"],
                address["zipCode"],
                address["countryCode"],
            )
            self.assertIn(header, expected_headers)
            self.assertIn(
                (address["countryCode"], order["shipViaCode"]),
                valid_shipping,
            )
            for line in order["lines"]:
                self.assertIn(
                    (
                        address["countryCode"],
                        line["configuration"]["type"],
                        line["partNo"],
                    ),
                    valid_products,
                )

    def test_required_values_are_filtered_before_generation(self) -> None:
        dataframe = sample_dataframe()
        dataframe["emailAddress"] = None
        analysis = analyze_orders(OrderDataset(merged=dataframe), {})

        with self.assertRaisesRegex(ValueError, "order_header"):
            generate_orders(analysis, "1")

    def test_min_lines_uses_an_inclusive_derived_range(self) -> None:
        dataframe = sample_dataframe()
        analysis = analyze_orders(OrderDataset(merged=dataframe), {})
        random.seed(11)

        orders = generate_orders(analysis, "3", min_lines="5")

        self.assertTrue(
            all(5 <= len(order["lines"]) <= 8 for order in orders)
        )

    def test_quantity_range_applies_to_every_generated_line(self) -> None:
        dataframe = sample_dataframe()
        analysis = analyze_orders(OrderDataset(merged=dataframe), {})
        random.seed(13)

        orders = generate_orders(
            analysis,
            "3",
            min_quantity="9",
            max_quantity="12",
        )

        self.assertTrue(
            all(
                9 <= line["quantity"] <= 12
                for order in orders
                for line in order["lines"]
            )
        )

    def test_quantity_bounds_use_inclusive_defaults(self) -> None:
        cases = (
            ("3", "5", (3, 5)),
            ("3", "", (3, 5)),
            ("", "5", (0, 5)),
        )
        for min_quantity, max_quantity, expected_range in cases:
            with self.subTest(
                min_quantity=min_quantity,
                max_quantity=max_quantity,
            ):
                with patch(
                    "order_generator.generate.generate_orders.random.randint",
                    side_effect=lambda minimum, _maximum: minimum,
                ) as randint:
                    order = generate_orders(
                        analyze_orders(
                            OrderDataset(merged=sample_dataframe()),
                            {},
                        ),
                        "1",
                        min_lines="1",
                        min_quantity=min_quantity,
                        max_quantity=max_quantity,
                    )[0]

                self.assertEqual(
                    order["lines"][0]["quantity"],
                    expected_range[0],
                )
                randint.assert_any_call(*expected_range)

    def test_sql_values_are_converted_only_for_output_types(self) -> None:
        analysis = analyze_orders(
            OrderDataset(merged=sample_dataframe()),
            {},
        )
        random.seed(17)

        order = generate_orders(analysis, "1")[0]

        self.assertIsInstance(order["contact"]["id"], int)
        self.assertIsInstance(order["lines"][0]["quantity"], int)
        self.assertIsInstance(
            order["lines"][0]["configuration"]["proofRequested"],
            bool,
        )

    def test_order_level_fields_must_be_stable_per_order(self) -> None:
        dataframe = sample_dataframe()
        dataframe.loc[1, "city"] = "Cambridge"

        with self.assertRaisesRegex(ValueError, "city"):
            analyze_orders(OrderDataset(merged=dataframe), {})

    def test_registered_field_flows_through_analysis_and_generation(self) -> None:
        new_field = FieldSpec(
            column="salesRegion",
            level="order",
            output_path=("salesRegion",),
            required=True,
        )
        header_group = replace(
            ORDER_SCHEMA.sampling_groups[0],
            target_fields=(
                *ORDER_SCHEMA.sampling_groups[0].target_fields,
                "salesRegion",
            ),
        )
        schema = replace(
            ORDER_SCHEMA,
            fields=(*ORDER_SCHEMA.fields, new_field),
            sampling_groups=(
                header_group,
                *ORDER_SCHEMA.sampling_groups[1:],
            ),
        )

        dataframe = sample_dataframe()
        dataframe["salesRegion"] = dataframe["countryCode"].map(
            {"US": "EAST", "CA": "NORTH"}
        )
        analysis = analyze_orders(
            OrderDataset(merged=dataframe),
            {},
            schema=schema,
        )
        random.seed(3)
        order = generate_orders(analysis, "1")[0]

        self.assertIn("salesRegion", analysis.profile.frequencies)
        self.assertIn(order["salesRegion"], {"EAST", "NORTH"})

    def test_duplicate_candidates_are_allowed(self) -> None:
        sampled_order = {"customerNo": "C1", "lines": []}
        analysis = SimpleNamespace(profile=object())

        with patch(
            "order_generator.generate.generate_orders.generate_order",
            return_value=sampled_order,
        ) as generate_order:
            orders = generate_orders(analysis, "2")

        self.assertEqual(orders, [sampled_order, sampled_order])
        self.assertEqual(generate_order.call_count, 2)


if __name__ == "__main__":
    unittest.main()
