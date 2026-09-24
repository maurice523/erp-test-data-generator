-- Tables read by extract/query.sql. Safe to re-run: drops and recreates
-- everything (the spend-cap table, api_usage, is managed by the API and
-- is not touched here).

DROP TABLE IF EXISTS contact_methods CASCADE;
DROP TABLE IF EXISTS customer_contacts CASCADE;
DROP TABLE IF EXISTS order_addresses CASCADE;
DROP TABLE IF EXISTS order_lines CASCADE;
DROP TABLE IF EXISTS orders CASCADE;

CREATE TABLE orders (
    order_no         varchar(12) PRIMARY KEY,
    customer_no      varchar(20) NOT NULL,
    po_number        varchar(50),
    external_ref     varchar(50),
    shipping_method  varchar(20)
);

CREATE TABLE order_lines (
    order_no         varchar(12) NOT NULL REFERENCES orders (order_no),
    line_no          integer     NOT NULL,
    item_no          varchar(25) NOT NULL,
    quantity         integer     NOT NULL,
    order_type       varchar(10),
    proof_requested  varchar(1),
    PRIMARY KEY (order_no, line_no)
);

CREATE TABLE order_addresses (
    order_no      varchar(12) NOT NULL REFERENCES orders (order_no),
    address_1     varchar(100),
    address_2     varchar(35),
    address_3     varchar(100),
    address_4     varchar(100),
    city          varchar(35),
    state         varchar(35),
    postal_code   varchar(35),
    country_code  varchar(2)
);

CREATE TABLE customer_contacts (
    customer_no  varchar(20) NOT NULL,
    contact_id   varchar(20) NOT NULL,
    PRIMARY KEY (customer_no, contact_id)
);

CREATE TABLE contact_methods (
    contact_id  varchar(20)  NOT NULL,
    method      varchar(20)  NOT NULL,
    value       varchar(200) NOT NULL,
    PRIMARY KEY (contact_id, method)
);

CREATE INDEX ON order_lines (order_no);
CREATE INDEX ON order_addresses (order_no);
