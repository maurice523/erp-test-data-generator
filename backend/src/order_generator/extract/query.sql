WITH
eligible_orders AS (
    SELECT o.order_no
    FROM orders o
    WHERE (:shipViaCode IS NULL OR o.shipping_method LIKE :shipViaCode)
      AND (:orderNo IS NULL OR o.order_no = :orderNo)
      AND EXISTS (
          SELECT 1
          FROM order_lines ol
          WHERE ol.order_no = o.order_no
            AND (:type IS NULL OR ol.order_type = :type)
      )
    ORDER BY o.order_no DESC
    LIMIT 400
),
-- First matching address per order (SQLite has no LATERAL join).
ranked_addresses AS (
    SELECT
        oa.order_no,
        oa.address_1,
        oa.address_2,
        oa.address_3,
        oa.address_4,
        oa.city,
        oa.state,
        oa.postal_code,
        oa.country_code,
        ROW_NUMBER() OVER (
            PARTITION BY oa.order_no
            ORDER BY
                oa.address_1 NULLS LAST,
                oa.address_2 NULLS LAST,
                oa.address_3 NULLS LAST,
                oa.address_4 NULLS LAST,
                oa.city NULLS LAST,
                oa.state NULLS LAST,
                oa.postal_code NULLS LAST,
                oa.country_code NULLS LAST,
                oa.rowid
        ) AS rn
    FROM order_addresses oa
    JOIN eligible_orders eo
      ON eo.order_no = oa.order_no
    WHERE (:countryCode IS NULL OR oa.country_code = :countryCode)
),
-- First contact per customer, with its e-mail address if it has one.
ranked_contacts AS (
    SELECT
        cc.customer_no,
        cc.contact_id,
        cm.value AS email_address,
        ROW_NUMBER() OVER (
            PARTITION BY cc.customer_no
            ORDER BY cc.contact_id
        ) AS rn
    FROM customer_contacts cc
    LEFT JOIN contact_methods cm
      ON cm.contact_id = cc.contact_id
     AND cm.method = 'email'
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
JOIN ranked_addresses sa
  ON sa.order_no = o.order_no
 AND sa.rn = 1
LEFT JOIN ranked_contacts sc
  ON sc.customer_no = o.customer_no
 AND sc.rn = 1
JOIN order_lines ol
  ON ol.order_no = o.order_no
WHERE (:type IS NULL OR ol.order_type = :type)
ORDER BY o.order_no, ol.item_no;
