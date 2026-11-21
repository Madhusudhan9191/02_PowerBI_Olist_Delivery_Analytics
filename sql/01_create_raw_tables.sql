-- ============================================================================
-- SCRIPT 01: Create Raw Staging Tables
-- PROJECT: Olist E-commerce Delivery Performance & Customer Satisfaction
-- ENVIRONMENT: PostgreSQL 16+
-- AUTHOR: Independent Portfolio Project
-- DESCRIPTION: DDL for 1:1 raw staging tables matching Kaggle CSV schemas.
-- ============================================================================

DROP TABLE IF EXISTS raw_order_items CASCADE;
DROP TABLE IF EXISTS raw_order_payments CASCADE;
DROP TABLE IF EXISTS raw_order_reviews CASCADE;
DROP TABLE IF EXISTS raw_orders CASCADE;
DROP TABLE IF EXISTS raw_customers CASCADE;
DROP TABLE IF EXISTS raw_products CASCADE;
DROP TABLE IF EXISTS raw_sellers CASCADE;
DROP TABLE IF EXISTS raw_geolocation CASCADE;
DROP TABLE IF EXISTS raw_product_category_name_translation CASCADE;

-- 1. Customers Staging
CREATE TABLE raw_customers (
    customer_id                 VARCHAR(50) NOT NULL,
    customer_unique_id          VARCHAR(50) NOT NULL,
    customer_zip_code_prefix    INTEGER NOT NULL,
    customer_city               VARCHAR(100) NOT NULL,
    customer_state              VARCHAR(10) NOT NULL,
    CONSTRAINT pk_raw_customers PRIMARY KEY (customer_id)
);

-- 2. Geolocation Staging (no PK: multiple coordinate samples per prefix)
CREATE TABLE raw_geolocation (
    geolocation_zip_code_prefix INTEGER NOT NULL,
    geolocation_lat             NUMERIC(12, 8) NOT NULL,
    geolocation_lng             NUMERIC(12, 8) NOT NULL,
    geolocation_city            VARCHAR(100) NOT NULL,
    geolocation_state           VARCHAR(10) NOT NULL
);

-- 3. Orders Staging
CREATE TABLE raw_orders (
    order_id                        VARCHAR(50) NOT NULL,
    customer_id                     VARCHAR(50) NOT NULL,
    order_status                    VARCHAR(30) NOT NULL,
    order_purchase_timestamp        TIMESTAMP NOT NULL,
    order_approved_at               TIMESTAMP,
    order_delivered_carrier_date    TIMESTAMP,
    order_delivered_customer_date   TIMESTAMP,
    order_estimated_delivery_date   TIMESTAMP NOT NULL,
    CONSTRAINT pk_raw_orders PRIMARY KEY (order_id)
);

-- 4. Order Items Staging
CREATE TABLE raw_order_items (
    order_id            VARCHAR(50) NOT NULL,
    order_item_id       INTEGER NOT NULL,
    product_id          VARCHAR(50) NOT NULL,
    seller_id           VARCHAR(50) NOT NULL,
    shipping_limit_date TIMESTAMP NOT NULL,
    price               NUMERIC(10, 2) NOT NULL,
    freight_value       NUMERIC(10, 2) NOT NULL,
    CONSTRAINT pk_raw_order_items PRIMARY KEY (order_id, order_item_id)
);

-- 5. Order Payments Staging
CREATE TABLE raw_order_payments (
    order_id            VARCHAR(50) NOT NULL,
    payment_sequential  INTEGER NOT NULL,
    payment_type        VARCHAR(30) NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value       NUMERIC(10, 2) NOT NULL,
    CONSTRAINT pk_raw_order_payments PRIMARY KEY (order_id, payment_sequential)
);

-- 6. Order Reviews Staging
-- Note: review_id has duplicates across submissions in raw data; surrogate ID used for raw staging
CREATE TABLE raw_order_reviews (
    raw_review_key          BIGSERIAL PRIMARY KEY,
    review_id               VARCHAR(50) NOT NULL,
    order_id                VARCHAR(50) NOT NULL,
    review_score            INTEGER NOT NULL,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP NOT NULL,
    review_answer_timestamp TIMESTAMP NOT NULL
);

-- 7. Products Staging
CREATE TABLE raw_products (
    product_id                  VARCHAR(50) NOT NULL,
    product_category_name       VARCHAR(100),
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10, 2),
    product_length_cm           NUMERIC(10, 2),
    product_height_cm           NUMERIC(10, 2),
    product_width_cm            NUMERIC(10, 2),
    CONSTRAINT pk_raw_products PRIMARY KEY (product_id)
);

-- 8. Sellers Staging
CREATE TABLE raw_sellers (
    seller_id               VARCHAR(50) NOT NULL,
    seller_zip_code_prefix  INTEGER NOT NULL,
    seller_city             VARCHAR(100) NOT NULL,
    seller_state            VARCHAR(10) NOT NULL,
    CONSTRAINT pk_raw_sellers PRIMARY KEY (seller_id)
);

-- 9. Category Name Translation Staging
CREATE TABLE raw_product_category_name_translation (
    product_category_name           VARCHAR(100) NOT NULL,
    product_category_name_english   VARCHAR(100) NOT NULL,
    CONSTRAINT pk_raw_category_translation PRIMARY KEY (product_category_name)
);

COMMENT ON TABLE raw_customers IS 'Staging: raw customer records (99,441 rows)';
COMMENT ON TABLE raw_geolocation IS 'Staging: raw geolocation coordinates (1,000,163 rows)';
COMMENT ON TABLE raw_orders IS 'Staging: raw order records (99,441 rows)';
COMMENT ON TABLE raw_order_items IS 'Staging: raw order item records (112,650 rows)';
COMMENT ON TABLE raw_order_payments IS 'Staging: raw payment transactions (103,886 rows)';
COMMENT ON TABLE raw_order_reviews IS 'Staging: raw customer reviews (99,224 rows)';
COMMENT ON TABLE raw_products IS 'Staging: raw product records (32,951 rows)';
COMMENT ON TABLE raw_sellers IS 'Staging: raw merchant records (3,095 rows)';
COMMENT ON TABLE raw_product_category_name_translation IS 'Staging: category translations (71 rows)';
