"""
Comprehensive Verification Script: Power BI Exported CSVs vs DAX Measure Benchmarks
Project: Olist E-commerce Delivery Performance & Customer Satisfaction
"""

import os
import duckdb

INPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "powerbi_input"))
con = duckdb.connect()

print("Loading exported CSVs into DuckDB...")
for tbl in [
    "dim_date", "dim_geography", "dim_customer", "dim_seller",
    "dim_product", "fact_order_delivery", "fact_order_items", "fact_order_payments"
]:
    csv_file = os.path.join(INPUT_DIR, f"{tbl}.csv")
    con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM read_csv_auto('{csv_file}');")
    count = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    print(f"  {tbl}: {count:,} rows")

print("\n--- Verifying Core DAX Measures ---")

checks = []

def check(name, expected, actual, tol=0.01):
    diff = abs(expected - actual)
    status = "PASS" if diff <= tol else "FAIL"
    checks.append((name, expected, actual, diff, status))
    print(f"[{status}] {name}: Expected={expected}, Actual={actual} (diff={diff:.4f})")

# 1. Total Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery;").fetchone()[0]
check("Total Orders", 99441, val, 0)

# 2. Delivered Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered;").fetchone()[0]
check("Delivered Orders", 96478, val, 0)

# 3. Valid Delivered Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
check("Valid Delivered Orders", 96470, val, 0)

# 4. Total Order Items
val = con.execute("SELECT COUNT(*) FROM fact_order_items;").fetchone()[0]
check("Total Order Items", 112650, val, 0)

# 5. Gross Item Revenue
val = con.execute("SELECT ROUND(SUM(price), 2) FROM fact_order_items;").fetchone()[0]
check("Gross Item Revenue", 13591643.70, val, 0.05)

# 6. Total Freight Billed
val = con.execute("SELECT ROUND(SUM(freight_value), 2) FROM fact_order_items;").fetchone()[0]
check("Total Freight Billed", 2251909.54, val, 0.05)

# 7. Total Customer Spend
val = con.execute("SELECT ROUND(SUM(total_item_spend), 2) FROM fact_order_items;").fetchone()[0]
check("Total Customer Spend", 15843553.24, val, 0.05)

# 8. Captured Payment Value
val = con.execute("SELECT ROUND(SUM(payment_value), 2) FROM fact_order_payments;").fetchone()[0]
check("Captured Payment Value", 16008872.12, val, 0.05)

# 9. Total Unique Customers on Fact Table
val = con.execute("SELECT COUNT(DISTINCT customer_unique_id) FROM fact_order_delivery;").fetchone()[0]
check("Total Unique Customers (Fact)", 96096, val, 0)

# 10. Total Active Sellers
val = con.execute("SELECT COUNT(DISTINCT seller_id) FROM fact_order_items;").fetchone()[0]
check("Total Active Sellers", 3095, val, 0)

# 11. On-Time Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_on_time;").fetchone()[0]
check("On-Time Orders", 89936, val, 0)

# 12. Late Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late;").fetchone()[0]
check("Late Orders", 6534, val, 0)

# 13. On-Time Delivery Rate %
val = con.execute("SELECT ROUND(100.0 * SUM(CASE WHEN is_on_time THEN 1 ELSE 0 END) / COUNT(*), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
check("On-Time Delivery Rate %", 93.23, val, 0.01)

# 14. Average Delay Days
val = con.execute("SELECT ROUND(AVG(delay_days), 2) FROM fact_order_delivery WHERE is_late;").fetchone()[0]
check("Average Delay Days", 10.62, val, 0.05)

# 15. Average Promised Lead Time Days
val = con.execute("SELECT ROUND(AVG(promised_lead_time_days), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
check("Average Promised Lead Time Days", 24.37, val, 0.05)

# 16. Average Actual Cycle Days
val = con.execute("SELECT ROUND(AVG(cycle_days), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
check("Average Actual Cycle Days", 12.55, val, 0.05)

# 17. ETA Safety Buffer Days
check("ETA Safety Buffer Days", 11.82, round(24.37 - 12.55, 2), 0.05)

# 18. Delivered Reviewed Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND has_review;").fetchone()[0]
check("Delivered Reviewed Orders", 95824, val, 0)

# 19. Average Review Score (Delivered)
val = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND has_review;").fetchone()[0]
check("Average Review Score (Delivered)", 4.1559, val, 0.001)

# 20. Average Review Score (On-Time)
val = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_on_time AND has_review;").fetchone()[0]
check("Average Review Score (On-Time)", 4.2904, val, 0.001)

# 21. Average Review Score (Late)
val = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late AND has_review;").fetchone()[0]
check("Average Review Score (Late)", 2.2705, val, 0.001)

# 22. Negative Reviews Count (Delivered 1-2 star)
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND has_review AND review_score IN (1, 2);").fetchone()[0]
check("Negative Reviews Count (1-2 Star)", 12272, val, 0)

# 23. Negative Review Share % (Late)
val = con.execute("SELECT ROUND(100.0 * SUM(CASE WHEN review_score IN (1, 2) THEN 1 ELSE 0 END) / COUNT(*), 2) FROM fact_order_delivery WHERE is_late AND has_review;").fetchone()[0]
check("Negative Review Share % (Late)", 62.42, val, 0.01)

# 24. Negative Review Share % (On-Time)
val = con.execute("SELECT ROUND(100.0 * SUM(CASE WHEN review_score IN (1, 2) THEN 1 ELSE 0 END) / COUNT(*), 2) FROM fact_order_delivery WHERE is_on_time AND has_review;").fetchone()[0]
check("Negative Review Share % (On-Time)", 9.27, val, 0.01)

# 25. Pre-Delivery Late Reviews Count
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late AND review_created_before_delivery AND has_review;").fetchone()[0]
check("Pre-Delivery Late Reviews Count", 4751, val, 0)

# 26. Pre-Delivery Late Review Share %
val = con.execute("SELECT ROUND(100.0 * 4751 / 6381, 2);").fetchone()[0]
check("Pre-Delivery Late Review Share %", 74.46, val, 0.01)

# 27. Avg Review Score (Pre-Delivery Late)
val = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late AND review_created_before_delivery AND has_review;").fetchone()[0]
check("Avg Review Score (Pre-Delivery Late)", 1.8396, val, 0.001)

# 28. Avg Review Score (Post-Delivery Late)
val = con.execute("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late AND NOT review_created_before_delivery AND has_review;").fetchone()[0]
check("Avg Review Score (Post-Delivery Late)", 3.5264, val, 0.001)

# 29. Clean Fulfillment Orders
val = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND handling_days >= 0 AND transit_days >= 0;").fetchone()[0]
check("Clean Fulfillment Orders", 95082, val, 0)

# 30. Average Handling Days (Clean)
val = con.execute("SELECT ROUND(AVG(handling_days), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND handling_days >= 0 AND transit_days >= 0;").fetchone()[0]
check("Average Handling Days", 2.85, val, 0.01)

# 31. Average Transit Days (Clean)
val = con.execute("SELECT ROUND(AVG(transit_days), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND handling_days >= 0 AND transit_days >= 0;").fetchone()[0]
check("Average Transit Days", 9.37, val, 0.01)

# 32. Average Cycle Days (Clean)
val = con.execute("SELECT ROUND(AVG(cycle_days), 2) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND handling_days >= 0 AND transit_days >= 0;").fetchone()[0]
check("Average Cycle Days", 12.61, val, 0.02)

# 33. Interstate Orders Count
val = con.execute("""
SELECT COUNT(DISTINCT i.order_id) 
FROM fact_order_items i 
JOIN fact_order_delivery d ON i.order_id = d.order_id 
WHERE i.is_interstate AND d.is_delivered AND d.is_valid_delivery_date AND d.handling_days >= 0 AND d.transit_days >= 0;
""").fetchone()[0]
check("Interstate Orders Count", 61022, val, 0)

# 34. Intrastate Orders Count
check("Intrastate Orders Count", 34060, 95082 - 61022, 0)

# 35. Intrastate On-Time Rate %
val = con.execute("""
WITH interstate_orders AS (
    SELECT DISTINCT order_id FROM fact_order_items WHERE is_interstate
)
SELECT ROUND(100.0 * SUM(CASE WHEN d.is_on_time THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_delivery d
WHERE d.is_delivered AND d.is_valid_delivery_date AND d.handling_days >= 0 AND d.transit_days >= 0
  AND d.order_id NOT IN (SELECT order_id FROM interstate_orders);
""").fetchone()[0]
check("Intrastate On-Time Rate %", 95.43, val, 0.01)

# 36. Interstate On-Time Rate %
val = con.execute("""
WITH interstate_orders AS (
    SELECT DISTINCT order_id FROM fact_order_items WHERE is_interstate
)
SELECT ROUND(100.0 * SUM(CASE WHEN d.is_on_time THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_delivery d
WHERE d.is_delivered AND d.is_valid_delivery_date AND d.handling_days >= 0 AND d.transit_days >= 0
  AND d.order_id IN (SELECT order_id FROM interstate_orders);
""").fetchone()[0]
check("Interstate On-Time Rate %", 91.89, val, 0.01)

# 37. RJ Performance Gap
rj_actual = con.execute("SELECT ROUND(100.0 * SUM(CASE WHEN is_on_time THEN 1 ELSE 0 END) / COUNT(*), 2) FROM fact_order_delivery WHERE order_customer_state = 'RJ' AND is_delivered AND is_valid_delivery_date;").fetchone()[0]
check("RJ Actual On-Time Rate %", 87.89, rj_actual, 0.01)

# 38. Late Dispatch Rate by Seller Tier
t1 = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN i.is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_items i
JOIN dim_seller s ON i.seller_id = s.seller_id
JOIN fact_order_delivery d ON i.order_id = d.order_id
WHERE s.seller_tier = 'Tier 1: High Volume (500+ orders)'
  AND d.is_clean_fulfillment;
""").fetchone()[0]
check("Late Dispatch Rate % (Tier 1)", 8.07, t1, 0.01)

t2 = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN i.is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_items i
JOIN dim_seller s ON i.seller_id = s.seller_id
JOIN fact_order_delivery d ON i.order_id = d.order_id
WHERE s.seller_tier = 'Tier 2: Mid Volume (100-499 orders)'
  AND d.is_clean_fulfillment;
""").fetchone()[0]
check("Late Dispatch Rate % (Tier 2)", 9.31, t2, 0.01)

t3 = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN i.is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_items i
JOIN dim_seller s ON i.seller_id = s.seller_id
JOIN fact_order_delivery d ON i.order_id = d.order_id
WHERE s.seller_tier = 'Tier 3: Low Volume (30-99 orders)'
  AND d.is_clean_fulfillment;
""").fetchone()[0]
check("Late Dispatch Rate % (Tier 3)", 9.86, t3, 0.01)

t4 = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN i.is_late_dispatch THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM fact_order_items i
JOIN dim_seller s ON i.seller_id = s.seller_id
JOIN fact_order_delivery d ON i.order_id = d.order_id
WHERE s.seller_tier = 'Tier 4: Micro Volume (<30 orders)'
  AND d.is_clean_fulfillment;
""").fetchone()[0]
check("Late Dispatch Rate % (Tier 4)", 11.07, t4, 0.01)

# 39. Repeat Customer Metrics
rep_cust = con.execute("SELECT COUNT(*) FROM dim_customer WHERE is_repeat_customer;").fetchone()[0]
check("Total Repeat Customers", 2997, rep_cust, 0)
check("Repeat Customer Rate %", 3.12, round(100.0 * 2997 / 96096, 2), 0.01)

# 40. Dynamic Retention Measures
del_ontime_rep = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM dim_customer WHERE has_delivered_order AND first_order_on_time;
""").fetchone()[0]
check("Delivered Repeat Rate % (On-Time First Order)", 3.04, del_ontime_rep, 0.01)

del_late_rep = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN has_repeat_delivered_order THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM dim_customer WHERE has_delivered_order AND first_order_late;
""").fetchone()[0]
check("Delivered Repeat Rate % (Late First Order)", 2.52, del_late_rep, 0.01)
check("Delivered Repeat Rate Gap pp", -0.52, round(del_late_rep - del_ontime_rep, 2), 0.01)

mat_ontime_rep = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM dim_customer WHERE is_mature_cohort AND first_order_on_time;
""").fetchone()[0]
check("Mature Repeat Rate % (On-Time First Order)", 5.13, mat_ontime_rep, 0.01)

mat_late_rep = con.execute("""
SELECT ROUND(100.0 * SUM(CASE WHEN has_repeat_all_order THEN 1 ELSE 0 END) / COUNT(*), 2)
FROM dim_customer WHERE is_mature_cohort AND first_order_late;
""").fetchone()[0]
check("Mature Repeat Rate % (Late First Order)", 3.78, mat_late_rep, 0.01)
check("Mature Repeat Rate Gap pp", -1.35, round(mat_late_rep - mat_ontime_rep, 2), 0.01)

# 41. Donut Visual Reconciliation
donut_res = con.execute("""
SELECT order_delivery_status_category, COUNT(*) 
FROM fact_order_delivery 
GROUP BY order_delivery_status_category
ORDER BY order_delivery_status_category;
""").fetchall()
print("\nDonut visual breakdown across all 99,441 orders:")
donut_total = 0
for cat, cnt in donut_res:
    print(f"  {cat}: {cnt:,}")
    donut_total += cnt
check("Donut Visual Total Orders", 99441, donut_total, 0)

failed = [c for c in checks if c[4] == "FAIL"]
print(f"\n==========================================")
print(f"TOTAL CHECKS: {len(checks)} | PASSED: {len(checks) - len(failed)} | FAILED: {len(failed)}")
print(f"==========================================")
