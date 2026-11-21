"""
Export Warehouse Derived Star Schema Tables to CSV for Power BI Desktop
Project: Olist E-commerce Delivery Performance & Customer Satisfaction
Version: 2.0.0
Author: Independent Portfolio Project

Generates portable CSV exports of all 8 analytical star schema tables directly into
data/processed/powerbi_input/, enabling Power BI Desktop (.pbix) to ingest the
pre-cleaned star schema via Power Query M without requiring an active PostgreSQL connection.

Design Specifications:
- dim_date: Spans 2016-01-01 to 2018-10-17 (exact dataset max date; never TODAY()).
- dim_customer: Enriched with cohort tracking (first delivered order outcome, repeat delivered orders, mature cohort).
- dim_seller: Enriched with lifetime orders and seller volume tiers (Tier 1 to 4).
- fact_order_delivery: Enriched with promised lead time, order-grain route distance, order distance band, and delivery status category.
- fact_order_items: Enriched with freight per kg, late dispatch compliance flag, and item distance band.
"""

import os
import duckdb

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw"))
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed", "powerbi_input"))
os.makedirs(OUT_DIR, exist_ok=True)

con = duckdb.connect()

print("Loading raw CSV files into staging...")
for tbl, fname in [
    ("raw_customers", "olist_customers_dataset.csv"),
    ("raw_geolocation", "olist_geolocation_dataset.csv"),
    ("raw_orders", "olist_orders_dataset.csv"),
    ("raw_order_items", "olist_order_items_dataset.csv"),
    ("raw_order_payments", "olist_order_payments_dataset.csv"),
    ("raw_order_reviews", "olist_order_reviews_dataset.csv"),
    ("raw_products", "olist_products_dataset.csv"),
    ("raw_sellers", "olist_sellers_dataset.csv"),
    ("raw_product_category_name_translation", "product_category_name_translation.csv")
]:
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{RAW_DIR}/{fname}');")

print("Building dimensional star schema...")

# 1. dim_date ending at 2018-10-17 (max date in dataset)
con.execute("""
CREATE TABLE dim_date AS
SELECT 
    CAST(strftime(d, '%Y%m%d') AS INTEGER) AS date_key,
    CAST(d AS DATE) AS full_date,
    CAST(EXTRACT(YEAR FROM d) AS INTEGER) AS year_num,
    CAST(EXTRACT(QUARTER FROM d) AS INTEGER) AS quarter_num,
    'Q' || CAST(EXTRACT(QUARTER FROM d) AS VARCHAR) AS quarter_name,
    CAST(EXTRACT(MONTH FROM d) AS INTEGER) AS month_num,
    strftime(d, '%B') AS month_name,
    strftime(d, '%Y-%m') AS year_month,
    CAST(EXTRACT(WEEK FROM d) AS INTEGER) AS week_of_year,
    CAST(EXTRACT(DAY FROM d) AS INTEGER) AS day_of_month,
    CAST(EXTRACT(ISODOW FROM d) AS INTEGER) AS day_of_week,
    strftime(d, '%A') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series(DATE '2016-01-01', DATE '2018-10-17', INTERVAL 1 DAY) AS t(d);
""")

# 2. dim_geography
con.execute("""
CREATE TABLE dim_geography AS
WITH geo_stats AS (
    SELECT 
        geolocation_zip_code_prefix AS zip_code_prefix,
        MEDIAN(geolocation_lat) AS median_lat,
        MEDIAN(geolocation_lng) AS median_lng,
        COUNT(*) AS coordinate_count
    FROM raw_geolocation
    GROUP BY geolocation_zip_code_prefix
),
geo_city_mode AS (
    SELECT 
        geolocation_zip_code_prefix AS zip_code_prefix,
        geolocation_city,
        geolocation_state,
        ROW_NUMBER() OVER (
            PARTITION BY geolocation_zip_code_prefix 
            ORDER BY COUNT(*) DESC, geolocation_city ASC
        ) AS rn
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
""")

# 3. dim_customer (Enriched with retention & cohort tracking)
con.execute("""
CREATE TABLE dim_customer AS
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
),
delivered_orders AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
        CAST(o.order_delivered_customer_date AS DATE) AS delivered_date,
        CAST(o.order_estimated_delivery_date AS DATE) AS estimated_date,
        (CAST(o.order_delivered_customer_date AS DATE) <= CAST(o.order_estimated_delivery_date AS DATE)) AS is_ontime,
        (CAST(o.order_delivered_customer_date AS DATE) > CAST(o.order_estimated_delivery_date AS DATE)) AS is_late,
        ROW_NUMBER() OVER (
            PARTITION BY c.customer_unique_id 
            ORDER BY o.order_purchase_timestamp ASC, o.order_id ASC
        ) AS rn_del
    FROM raw_orders o
    JOIN raw_customers c ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
),
cust_del_agg AS (
    SELECT 
        customer_unique_id,
        COUNT(DISTINCT order_id) AS total_delivered_orders,
        MAX(CASE WHEN rn_del = 1 THEN order_id END) AS first_delivered_order_id,
        MAX(CASE WHEN rn_del = 1 THEN order_purchase_date END) AS first_delivered_order_date,
        MAX(CASE WHEN rn_del = 1 THEN is_ontime END) AS first_order_on_time,
        MAX(CASE WHEN rn_del = 1 THEN is_late END) AS first_order_late
    FROM delivered_orders
    GROUP BY customer_unique_id
)
SELECT 
    a.customer_unique_id,
    l.customer_city AS primary_city,
    l.customer_state AS primary_state,
    l.customer_zip_code_prefix AS primary_zip_code_prefix,
    a.first_order_timestamp,
    a.last_order_timestamp,
    a.lifetime_orders,
    (a.lifetime_orders >= 2) AS is_repeat_customer,
    (d.customer_unique_id IS NOT NULL) AS has_delivered_order,
    d.first_delivered_order_id,
    d.first_delivered_order_date,
    COALESCE(d.first_order_on_time, FALSE) AS first_order_on_time,
    COALESCE(d.first_order_late, FALSE) AS first_order_late,
    COALESCE(d.total_delivered_orders, 0) AS total_delivered_orders,
    (COALESCE(d.total_delivered_orders, 0) >= 2) AS has_repeat_delivered_order,
    (a.lifetime_orders >= 2) AS has_repeat_all_order,
    (d.first_delivered_order_date IS NOT NULL AND d.first_delivered_order_date < DATE '2017-10-01') AS is_mature_cohort
FROM cust_agg a
JOIN cust_orders l ON a.customer_unique_id = l.customer_unique_id AND l.rn_latest = 1
LEFT JOIN cust_del_agg d ON a.customer_unique_id = d.customer_unique_id;
""")

# 4. dim_seller (Enriched with lifetime orders and seller volume tiers)
con.execute("""
CREATE TABLE dim_seller AS
WITH seller_orders AS (
    SELECT 
        s.seller_id,
        COUNT(DISTINCT i.order_id) AS seller_lifetime_orders
    FROM raw_sellers s
    LEFT JOIN raw_order_items i ON s.seller_id = i.seller_id
    GROUP BY s.seller_id
)
SELECT 
    s.seller_id,
    s.seller_zip_code_prefix,
    s.seller_city,
    s.seller_state,
    COALESCE(so.seller_lifetime_orders, 0) AS seller_lifetime_orders,
    CASE 
        WHEN COALESCE(so.seller_lifetime_orders, 0) >= 500 THEN 'Tier 1: High Volume (500+ orders)'
        WHEN COALESCE(so.seller_lifetime_orders, 0) >= 100 THEN 'Tier 2: Mid Volume (100-499 orders)'
        WHEN COALESCE(so.seller_lifetime_orders, 0) >= 30  THEN 'Tier 3: Low Volume (30-99 orders)'
        ELSE 'Tier 4: Micro Volume (<30 orders)'
    END AS seller_tier
FROM raw_sellers s
LEFT JOIN seller_orders so ON s.seller_id = so.seller_id;
""")

# 5. dim_product
con.execute("""
CREATE TABLE dim_product AS
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
""")

# Preliminary: item route distances for order aggregation
con.execute("""
CREATE TABLE staging_item_distances AS
SELECT 
    i.order_id,
    i.order_item_id,
    i.product_id,
    i.seller_id,
    c.customer_unique_id,
    CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
    i.shipping_limit_date,
    i.price,
    i.freight_value,
    (i.price + i.freight_value) AS total_item_spend,
    ROUND(i.freight_value / NULLIF(i.price, 0), 4) AS freight_to_price_ratio,
    c.customer_zip_code_prefix AS customer_zip_prefix,
    s.seller_zip_code_prefix AS seller_zip_prefix,
    CASE 
        WHEN g_cust.median_lat IS NOT NULL AND g_sell.median_lat IS NOT NULL THEN
            ROUND((
                2 * 6371.0 * ASIN(SQRT(
                    POWER(SIN(RADIANS((g_cust.median_lat - g_sell.median_lat) / 2.0)), 2) +
                    COS(RADIANS(g_sell.median_lat)) * COS(RADIANS(g_cust.median_lat)) *
                    POWER(SIN(RADIANS((g_cust.median_lng - g_sell.median_lng) / 2.0)), 2)
                ))
            ), 2)
        ELSE NULL 
    END AS route_distance_km,
    (c.customer_state <> s.seller_state) AS is_interstate,
    p.product_weight_g,
    ROUND(i.freight_value / NULLIF(p.product_weight_g / 1000.0, 0), 4) AS freight_per_kg,
    (o.order_delivered_carrier_date > i.shipping_limit_date) AS is_late_dispatch
FROM raw_order_items i
JOIN raw_orders o ON i.order_id = o.order_id
JOIN raw_customers c ON o.customer_id = c.customer_id
JOIN raw_sellers s ON i.seller_id = s.seller_id
LEFT JOIN raw_products p ON i.product_id = p.product_id
LEFT JOIN dim_geography g_cust ON c.customer_zip_code_prefix = g_cust.zip_code_prefix
LEFT JOIN dim_geography g_sell ON s.seller_zip_code_prefix = g_sell.zip_code_prefix;
""")

# 6. fact_order_delivery (Enriched with promised lead time, order distance band, status category)
con.execute("""
CREATE TABLE fact_order_delivery AS
WITH dedup_reviews AS (
    SELECT 
        order_id,
        review_id,
        review_score,
        CAST(review_creation_date AS DATE) AS review_creation_date,
        review_answer_timestamp,
        ROW_NUMBER() OVER (
            PARTITION BY order_id 
            ORDER BY review_answer_timestamp DESC, review_creation_date DESC, review_id DESC
        ) AS rn
    FROM raw_order_reviews
),
order_distance_agg AS (
    SELECT 
        order_id,
        MAX(route_distance_km) AS order_route_distance_km
    FROM staging_item_distances
    GROUP BY order_id
)
SELECT 
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_state AS order_customer_state,
    c.customer_city AS order_customer_city,
    c.customer_zip_code_prefix AS order_customer_zip_prefix,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
    CAST(o.order_delivered_customer_date AS DATE) AS order_delivered_customer_date_only,
    CAST(o.order_estimated_delivery_date AS DATE) AS order_estimated_delivery_date_only,
    CAST(CAST(o.order_estimated_delivery_date AS DATE) - CAST(o.order_purchase_timestamp AS DATE) AS INTEGER) AS promised_lead_time_days,
    (o.order_status = 'delivered') AS is_delivered,
    (o.order_delivered_customer_date IS NOT NULL) AS is_valid_delivery_date,
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (CAST(o.order_delivered_customer_date AS DATE) <= CAST(o.order_estimated_delivery_date AS DATE))
        ELSE FALSE 
    END AS is_on_time,
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (CAST(o.order_delivered_customer_date AS DATE) > CAST(o.order_estimated_delivery_date AS DATE))
        ELSE FALSE 
    END AS is_late,
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL 
             AND (CAST(o.order_delivered_customer_date AS DATE) > CAST(o.order_estimated_delivery_date AS DATE))
        THEN CAST(CAST(o.order_delivered_customer_date AS DATE) - CAST(o.order_estimated_delivery_date AS DATE) AS INTEGER)
        ELSE 0 
    END AS delay_days,
    CASE 
        WHEN o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN CAST(CAST(o.order_estimated_delivery_date AS DATE) - CAST(o.order_delivered_customer_date AS DATE) AS INTEGER)
        ELSE NULL 
    END AS estimate_variance_days,
    CASE 
        WHEN o.order_delivered_carrier_date IS NOT NULL AND o.order_approved_at IS NOT NULL
        THEN ROUND(epoch(o.order_delivered_carrier_date - o.order_approved_at) / 86400.0, 4)
        ELSE NULL 
    END AS handling_days,
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL AND o.order_delivered_carrier_date IS NOT NULL
        THEN ROUND(epoch(o.order_delivered_customer_date - o.order_delivered_carrier_date) / 86400.0, 4)
        ELSE NULL 
    END AS transit_days,
    CASE 
        WHEN o.order_delivered_customer_date IS NOT NULL
        THEN ROUND(epoch(o.order_delivered_customer_date - o.order_purchase_timestamp) / 86400.0, 4)
        ELSE NULL 
    END AS cycle_days,
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
    oda.order_route_distance_km,
    CASE 
        WHEN oda.order_route_distance_km IS NULL THEN 'Unknown'
        WHEN oda.order_route_distance_km < 250 THEN '1. Local (<250km)'
        WHEN oda.order_route_distance_km < 500 THEN '2. Regional (250-500km)'
        WHEN oda.order_route_distance_km < 1000 THEN '3. Medium (500-1000km)'
        WHEN oda.order_route_distance_km < 2000 THEN '4. Long (1000-2000km)'
        ELSE '5. Remote (2000km+)'
    END AS order_distance_band,
    CASE 
        WHEN o.order_status <> 'delivered' THEN 'Non-Delivered'
        WHEN o.order_delivered_customer_date IS NULL THEN 'Delivered (Missing Date)'
        WHEN (CAST(o.order_delivered_customer_date AS DATE) <= CAST(o.order_estimated_delivery_date AS DATE)) THEN 'On-Time'
        WHEN (CAST(o.order_delivered_customer_date AS DATE) > CAST(o.order_estimated_delivery_date AS DATE)) THEN 'Late'
        ELSE 'Other'
    END AS order_delivery_status_category,
    r.review_id,
    r.review_score,
    r.review_creation_date,
    r.review_answer_timestamp,
    (r.review_id IS NOT NULL) AS has_review,
    CASE 
        WHEN r.review_id IS NOT NULL AND o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
        THEN (r.review_creation_date < CAST(o.order_delivered_customer_date AS DATE))
        ELSE FALSE 
    END AS review_created_before_delivery
FROM raw_orders o
JOIN raw_customers c ON o.customer_id = c.customer_id
LEFT JOIN dedup_reviews r ON o.order_id = r.order_id AND r.rn = 1
LEFT JOIN order_distance_agg oda ON o.order_id = oda.order_id;
""")

# 7. fact_order_items (Enriched with late dispatch, freight_per_kg, distance band)
con.execute("""
CREATE TABLE fact_order_items AS
SELECT 
    order_id,
    order_item_id,
    product_id,
    seller_id,
    customer_unique_id,
    order_purchase_date,
    shipping_limit_date,
    price,
    freight_value,
    total_item_spend,
    freight_to_price_ratio,
    freight_per_kg,
    is_late_dispatch,
    customer_zip_prefix,
    seller_zip_prefix,
    route_distance_km,
    CASE 
        WHEN route_distance_km IS NULL THEN 'Unknown'
        WHEN route_distance_km < 250 THEN '1. Local (<250km)'
        WHEN route_distance_km < 500 THEN '2. Regional (250-500km)'
        WHEN route_distance_km < 1000 THEN '3. Medium (500-1000km)'
        WHEN route_distance_km < 2000 THEN '4. Long (1000-2000km)'
        ELSE '5. Remote (2000km+)'
    END AS distance_band,
    is_interstate
FROM staging_item_distances;
""")

# 8. fact_order_payments
con.execute("""
CREATE TABLE fact_order_payments AS
SELECT 
    order_id,
    payment_sequential,
    payment_type,
    payment_installments,
    payment_value
FROM raw_order_payments;
""")

print("\nExporting enriched tables to CSV for Power BI ingestion...")
tables = [
    ("dim_date", 1021),
    ("dim_geography", 19015),
    ("dim_customer", 96096),
    ("dim_seller", 3095),
    ("dim_product", 32951),
    ("fact_order_delivery", 99441),
    ("fact_order_items", 112650),
    ("fact_order_payments", 103886)
]

for t, expected_n in tables:
    csv_file = os.path.join(OUT_DIR, f"{t}.csv")
    con.execute(f"COPY {t} TO '{csv_file}' (HEADER, DELIMITER ',');")
    actual_n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    status = "PASS" if actual_n == expected_n else f"FAIL (expected {expected_n})"
    print(f"  [{status}] {t}: {actual_n:,} rows -> {csv_file}")

print("\nAll 8 enriched tables exported successfully to data/processed/powerbi_input/.")
