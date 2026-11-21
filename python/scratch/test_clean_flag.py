import duckdb

con = duckdb.connect()
con.execute("CREATE TABLE raw_orders AS SELECT * FROM read_csv_auto('data/raw/olist_orders_dataset.csv');")
con.execute("CREATE TABLE raw_items AS SELECT * FROM read_csv_auto('data/raw/olist_order_items_dataset.csv');")
con.execute("CREATE TABLE raw_sellers AS SELECT * FROM read_csv_auto('data/raw/olist_sellers_dataset.csv');")

res = con.execute("""
WITH seller_orders AS (
    SELECT s.seller_id, COUNT(DISTINCT i.order_id) as orders_count
    FROM raw_sellers s
    LEFT JOIN raw_items i ON s.seller_id = i.seller_id
    GROUP BY s.seller_id
),
seller_tiers AS (
    SELECT 
        seller_id,
        CASE 
            WHEN orders_count >= 500 THEN 'Tier 1'
            WHEN orders_count >= 100 THEN 'Tier 2'
            WHEN orders_count >= 30 THEN 'Tier 3'
            ELSE 'Tier 4'
        END as tier
    FROM seller_orders
),
eligible_items AS (
    SELECT 
        t.tier,
        (o.order_delivered_carrier_date > i.shipping_limit_date) as is_late_dispatch
    FROM raw_items i
    JOIN raw_orders o ON i.order_id = o.order_id
    JOIN seller_tiers t ON i.seller_id = t.seller_id
    WHERE o.order_status = 'delivered' 
      AND o.order_delivered_customer_date IS NOT NULL 
      AND o.order_approved_at IS NOT NULL 
      AND o.order_delivered_carrier_date IS NOT NULL 
      AND (o.order_delivered_carrier_date >= o.order_approved_at) 
      AND (o.order_delivered_customer_date >= o.order_delivered_carrier_date)
)
SELECT 
    tier,
    COUNT(*) as total_items,
    SUM(CASE WHEN is_late_dispatch THEN 1 ELSE 0 END) as late_items,
    ROUND(AVG(CASE WHEN is_late_dispatch THEN 1.0 ELSE 0.0 END) * 100, 2) as late_dispatch_pct
FROM eligible_items
GROUP BY tier
ORDER BY tier;
""").fetchall()
print("Late dispatch by tier:")
for r in res:
    print(r)
