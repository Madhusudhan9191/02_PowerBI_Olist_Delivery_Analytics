-- ============================================================================
-- SCRIPT 03: Create Production Derived Tables (Star Schema)
-- PROJECT: Olist E-commerce Delivery Performance & Customer Satisfaction
-- ENVIRONMENT: PostgreSQL 16+
-- AUTHOR: Independent Portfolio Project
-- DESCRIPTION: DDL and idempotent transformations (T1..T10) creating the 
--              production analytical star schema with explicit constraints,
--              calendar-date SLA definitions, and non-destructive anomaly flags.
-- ============================================================================

DROP TABLE IF EXISTS fact_order_items CASCADE;
DROP TABLE IF EXISTS fact_order_payments CASCADE;
DROP TABLE IF EXISTS fact_order_delivery CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_seller CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_geography CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ----------------------------------------------------------------------------
-- 1. DIM_DATE (Calendar Dimension)
-- Transformation T1: Date Dimension Generation
-- ----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key            INTEGER PRIMARY KEY,            -- YYYYMMDD
    full_date           DATE NOT NULL UNIQUE,
    year_num            INTEGER NOT NULL,
    quarter_num         INTEGER NOT NULL,
    quarter_name        VARCHAR(10) NOT NULL,
    month_num           INTEGER NOT NULL,
    month_name          VARCHAR(20) NOT NULL,
    year_month          VARCHAR(7) NOT NULL,            -- YYYY-MM
    week_of_year        INTEGER NOT NULL,
    day_of_month        INTEGER NOT NULL,
    day_of_week         INTEGER NOT NULL,               -- 1 = Monday, 7 = Sunday
    day_name            VARCHAR(20) NOT NULL,
    is_weekend          BOOLEAN NOT NULL
);

INSERT INTO dim_date
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_key,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::INTEGER AS year_num,
    EXTRACT(QUARTER FROM d)::INTEGER AS quarter_num,
    'Q' || EXTRACT(QUARTER FROM d)::TEXT AS quarter_name,
    EXTRACT(MONTH FROM d)::INTEGER AS month_num,
    TO_CHAR(d, 'FMMonth') AS month_name,
    TO_CHAR(d, 'YYYY-MM') AS year_month,
    EXTRACT(WEEK FROM d)::INTEGER AS week_of_year,
    EXTRACT(DAY FROM d)::INTEGER AS day_of_month,
    EXTRACT(ISODOW FROM d)::INTEGER AS day_of_week,
    TO_CHAR(d, 'FMDay') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2016-01-01'::DATE, '2018-12-31'::DATE, '1 day'::INTERVAL) AS d;

-- ----------------------------------------------------------------------------
-- 2. DIM_GEOGRAPHY (Deduplicated Postal Centroids)
-- Transformation T2: Geolocation Deduplication to Zip Prefix Grain
-- ----------------------------------------------------------------------------
CREATE TABLE dim_geography (
    zip_code_prefix     INTEGER PRIMARY KEY,
    median_lat          NUMERIC(12, 8) NOT NULL,
    median_lng          NUMERIC(12, 8) NOT NULL,
    primary_city        VARCHAR(100) NOT NULL,
    primary_state       VARCHAR(10) NOT NULL,
    coordinate_count    INTEGER NOT NULL
);

INSERT INTO dim_geography
WITH geo_stats AS (
    SELECT 
        geolocation_zip_code_prefix AS zip_code_prefix,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lat)::NUMERIC(12,8) AS median_lat,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY geolocation_lng)::NUMERIC(12,8) AS median_lng,
        COUNT(*) AS coordinate_count
    FROM raw_geolocation
    GROUP BY geolocation_zip_code_prefix
),
geo_city_mode AS (
    SELECT 
        geolocation_zip_code_prefix AS zip_code_prefix,
        geolocation_city,
        geolocation_state,
        ROW_NUMBER() OVER (PARTITION BY geolocation_zip_code_prefix ORDER BY COUNT(*) DESC) AS rn
    FROM raw_geolocation
    GROUP BY geolocation_zip_code_prefix, geolocation_city, geolocation_state
)
SELECT 
    s.zip_code_prefix,
    s.median_lat,
    s.median_lng,
    m.geolocation_city AS primary_city,
    m.geolocation_state AS primary_state,
    s.coordinate_count
FROM geo_stats s
JOIN geo_city_mode m ON s.zip_code_prefix = m.zip_code_prefix AND m.rn = 1;

-- ----------------------------------------------------------------------------
-- 3. DIM_CUSTOMER (Entity Resolution at customer_unique_id)
-- Transformation T3: Customer Entity Resolution
-- ----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_unique_id          VARCHAR(50) PRIMARY KEY,
    primary_city                VARCHAR(100) NOT NULL,
    primary_state               VARCHAR(10) NOT NULL,
    primary_zip_code_prefix     INTEGER NOT NULL,
    first_order_timestamp       TIMESTAMP NOT NULL,
    last_order_timestamp        TIMESTAMP NOT NULL,
    lifetime_orders             INTEGER NOT NULL,
    is_repeat_customer          BOOLEAN NOT NULL
);

INSERT INTO dim_customer
WITH cust_orders AS (
    SELECT 
        c.customer_unique_id,
        c.customer_city,
        c.customer_state,
        c.customer_zip_code_prefix,
        o.order_purchase_timestamp,
        ROW_NUMBER() OVER (PARTITION BY c.customer_unique_id ORDER BY o.order_purchase_timestamp DESC) AS rn_latest
    FROM raw_customers c
    JOIN raw_orders o ON c.customer_id = o.customer_id
),
cust_agg AS (
    SELECT 
        c.customer_unique_id,
        MIN(o.order_purchase_timestamp) AS first_order_timestamp,
        MAX(o.order_purchase_timestamp) AS last_order_timestamp,
        COUNT(DISTINCT o.order_id) AS lifetime_orders
    FROM raw_customers c
    JOIN raw_orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_unique_id
)
SELECT 
    a.customer_unique_id,
    l.customer_city AS primary_city,
    l.customer_state AS primary_state,
    l.customer_zip_code_prefix AS primary_zip_code_prefix,
    a.first_order_timestamp,
    a.last_order_timestamp,
    a.lifetime_orders,
    CASE WHEN a.lifetime_orders >= 2 THEN TRUE ELSE FALSE END AS is_repeat_customer
FROM cust_agg a
JOIN cust_orders l ON a.customer_unique_id = l.customer_unique_id AND l.rn_latest = 1;

-- ----------------------------------------------------------------------------
-- 4. DIM_SELLER (Merchant Dimension)
-- Transformation T4: Merchant Dimension Construction
-- ----------------------------------------------------------------------------
CREATE TABLE dim_seller (
    seller_id               VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix  INTEGER NOT NULL,
    seller_city             VARCHAR(100) NOT NULL,
    seller_state            VARCHAR(10) NOT NULL
);

INSERT INTO dim_seller
SELECT 
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state
FROM raw_sellers;

-- ----------------------------------------------------------------------------
-- 5. DIM_PRODUCT (Product Dimension with Translation & Category Fallback)
-- Transformation T5: Category Mapping & Null Handling
-- ----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_id                  VARCHAR(50) PRIMARY KEY,
    product_category_name_pt    VARCHAR(100) NOT NULL,
    product_category_name_en    VARCHAR(100) NOT NULL,
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            NUMERIC(10, 2),
    product_length_cm           NUMERIC(10, 2),
    product_height_cm           NUMERIC(10, 2),
    product_width_cm            NUMERIC(10, 2)
);

INSERT INTO dim_product
SELECT 
    p.product_id,
    COALESCE(p.product_category_name, 'uncategorized') AS product_category_name_pt,
    CASE 
        WHEN p.product_category_name IS NULL THEN 'uncategorized'
        WHEN p.product_category_name = 'pc_gamer' THEN 'pc_gamer'
        WHEN p.product_category_name = 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'kitchen_small_appliances'
        ELSE COALESCE(t.product_category_name_english, p.product_category_name)
    END AS product_category_name_en,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM raw_products p
LEFT JOIN raw_product_category_name_translation t 
    ON p.product_category_name = t.product_category_name;

-- ----------------------------------------------------------------------------
-- 6. FACT_ORDER_DELIVERY (Order-Level Delivery Milestones & Deduplicated Reviews)
-- Transformation T6: Date-Level SLA, Non-Destructive QA Flags, Review Deduplication
-- ----------------------------------------------------------------------------
CREATE TABLE fact_order_delivery (
    order_id                            VARCHAR(50) PRIMARY KEY,
    customer_id                         VARCHAR(50) NOT NULL,
    customer_unique_id                  VARCHAR(50) NOT NULL,
    order_status                        VARCHAR(30) NOT NULL,
    
    -- Timestamps
    order_purchase_timestamp            TIMESTAMP NOT NULL,
    order_approved_at                   TIMESTAMP,
    order_delivered_carrier_date        TIMESTAMP,
    order_delivered_customer_date       TIMESTAMP,
    order_estimated_delivery_date       TIMESTAMP NOT NULL,
    
    -- Date-only projections
    order_purchase_date                 DATE NOT NULL,
    order_delivered_customer_date_only  DATE,
    order_estimated_delivery_date_only   DATE NOT NULL,
    
    -- Delivery SLA Classifications (Date-Level)
    is_delivered                        BOOLEAN NOT NULL,
    is_valid_delivery_date              BOOLEAN NOT NULL,
    is_on_time                          BOOLEAN NOT NULL,
    is_late                             BOOLEAN NOT NULL,
    delay_days                          INTEGER NOT NULL,   -- Whole calendar days (>= 0 when late, else 0)
    estimate_variance_days              INTEGER,           -- Whole days: estimated - delivered (positive = early)
    
    -- Fulfillment Lead Times (Fractional Days)
    handling_days                       NUMERIC(10, 4),    -- Carrier handoff - approved_at
    transit_days                        NUMERIC(10, 4),    -- Customer delivery - carrier handoff
    cycle_days                          NUMERIC(10, 4),    -- Customer delivery - purchase timestamp
    
    -- Chronological Quality & Anomaly Flags (Non-destructive)
    carrier_before_purchase             BOOLEAN NOT NULL,
    carrier_before_approved             BOOLEAN NOT NULL,
    delivery_before_purchase            BOOLEAN NOT NULL,
    delivery_before_carrier             BOOLEAN NOT NULL,
    delivery_before_approved            BOOLEAN NOT NULL,
    has_negative_handling               BOOLEAN NOT NULL,
    has_negative_transit                BOOLEAN NOT NULL,
    is_anomalous_sequence               BOOLEAN NOT NULL,
    is_clean_fulfillment                BOOLEAN NOT NULL,  -- Delivered, valid dates, handling >= 0 and transit >= 0
    is_steady_state_window              BOOLEAN NOT NULL,  -- 2017-01-01 to 2018-08-31
    
    -- Deduplicated Review Attributes (Latest review per order)
    review_id                           VARCHAR(50),
    review_score                        INTEGER,
    review_creation_date                DATE,
    review_answer_timestamp             TIMESTAMP,
    has_review                          BOOLEAN NOT NULL,
    review_created_before_delivery      BOOLEAN NOT NULL,
    
    CONSTRAINT fk_delivery_customer FOREIGN KEY (customer_unique_id) REFERENCES dim_customer (customer_unique_id),
    CONSTRAINT fk_delivery_date FOREIGN KEY (order_purchase_date) REFERENCES dim_date (full_date)
);

INSERT INTO fact_order_delivery
WITH dedup_reviews AS (
    SELECT 
        order_id,
        review_id,
        review_score,
        review_creation_date::DATE AS review_creation_date,
        review_answer_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY order_id 
            ORDER BY review_answer_timestamp DESC, review_creation_date DESC, review_id DESC
        ) AS rn
    FROM raw_order_reviews
)
SELECT 
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    o.order_status,
    
    -- Raw Timestamps
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    
    -- Calendar Date Projections
    o.order_purchase_timestamp::DATE AS order_purchase_date,
    o.order_delivered_customer_date::DATE AS order_delivered_customer_date_only,
    o.order_estimated_delivery_date::DATE AS order_estimated_delivery_date_only,
    
    -- Status and Delivery Validations
    (o.order_status = 'delivered') AS is_delivered,
    (o.order_delivered_customer_date IS NOT NULL) AS is_valid_delivery_date,
    
    -- Canonical Date-Level SLA Classification
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (o.order_delivered_customer_date::DATE <= o.order_estimated_delivery_date::DATE)
        ELSE FALSE 
    END AS is_on_time,
    
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (o.order_delivered_customer_date::DATE > o.order_estimated_delivery_date::DATE)
        ELSE FALSE 
    END AS is_late,
    
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL 
             AND (o.order_delivered_customer_date::DATE > o.order_estimated_delivery_date::DATE)
        THEN (o.order_delivered_customer_date::DATE - o.order_estimated_delivery_date::DATE)
        ELSE 0 
    END AS delay_days,
    
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (o.order_estimated_delivery_date::DATE - o.order_delivered_customer_date::DATE)
        ELSE NULL 
    END AS estimate_variance_days,
    
    -- Lead Times in Fractional Days
    CASE 
        WHEN o.order_delivered_carrier_date IS NOT NULL AND o.order_approved_at IS NOT NULL
        THEN ROUND((EXTRACT(EPOCH FROM (o.order_delivered_carrier_date - o.order_approved_at)) / 86400.0)::NUMERIC, 4)
        ELSE NULL 
    END AS handling_days,
    
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_carrier_date IS NOT NULL
        THEN ROUND((EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_delivered_carrier_date)) / 86400.0)::NUMERIC, 4)
        ELSE NULL 
    END AS transit_days,
    
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL
        THEN ROUND((EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp)) / 86400.0)::NUMERIC, 4)
        ELSE NULL 
    END AS cycle_days,
    
    -- Non-Destructive Chronological Anomaly Flags (COALESCE handles null timestamps)
    COALESCE(o.order_delivered_carrier_date < o.order_purchase_timestamp, FALSE) AS carrier_before_purchase,
    COALESCE(o.order_delivered_carrier_date < o.order_approved_at, FALSE) AS carrier_before_approved,
    COALESCE(o.order_delivered_customer_date < o.order_purchase_timestamp, FALSE) AS delivery_before_purchase,
    COALESCE(o.order_delivered_customer_date < o.order_delivered_carrier_date, FALSE) AS delivery_before_carrier,
    COALESCE(o.order_delivered_customer_date < o.order_approved_at, FALSE) AS delivery_before_approved,
    
    COALESCE(o.order_delivered_carrier_date < o.order_approved_at, FALSE) AS has_negative_handling,
    COALESCE(o.order_delivered_customer_date < o.order_delivered_carrier_date, FALSE) AS has_negative_transit,
    
    (
        COALESCE(o.order_delivered_carrier_date < o.order_purchase_timestamp, FALSE) OR
        COALESCE(o.order_delivered_carrier_date < o.order_approved_at, FALSE) OR
        COALESCE(o.order_delivered_customer_date < o.order_purchase_timestamp, FALSE) OR
        COALESCE(o.order_delivered_customer_date < o.order_delivered_carrier_date, FALSE) OR
        COALESCE(o.order_delivered_customer_date < o.order_approved_at, FALSE)
    ) AS is_anomalous_sequence,
    
    (
        o.order_status = 'delivered' 
        AND o.order_delivered_customer_date IS NOT NULL 
        AND o.order_approved_at IS NOT NULL 
        AND o.order_delivered_carrier_date IS NOT NULL 
        AND (o.order_delivered_carrier_date >= o.order_approved_at) 
        AND (o.order_delivered_customer_date >= o.order_delivered_carrier_date)
    ) AS is_clean_fulfillment,
    
    (o.order_purchase_timestamp >= '2017-01-01 00:00:00' AND o.order_purchase_timestamp <= '2018-08-31 23:59:59') AS is_steady_state_window,
    
    -- Deduplicated Review Information
    r.review_id,
    r.review_score,
    r.review_creation_date,
    r.review_answer_timestamp,
    (r.review_id IS NOT NULL) AS has_review,
    
    CASE 
        WHEN r.review_id IS NOT NULL AND o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (r.review_creation_date < o.order_delivered_customer_date::DATE)
        ELSE FALSE 
    END AS review_created_before_delivery

FROM raw_orders o
JOIN raw_customers c ON o.customer_id = c.customer_id
LEFT JOIN dedup_reviews r ON o.order_id = r.order_id AND r.rn = 1;

-- ----------------------------------------------------------------------------
-- 7. FACT_ORDER_ITEMS (Revenue Grain with Route Distance)
-- Transformation T7: Item Revenue, Shipping Burden & Haversine Distance
-- ----------------------------------------------------------------------------
CREATE TABLE fact_order_items (
    order_id                VARCHAR(50) NOT NULL,
    order_item_id           INTEGER NOT NULL,
    product_id              VARCHAR(50) NOT NULL,
    seller_id               VARCHAR(50) NOT NULL,
    customer_unique_id      VARCHAR(50) NOT NULL,
    order_purchase_date     DATE NOT NULL,
    shipping_limit_date     TIMESTAMP NOT NULL,
    price                   NUMERIC(10, 2) NOT NULL,
    freight_value           NUMERIC(10, 2) NOT NULL,
    total_item_spend        NUMERIC(10, 2) NOT NULL,
    freight_to_price_ratio  NUMERIC(10, 4) NOT NULL,
    customer_zip_prefix     INTEGER NOT NULL,
    seller_zip_prefix       INTEGER NOT NULL,
    route_distance_km       NUMERIC(10, 2),
    is_interstate           BOOLEAN NOT NULL,
    
    CONSTRAINT pk_fact_order_items PRIMARY KEY (order_id, order_item_id),
    CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES fact_order_delivery (order_id),
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES dim_product (product_id),
    CONSTRAINT fk_items_seller FOREIGN KEY (seller_id) REFERENCES dim_seller (seller_id),
    CONSTRAINT fk_items_customer FOREIGN KEY (customer_unique_id) REFERENCES dim_customer (customer_unique_id),
    CONSTRAINT fk_items_date FOREIGN KEY (order_purchase_date) REFERENCES dim_date (full_date)
);

INSERT INTO fact_order_items
SELECT 
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    c.customer_unique_id,
    o.order_purchase_timestamp::DATE AS order_purchase_date,
    i.shipping_limit_date,
    i.price,
    i.freight_value,
    (i.price + i.freight_value) AS total_item_spend,
    ROUND((i.freight_value / NULLIF(i.price, 0))::NUMERIC, 4) AS freight_to_price_ratio,
    c.customer_zip_code_prefix AS customer_zip_prefix,
    s.seller_zip_code_prefix AS seller_zip_prefix,
    
    -- Haversine Route Distance Formula (Earth radius ~ 6,371 km)
    CASE 
        WHEN g_cust.median_lat IS NOT NULL AND g_sell.median_lat IS NOT NULL THEN
            ROUND((
                2 * 6371.0 * ASIN(SQRT(
                    POWER(SIN(RADIANS((g_cust.median_lat - g_sell.median_lat) / 2.0)), 2) +
                    COS(RADIANS(g_sell.median_lat)) * COS(RADIANS(g_cust.median_lat)) *
                    POWER(SIN(RADIANS((g_cust.median_lng - g_sell.median_lng) / 2.0)), 2)
                ))
            )::NUMERIC, 2)
        ELSE NULL 
    END AS route_distance_km,
    
    (c.customer_state <> s.seller_state) AS is_interstate

FROM raw_order_items i
JOIN raw_orders o ON i.order_id = o.order_id
JOIN raw_customers c ON o.customer_id = c.customer_id
JOIN raw_sellers s ON i.seller_id = s.seller_id
LEFT JOIN dim_geography g_cust ON c.customer_zip_code_prefix = g_cust.zip_code_prefix
LEFT JOIN dim_geography g_sell ON s.seller_zip_code_prefix = g_sell.zip_code_prefix;

-- ----------------------------------------------------------------------------
-- 8. FACT_ORDER_PAYMENTS (Payment Transactions Grain)
-- Transformation T8: Payment Transactions Staging
-- ----------------------------------------------------------------------------
CREATE TABLE fact_order_payments (
    order_id                VARCHAR(50) NOT NULL,
    payment_sequential      INTEGER NOT NULL,
    payment_type            VARCHAR(30) NOT NULL,
    payment_installments    INTEGER NOT NULL,
    payment_value           NUMERIC(10, 2) NOT NULL,
    
    CONSTRAINT pk_fact_order_payments PRIMARY KEY (order_id, payment_sequential),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES fact_order_delivery (order_id)
);

INSERT INTO fact_order_payments
SELECT 
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
FROM raw_order_payments;

-- ----------------------------------------------------------------------------
-- 9. PERFORMANCE INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX idx_delivery_purchase_date ON fact_order_delivery (order_purchase_date);
CREATE INDEX idx_delivery_status_late ON fact_order_delivery (order_status, is_late);
CREATE INDEX idx_delivery_customer_uniq ON fact_order_delivery (customer_unique_id);
CREATE INDEX idx_items_product ON fact_order_items (product_id);
CREATE INDEX idx_items_seller ON fact_order_items (seller_id);
CREATE INDEX idx_items_order ON fact_order_items (order_id);
CREATE INDEX idx_payments_order ON fact_order_payments (order_id);

COMMENT ON TABLE dim_date IS 'Dimension: Calendar dates from 2016 to 2018 (1,096 days)';
COMMENT ON TABLE dim_geography IS 'Dimension: Zip code prefix geographic centroids (19,015 prefixes)';
COMMENT ON TABLE dim_customer IS 'Dimension: Unique customer entities with lifetime metrics (96,096 entities)';
COMMENT ON TABLE dim_seller IS 'Dimension: Marketplace merchants (3,095 sellers)';
COMMENT ON TABLE dim_product IS 'Dimension: Products with Portuguese and English categories (32,951 products)';
COMMENT ON TABLE fact_order_delivery IS 'Fact: Order-level delivery milestones, SLA classifications, and reviews (99,441 orders)';
COMMENT ON TABLE fact_order_items IS 'Fact: Item revenue and shipping burden (112,650 items)';
COMMENT ON TABLE fact_order_payments IS 'Fact: Payment transactions (103,886 payments)';
