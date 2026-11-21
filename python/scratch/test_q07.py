import os, duckdb
RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
con = duckdb.connect()

for tbl, fname in [
    ("raw_customers", "olist_customers_dataset.csv"),
    ("raw_orders", "olist_orders_dataset.csv"),
    ("raw_order_items", "olist_order_items_dataset.csv"),
    ("raw_sellers", "olist_sellers_dataset.csv"),
    ("raw_geolocation", "olist_geolocation_dataset.csv")
]:
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{RAW_DIR}/{fname}');")

con.execute("""
CREATE TABLE geo_stats AS 
SELECT 
    geolocation_zip_code_prefix AS zip_code_prefix,
    MEDIAN(geolocation_lat) AS median_lat,
    MEDIAN(geolocation_lng) AS median_lng
FROM raw_geolocation
GROUP BY geolocation_zip_code_prefix;
""")

con.execute("""
CREATE TABLE order_items_geo AS
SELECT 
    i.order_id,
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
    END AS route_distance_km
FROM raw_order_items i
JOIN raw_orders o ON i.order_id = o.order_id
JOIN raw_customers c ON o.customer_id = c.customer_id
JOIN raw_sellers s ON i.seller_id = s.seller_id
LEFT JOIN geo_stats g_cust ON c.customer_zip_code_prefix = g_cust.zip_code_prefix
LEFT JOIN geo_stats g_sell ON s.seller_zip_code_prefix = g_sell.zip_code_prefix;
""")

res = con.execute("""
WITH order_max_dist AS (
    SELECT order_id, MAX(route_distance_km) AS order_route_distance_km
    FROM order_items_geo
    GROUP BY order_id
),
order_bands AS (
    SELECT 
        o.order_id,
        c.customer_state AS destination_state,
        (CAST(o.order_delivered_customer_date AS DATE) <= CAST(o.order_estimated_delivery_date AS DATE)) AS is_on_time,
        CAST(CAST(o.order_estimated_delivery_date AS DATE) - CAST(o.order_purchase_timestamp AS DATE) AS INTEGER) AS promised_lead_time_days,
        ROUND(epoch(o.order_delivered_customer_date - o.order_purchase_timestamp) / 86400.0, 4) AS actual_cycle_days,
        m.order_route_distance_km,
        CASE 
            WHEN m.order_route_distance_km IS NULL THEN 'Unknown'
            WHEN m.order_route_distance_km < 250 THEN '1. Local (<250km)'
            WHEN m.order_route_distance_km < 500 THEN '2. Regional (250-500km)'
            WHEN m.order_route_distance_km < 1000 THEN '3. Medium (500-1000km)'
            WHEN m.order_route_distance_km < 2000 THEN '4. Long (1000-2000km)'
            ELSE '5. Remote (2000km+)'
        END AS order_distance_band
    FROM raw_orders o
    JOIN raw_customers c ON o.customer_id = c.customer_id
    JOIN order_max_dist m ON o.order_id = m.order_id
    WHERE o.order_status = 'delivered' AND o.order_delivered_customer_date IS NOT NULL
),
global_benchmarks AS (
    SELECT 
        order_distance_band,
        COUNT(*) AS n_orders,
        ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END), 4) AS global_ontime_rate
    FROM order_bands
    GROUP BY order_distance_band
),
state_mix AS (
    SELECT 
        destination_state,
        order_distance_band,
        COUNT(*) AS band_orders,
        COUNT(*)::numeric / SUM(COUNT(*)) OVER (PARTITION BY destination_state)::numeric AS band_weight
    FROM order_bands
    GROUP BY destination_state, order_distance_band
),
state_expected AS (
    SELECT 
        sm.destination_state,
        ROUND(SUM(sm.band_weight * gb.global_ontime_rate) * 100, 2) AS expected_ontime_rate_pct
    FROM state_mix sm
    JOIN global_benchmarks gb ON sm.order_distance_band = gb.order_distance_band
    GROUP BY sm.destination_state
),
state_actual AS (
    SELECT 
        destination_state,
        COUNT(*) AS total_delivered_orders,
        ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) * 100, 2) AS actual_ontime_rate_pct,
        ROUND(AVG(promised_lead_time_days), 1) AS avg_promised_lead_time_days,
        ROUND(AVG(actual_cycle_days), 1) AS avg_actual_cycle_days
    FROM order_bands
    GROUP BY destination_state
)
SELECT 
    sa.destination_state,
    sa.total_delivered_orders,
    sa.actual_ontime_rate_pct,
    se.expected_ontime_rate_pct,
    ROUND(sa.actual_ontime_rate_pct - se.expected_ontime_rate_pct, 2) AS mix_adjusted_performance_gap_pp
FROM state_actual sa
JOIN state_expected se ON sa.destination_state = se.destination_state
WHERE sa.destination_state IN ('SP', 'RJ', 'MA', 'AL', 'AM', 'RO')
ORDER BY sa.total_delivered_orders DESC;
""").fetchall()

for r in res:
    print(r)
