"""Fake but plausible data for the tables in schema.sql.

Reproducible: the RNG is seeded, so every run produces the same rows.
``seed_statements()`` returns multi-row INSERTs with the values inlined; the
data is generated here, never user input, and ``sql_literal`` escapes quotes.
"""

import random
import zlib


ROWS_PER_INSERT = 200

FIRST_NAMES = (
    "avery", "blake", "casey", "devon", "ellis", "flynn", "harper", "jordan",
    "kelly", "logan", "morgan", "parker", "quinn", "riley", "sawyer", "taylor",
)
LAST_NAMES = (
    "adams", "brooks", "chen", "diaz", "evans", "ford", "garcia", "hayes",
    "ingram", "jensen",
)
DOMAINS = (
    "northwind.example", "acmesupply.example", "pinebrook.example",
    "lakeside.example", "redoak.example",
)
SHIPPING_METHODS = (
    "UPS-GND", "UPS-GND", "UPS-GND", "UPS-NDA", "UPS-2DAY", "UPS-2DAY",
    "UPS-3DAY", "FDX-GND", "FDX-GND", "FDX-2DAY", "FDX-ONT", "USPS-PRI",
    "DHL-INTL", "LTL-FRT", "LTL-FRT", "PICKUP",
)
COMPANIES = (
    "Northwind Trading Co", "Acme Supply Group", "Pinebrook Partners",
    "Lakeside Outfitters", "Red Oak Industries", "Bright Harbor LLC",
)
STREETS = (
    "Main St", "Oak Ave", "Industrial Pkwy", "Commerce Dr", "Lakeshore Blvd",
    "King St W", "Maple Ln", "Airport Rd",
)
LOCATIONS = (
    ("Boston", "MA", "02108", "US"),
    ("Chicago", "IL", "60607", "US"),
    ("Austin", "TX", "78702", "US"),
    ("Denver", "CO", "80206", "US"),
    ("Atlanta", "GA", "30318", "US"),
    ("Seattle", "WA", "98109", "US"),
    ("Columbus", "OH", "43215", "US"),
    ("Toronto", "ON", "M5H 2N2", "CA"),
    ("Calgary", "AB", "T2P 1J9", "CA"),
    ("Montreal", "QC", "H3B 2Y5", "CA"),
)
ITEMS = (
    "PN-1001", "PN-1002", "PN-1145", "PN-2210", "PN-2317", "PN-3080",
    "PN-3412", "PN-4500", "PN-4788", "PN-5120", "PN-6033", "PN-7741",
)
ORDER_TYPES = ("SAMPLE", "SAMPLE", "NO_PRINT", "NO_PRINT", None)


def generate(seed: int = 42) -> dict[str, list[tuple]]:
    rng = random.Random(seed)
    tables: dict[str, list[tuple]] = {}

    # 60 customers, each with one contact and one default e-mail address.
    tables["customer_contacts"] = [
        (f"C{1000 + n}", str(20000 + n)) for n in range(60)
    ]
    tables["contact_methods"] = [
        (
            str(20000 + n),
            "email",
            f"{FIRST_NAMES[n % 16]}.{LAST_NAMES[n % 10]}@{DOMAINS[n % 5]}",
        )
        for n in range(60)
    ]

    # 600 orders, so the query's 400-order cap is actually exercised.
    tables["orders"] = [
        (
            str(500000 + n),
            f"C{1000 + n % 60}",
            f"PO-{70000 + n}",
            f"EXT-{900000 + n}",
            rng.choice(SHIPPING_METHODS),
        )
        for n in range(600)
    ]
    order_numbers = [order[0] for order in tables["orders"]]

    # One shipping address per order, plus a second one for every 10th order so
    # the query's "first address only" behavior has something to pick between.
    addresses = []
    for order_no in order_numbers:
        addresses.append(
            (
                order_no,
                rng.choice(COMPANIES),
                f"{rng.randint(100, 8999)} {rng.choice(STREETS)}",
                f"Suite {rng.randint(100, 999)}" if rng.random() < 0.25 else None,
                None,
                *rng.choice(LOCATIONS),
            )
        )
    for order_no in order_numbers:
        if order_no.endswith("0"):
            addresses.append(
                (order_no, "Receiving Dock", "12 Warehouse Way", None, None,
                 "Reno", "NV", "89502", "US")
            )
    tables["order_addresses"] = addresses

    # 1 to 5 lines per order, the count derived from order_no.
    lines = []
    for order_no in order_numbers:
        for line_no in range(1, 2 + zlib.crc32(order_no.encode()) % 5):
            lines.append(
                (
                    order_no,
                    line_no,
                    rng.choice(ITEMS),
                    rng.randint(1, 500),
                    rng.choice(ORDER_TYPES),
                    "Y" if rng.random() < 0.35 else "N",
                )
            )
    tables["order_lines"] = lines

    return tables


COLUMNS = {
    "customer_contacts": ("customer_no", "contact_id"),
    "contact_methods": ("contact_id", "method", "value"),
    "orders": ("order_no", "customer_no", "po_number", "external_ref", "shipping_method"),
    "order_addresses": (
        "order_no", "address_1", "address_2", "address_3", "address_4",
        "city", "state", "postal_code", "country_code",
    ),
    "order_lines": (
        "order_no", "line_no", "item_no", "quantity", "order_type", "proof_requested",
    ),
}

# Parents before children, so the foreign keys hold at every step.
INSERT_ORDER = (
    "customer_contacts", "contact_methods", "orders", "order_addresses", "order_lines",
)


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def seed_statements() -> list[str]:
    tables = generate()
    statements = []
    for table in INSERT_ORDER:
        rows = tables[table]
        columns = ", ".join(COLUMNS[table])
        for start in range(0, len(rows), ROWS_PER_INSERT):
            values = ",\n".join(
                "(" + ", ".join(sql_literal(value) for value in row) + ")"
                for row in rows[start:start + ROWS_PER_INSERT]
            )
            statements.append(f"INSERT INTO {table} ({columns}) VALUES\n{values};")
    return statements
