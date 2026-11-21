import duckdb
import os
import json

RAW_DIR = r"../../data/raw"
JSON_PATH = r"../../data/processed\profiling_results.json"

with open(JSON_PATH) as f:
    control_data = json.load(f)
ct = control_data["control_totals"]
dur_clean = control_data["delivery_sla"]["duration_stats_clean"]
h1 = control_data["h1_satisfaction_analysis"]

con = duckdb.connect()

# Load raw tables directly from CSV
con.execute(f"CREATE TABLE raw_customers AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_customers_dataset.csv');")
con.execute(f"CREATE TABLE raw_geolocation AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_geolocation_dataset.csv');")
con.execute(f"CREATE TABLE raw_orders AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_orders_dataset.csv');")
con.execute(f"CREATE TABLE raw_order_items AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_order_items_dataset.csv');")
con.execute(f"CREATE TABLE raw_order_payments AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_order_payments_dataset.csv');")
con.execute(f"CREATE TABLE raw_order_reviews AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_order_reviews_dataset.csv');")
con.execute(f"CREATE TABLE raw_products AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_products_dataset.csv');")
con.execute(f"CREATE TABLE raw_sellers AS SELECT * FROM read_csv_auto('{RAW_DIR}/olist_sellers_dataset.csv');")
con.execute(f"CREATE TABLE raw_product_category_name_translation AS SELECT * FROM read_csv_auto('{RAW_DIR}/product_category_name_translation.csv');")

print("Loaded all raw CSVs into DuckDB.")

# Build dim_date
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
FROM generate_series(DATE '2016-01-01', DATE '2018-12-31', INTERVAL 1 DAY) AS t(d);
""")

# Build dim_customer
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
""")

# Build fact_order_delivery
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
)
SELECT 
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    CAST(o.order_purchase_timestamp AS DATE) AS order_purchase_date,
    CAST(o.order_delivered_customer_date AS DATE) AS order_delivered_customer_date_only,
    CAST(o.order_estimated_delivery_date AS DATE) AS order_estimated_delivery_date_only,
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
    (o.order_delivered_carrier_date < o.order_purchase_timestamp) AS carrier_before_purchase,
    (o.order_delivered_carrier_date < o.order_approved_at) AS carrier_before_approved,
    (o.order_delivered_customer_date < o.order_purchase_timestamp) AS delivery_before_purchase,
    (o.order_delivered_customer_date < o.order_delivered_carrier_date) AS delivery_before_carrier,
    (o.order_delivered_customer_date < o.order_approved_at) AS delivery_before_approved,
    COALESCE(o.order_delivered_carrier_date < o.order_approved_at, FALSE) AS has_negative_handling,
    COALESCE(o.order_delivered_customer_date < o.order_delivered_carrier_date, FALSE) AS has_negative_transit,
    (o.order_purchase_timestamp >= '2017-01-01 00:00:00' AND o.order_purchase_timestamp <= '2018-08-31 23:59:59') AS is_steady_state_window,
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
LEFT JOIN dedup_reviews r ON o.order_id = r.order_id AND r.rn = 1;
""")

# Build fact_order_items
con.execute("""
CREATE TABLE fact_order_items AS
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
    (c.customer_state <> s.seller_state) AS is_interstate
FROM raw_order_items i
JOIN raw_orders o ON i.order_id = o.order_id
JOIN raw_customers c ON o.customer_id = c.customer_id
JOIN raw_sellers s ON i.seller_id = s.seller_id;
""")

print("Dimensions and Fact tables created.")

# Test checks
print("\n--- RUNNING RECONCILIATION CHECKS IN DUCKDB ---")
res_orders = con.execute("SELECT COUNT(*) FROM fact_order_delivery").fetchone()[0]
print(f"Total orders: {res_orders} (Expected: {ct['total_orders']}) -> {'PASS' if res_orders == ct['total_orders'] else 'FAIL'}")

res_items = con.execute("SELECT COUNT(*) FROM fact_order_items").fetchone()[0]
print(f"Total items: {res_items} (Expected: {ct['total_order_items']}) -> {'PASS' if res_items == ct['total_order_items'] else 'FAIL'}")

res_rev = con.execute("SELECT ROUND(SUM(price), 2) FROM fact_order_items").fetchone()[0]
print(f"Gross Item Revenue: {res_rev} (Expected: {ct['total_item_revenue_brl']}) -> {'PASS' if res_rev == ct['total_item_revenue_brl'] else 'FAIL'}")

res_freight = con.execute("SELECT ROUND(SUM(freight_value), 2) FROM fact_order_items").fetchone()[0]
print(f"Total Freight: {res_freight} (Expected: {ct['total_freight_value_brl']}) -> {'PASS' if res_freight == ct['total_freight_value_brl'] else 'FAIL'}")

res_deliv = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE").fetchone()[0]
print(f"Delivered orders with date: {res_deliv} (Expected: {ct['delivered_orders_with_date']}) -> {'PASS' if res_deliv == ct['delivered_orders_with_date'] else 'FAIL'}")

res_ontime = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_on_time = TRUE").fetchone()[0]
print(f"On-time delivered orders: {res_ontime} (Expected: {ct['date_level_ontime_delivered_orders']}) -> {'PASS' if res_ontime == ct['date_level_ontime_delivered_orders'] else 'FAIL'}")

res_late = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late = TRUE").fetchone()[0]
print(f"Late delivered orders: {res_late} (Expected: {ct['date_level_late_delivered_orders']}) -> {'PASS' if res_late == ct['date_level_late_delivered_orders'] else 'FAIL'}")

res_ontime_rate = con.execute("SELECT ROUND(COUNT(CASE WHEN is_on_time THEN 1 END) * 100.0 / COUNT(CASE WHEN is_delivered AND is_valid_delivery_date THEN 1 END), 4) FROM fact_order_delivery").fetchone()[0]
print(f"On-time rate: {res_ontime_rate}% (Expected: {ct['date_level_ontime_delivery_rate_pct']}%) -> {'PASS' if res_ontime_rate == ct['date_level_ontime_delivery_rate_pct'] else 'FAIL'}")

res_late_rate = con.execute("SELECT ROUND(COUNT(CASE WHEN is_late THEN 1 END) * 100.0 / COUNT(CASE WHEN is_delivered AND is_valid_delivery_date THEN 1 END), 4) FROM fact_order_delivery").fetchone()[0]
print(f"Late rate: {res_late_rate}% (Expected: {ct['date_level_late_delivery_rate_pct']}%) -> {'PASS' if res_late_rate == ct['date_level_late_delivery_rate_pct'] else 'FAIL'}")

res_reviews = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE has_review = TRUE").fetchone()[0]
print(f"Deduplicated reviews count: {res_reviews} (Expected: {ct['deduplicated_order_reviews_count']}) -> {'PASS' if res_reviews == ct['deduplicated_order_reviews_count'] else 'FAIL'}")

res_avg_ontime_rev = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_on_time = TRUE AND has_review = TRUE").fetchone()[0]
print(f"On-time avg review score: {res_avg_ontime_rev} (Expected: {ct['date_level_ontime_avg_review_score']}) -> {'PASS' if res_avg_ontime_rev == ct['date_level_ontime_avg_review_score'] else 'FAIL'}")

res_avg_late_rev = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE").fetchone()[0]
print(f"Late avg review score: {res_avg_late_rev} (Expected: {ct['date_level_late_avg_review_score']}) -> {'PASS' if res_avg_late_rev == ct['date_level_late_avg_review_score'] else 'FAIL'}")

res_early_late_rev_cnt = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE AND review_created_before_delivery = TRUE").fetchone()[0]
print(f"Late early reviews count: {res_early_late_rev_cnt} (Expected: {h1['late_review_timing_split']['reviewed_before_delivery']['N']}) -> {'PASS' if res_early_late_rev_cnt == h1['late_review_timing_split']['reviewed_before_delivery']['N'] else 'FAIL'}")

res_early_late_rev_score = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE AND review_created_before_delivery = TRUE").fetchone()[0]
print(f"Late early reviews avg score: {res_early_late_rev_score} (Expected: {h1['late_review_timing_split']['reviewed_before_delivery']['avg_score']}) -> {'PASS' if res_early_late_rev_score == h1['late_review_timing_split']['reviewed_before_delivery']['avg_score'] else 'FAIL'}")

res_clean_handling = con.execute("SELECT ROUND(AVG(handling_days), 4) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE AND handling_days >= 0").fetchone()[0]
print(f"Clean handling mean: {res_clean_handling} (Expected: {dur_clean['avg_handling_clean_days']}) -> {'PASS' if res_clean_handling == dur_clean['avg_handling_clean_days'] else 'FAIL'}")

res_clean_transit = con.execute("SELECT ROUND(AVG(transit_days), 4) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE AND transit_days >= 0 AND handling_days >= 0").fetchone()[0]
print(f"Clean transit mean: {res_clean_transit} (Expected: {dur_clean['transit_excluding_all_anomalies_days']}) -> {'PASS' if res_clean_transit == dur_clean['transit_excluding_all_anomalies_days'] else 'FAIL'}")
