WITH
eligible_orders AS (
    SELECT o.order_no
    FROM orders o
    WHERE (%(shipViaCode)s::text IS NULL OR o.shipping_method LIKE %(shipViaCode)s::text)
      AND (%(orderNo)s::text IS NULL OR o.order_no = %(orderNo)s::text)
      AND EXISTS (
          SELECT 1
          FROM order_lines ol
          WHERE ol.order_no = o.order_no
            AND (%(type)s::text IS NULL OR ol.order_type = %(type)s::text)
      )
    ORDER BY o.order_no DESC
    LIMIT 400
)
SELECT
    o.order_no AS "orderNo",
    o.customer_no AS "customerNo",
    o.po_number AS "poNumber",
    o.external_ref AS "externalRefNo",
    sc.contact_id AS "id",
    sc.email_address AS "emailAddress",
    o.shipping_method AS "shipViaCode",
    sa.address_1 AS "address1",
    sa.address_2 AS "address2",
    sa.address_3 AS "address3",
    sa.address_4 AS "address4",
    sa.city AS "city",
    sa.state AS "state",
    sa.postal_code AS "zipCode",
    sa.country_code AS "countryCode",
    ol.item_no AS "partNo",
    ol.quantity AS "quantity",
    ol.order_type AS "type",
    ol.proof_requested AS "proofRequested"
FROM eligible_orders eo
JOIN orders o
  ON o.order_no = eo.order_no
CROSS JOIN LATERAL (
    SELECT
        oa.address_1,
        oa.address_2,
        oa.address_3,
        oa.address_4,
        oa.city,
        oa.state,
        oa.postal_code,
        oa.country_code
    FROM order_addresses oa
    WHERE oa.order_no = o.order_no
      AND (%(countryCode)s::text IS NULL OR oa.country_code = %(countryCode)s::text)
    ORDER BY
        oa.address_1,
        oa.address_2,
        oa.address_3,
        oa.address_4,
        oa.city,
        oa.state,
        oa.postal_code,
        oa.country_code,
        oa.ctid
    FETCH FIRST 1 ROW ONLY
) sa
LEFT JOIN LATERAL (
    SELECT
        cc.contact_id,
        cm.value AS email_address
    FROM customer_contacts cc
    LEFT JOIN contact_methods cm
      ON cm.contact_id = cc.contact_id
     AND cm.method = 'email'
    WHERE cc.customer_no = o.customer_no
    ORDER BY cc.contact_id
    FETCH FIRST 1 ROW ONLY
) sc ON true
JOIN order_lines ol
  ON ol.order_no = o.order_no
WHERE (%(type)s::text IS NULL OR ol.order_type = %(type)s::text)
ORDER BY o.order_no, ol.item_no;
