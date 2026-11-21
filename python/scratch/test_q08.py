import os, duckdb
RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw"))
con = duckdb.connect()

for tbl, fname in [
    ("raw_orders", "olist_orders_dataset.csv"),
    ("raw_order_items", "olist_order_items_dataset.csv"),
    ("raw_sellers", "olist_sellers_dataset.csv")
]:
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{RAW_DIR}/{fname}');")

res = con.execute("""
WITH seller_order_counts AS (
    SELECT 
        seller_id,
        COUNT(DISTINCT order_id) AS seller_lifetime_orders
    FROM raw_order_items
    GROUP BY seller_id
),
seller_order_facts AS (
    SELECT 
        i.order_id,
        i.seller_id,
        soc.seller_lifetime_orders,
        CASE 
            WHEN soc.seller_lifetime_orders >= 500 THEN 'Tier 1: High Volume (500+ orders)'
            WHEN soc.seller_lifetime_orders >= 100 THEN 'Tier 2: Mid Volume (100-499 orders)'
            WHEN soc.seller_lifetime_orders >= 30  THEN 'Tier 3: Low Volume (30-99 orders)'
            ELSE 'Tier 4: Micro Volume (<30 orders)'
        END AS seller_tier,
        (o.order_delivered_carrier_date > i.shipping_limit_date) AS is_late_dispatch
    FROM raw_order_items i
    JOIN seller_order_counts soc ON i.seller_id = soc.seller_id
    JOIN raw_orders o ON i.order_id = o.order_id
    WHERE o.order_status = 'delivered' 
      AND o.order_delivered_customer_date IS NOT NULL
      AND (epoch(o.order_delivered_carrier_date - o.order_approved_at) / 86400.0) >= 0
)
SELECT 
    seller_tier,
    COUNT(*) AS item_rows,
    COUNT(DISTINCT order_id) AS orders_n,
    ROUND(100.0 * SUM(CASE WHEN is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2) AS late_dispatch_pct
FROM seller_order_facts
GROUP BY seller_tier
ORDER BY seller_tier;
""").fetchall()

for r in res:
    print(r)
