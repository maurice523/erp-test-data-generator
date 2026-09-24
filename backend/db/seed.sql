-- Fake but plausible data for the tables in schema.sql.
-- Re-runnable: truncates first, and seeds the RNG so runs are reproducible.

TRUNCATE contact_methods, customer_contacts, order_addresses, order_lines, orders;

SELECT setseed(0.42);

-- 60 customers, each with one contact and one default e-mail address.
INSERT INTO customer_contacts (customer_no, contact_id)
SELECT
    'C' || (1000 + n),
    (20000 + n)::text
FROM generate_series(0, 59) AS n;

INSERT INTO contact_methods (contact_id, method, value)
SELECT
    cc.contact_id,
    'email',
    lower(
        (ARRAY['avery', 'blake', 'casey', 'devon', 'ellis', 'flynn', 'harper',
               'jordan', 'kelly', 'logan', 'morgan', 'parker', 'quinn', 'riley',
               'sawyer', 'taylor'])[1 + (n % 16)]
        || '.' ||
        (ARRAY['adams', 'brooks', 'chen', 'diaz', 'evans', 'ford', 'garcia',
               'hayes', 'ingram', 'jensen'])[1 + (n % 10)]
        || '@' ||
        (ARRAY['northwind.example', 'acmesupply.example', 'pinebrook.example',
               'lakeside.example', 'redoak.example'])[1 + (n % 5)]
    )
FROM generate_series(0, 59) AS n
JOIN customer_contacts cc ON cc.contact_id = (20000 + n)::text;

-- 600 orders, so the query's 400-order cap is actually exercised.
INSERT INTO orders (order_no, customer_no, po_number, external_ref, shipping_method)
SELECT
    lpad((500000 + n)::text, 6, '0'),
    'C' || (1000 + (n % 60)),
    'PO-' || (70000 + n),
    'EXT-' || (900000 + n),
    (ARRAY['UPS-GND', 'UPS-GND', 'UPS-GND', 'UPS-NDA', 'UPS-2DAY', 'UPS-2DAY',
           'UPS-3DAY', 'FDX-GND', 'FDX-GND', 'FDX-2DAY', 'FDX-ONT', 'USPS-PRI',
           'DHL-INTL', 'LTL-FRT', 'LTL-FRT', 'PICKUP'])[1 + floor(random() * 16)::int]
FROM generate_series(0, 599) AS n;

-- One shipping address per order, plus a second one for every 10th order so the
-- query's "first address only" behavior has something to pick between.
INSERT INTO order_addresses (
    order_no, address_1, address_2, address_3, address_4, city, state, postal_code, country_code
)
SELECT
    o.order_no,
    (ARRAY['Northwind Trading Co', 'Acme Supply Group', 'Pinebrook Partners',
           'Lakeside Outfitters', 'Red Oak Industries', 'Bright Harbor LLC'])[1 + floor(random() * 6)::int],
    (100 + floor(random() * 8900)::int) || ' ' ||
        (ARRAY['Main St', 'Oak Ave', 'Industrial Pkwy', 'Commerce Dr', 'Lakeshore Blvd',
               'King St W', 'Maple Ln', 'Airport Rd'])[1 + floor(random() * 8)::int],
    CASE WHEN random() < 0.25
         THEN 'Suite ' || (100 + floor(random() * 900)::int)
         ELSE NULL END,
    NULL,
    loc.city,
    loc.state,
    loc.postal_code,
    loc.country_code
FROM orders o
CROSS JOIN LATERAL (
    SELECT * FROM (
        VALUES
            ('Boston', 'MA', '02108', 'US'),
            ('Chicago', 'IL', '60607', 'US'),
            ('Austin', 'TX', '78702', 'US'),
            ('Denver', 'CO', '80206', 'US'),
            ('Atlanta', 'GA', '30318', 'US'),
            ('Seattle', 'WA', '98109', 'US'),
            ('Columbus', 'OH', '43215', 'US'),
            ('Toronto', 'ON', 'M5H 2N2', 'CA'),
            ('Calgary', 'AB', 'T2P 1J9', 'CA'),
            ('Montreal', 'QC', 'H3B 2Y5', 'CA')
    ) AS v (city, state, postal_code, country_code)
    ORDER BY random()
    LIMIT 1
) AS loc;

INSERT INTO order_addresses (
    order_no, address_1, address_2, address_3, address_4, city, state, postal_code, country_code
)
SELECT
    o.order_no,
    'Receiving Dock',
    '12 Warehouse Way',
    NULL,
    NULL,
    'Reno',
    'NV',
    '89502',
    'US'
FROM orders o
WHERE right(o.order_no, 1) = '0';

-- 1 to 5 lines per order. The count is derived from order_no rather than
-- random(), because a LATERAL argument that ignores the outer row is evaluated
-- once for the whole query and would give every order the same line count.
INSERT INTO order_lines (
    order_no, line_no, item_no, quantity, order_type, proof_requested
)
SELECT
    o.order_no,
    line.n,
    (ARRAY['PN-1001', 'PN-1002', 'PN-1145', 'PN-2210', 'PN-2317', 'PN-3080',
           'PN-3412', 'PN-4500', 'PN-4788', 'PN-5120', 'PN-6033', 'PN-7741'])[1 + floor(random() * 12)::int],
    1 + floor(random() * 500)::int,
    (ARRAY['SAMPLE', 'SAMPLE', 'NO_PRINT', 'NO_PRINT', NULL])[1 + floor(random() * 5)::int],
    CASE WHEN random() < 0.35 THEN 'Y' ELSE 'N' END
FROM orders o
CROSS JOIN LATERAL generate_series(1, 1 + (abs(hashtext(o.order_no)) % 5)) AS line (n);

ANALYZE;
