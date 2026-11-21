import os
import duckdb

RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
con = duckdb.connect()

for tbl, fname in [
    ("raw_customers", "olist_customers_dataset.csv"),
    ("raw_orders", "olist_orders_dataset.csv"),
    ("raw_order_items", "olist_order_items_dataset.csv"),
    ("raw_sellers", "olist_sellers_dataset.csv"),
    ("raw_products", "olist_products_dataset.csv"),
    ("raw_geolocation", "olist_geolocation_dataset.csv")
]:
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{RAW_DIR}/{fname}');")

print("--- Testing dim_customer logic ---")
con.execute("""
CREATE TABLE test_dim_customer AS
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

print("dim_customer total rows:", con.execute("SELECT COUNT(*) FROM test_dim_customer").fetchone()[0])
print("dim_customer has_delivered_order:", con.execute("SELECT COUNT(*) FROM test_dim_customer WHERE has_delivered_order").fetchone()[0])

print("Full cohort repeat breakdown:")
res_full = con.execute("""
SELECT 
    CASE WHEN first_order_on_time THEN 'On-Time' WHEN first_order_late THEN 'Late' ELSE 'Other' END AS first_status,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) AS repeat_delivered_cust,
    ROUND(100.0 * SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) / COUNT(*), 4) AS repeat_delivered_pct,
    SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) AS repeat_all_cust,
    ROUND(100.0 * SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) / COUNT(*), 4) AS repeat_all_pct
FROM test_dim_customer
WHERE has_delivered_order
GROUP BY 1 ORDER BY 1;
""").fetchall()
for r in res_full:
    print(" ", r)

print("Mature cohort repeat breakdown (< 2017-10-01):")
res_mature = con.execute("""
SELECT 
    CASE WHEN first_order_on_time THEN 'On-Time' WHEN first_order_late THEN 'Late' ELSE 'Other' END AS first_status,
    COUNT(*) AS total_customers,
    SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) AS repeat_delivered_cust,
    ROUND(100.0 * SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) / COUNT(*), 4) AS repeat_delivered_pct,
    SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) AS repeat_all_cust,
    ROUND(100.0 * SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) / COUNT(*), 4) AS repeat_all_pct
FROM test_dim_customer
WHERE is_mature_cohort
GROUP BY 1 ORDER BY 1;
""").fetchall()
for r in res_mature:
    print(" ", r)

print("\n--- Testing dim_seller logic ---")
con.execute("""
CREATE TABLE test_dim_seller AS
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

print("Seller tier breakdown:")
res_seller = con.execute("""
SELECT seller_tier, COUNT(*) AS seller_count, SUM(seller_lifetime_orders) AS total_orders
FROM test_dim_seller
GROUP BY seller_tier
ORDER BY seller_tier;
""").fetchall()
for r in res_seller:
    print(" ", r)

print("\n--- Testing fact_order_items late dispatch & freight_per_kg ---")
con.execute("""
CREATE TABLE test_items AS
SELECT 
    i.order_id,
    i.order_item_id,
    i.seller_id,
    i.price,
    i.freight_value,
    p.product_weight_g,
    ROUND(i.freight_value / NULLIF(p.product_weight_g / 1000.0, 0), 4) AS freight_per_kg,
    o.order_delivered_carrier_date > i.shipping_limit_date AS is_late_dispatch
FROM raw_order_items i
JOIN raw_orders o ON i.order_id = o.order_id
LEFT JOIN raw_products p ON i.product_id = p.product_id;
""")

print("Late dispatch rate by seller tier:")
res_dispatch = con.execute("""
SELECT 
    s.seller_tier,
    COUNT(*) AS total_items,
    SUM(CASE WHEN ti.is_late_dispatch THEN 1 ELSE 0 END) AS late_dispatch_items,
    ROUND(100.0 * SUM(CASE WHEN ti.is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_dispatch_pct
FROM test_items ti
JOIN test_dim_seller s ON ti.seller_id = s.seller_id
GROUP BY s.seller_tier
ORDER BY s.seller_tier;
""").fetchall()
for r in res_dispatch:
    print(" ", r)
