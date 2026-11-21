import os, duckdb
INPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "powerbi_input"))
con = duckdb.connect()

con.execute(f"CREATE TABLE fact_order_delivery AS SELECT * FROM read_csv_auto('{INPUT_DIR}/fact_order_delivery.csv');")

# Check negative reviews
ontime_neg = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_on_time AND has_review AND review_score IN (1, 2);").fetchone()[0]
late_neg = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late AND has_review AND review_score IN (1, 2);").fetchone()[0]
tot_del_neg = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND has_review AND review_score IN (1, 2);").fetchone()[0]
all_neg = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE has_review AND review_score IN (1, 2);").fetchone()[0]

print(f"Negative reviews: ontime={ontime_neg}, late={late_neg}, sum={ontime_neg+late_neg}, tot_del_neg={tot_del_neg}, all_neg={all_neg}")

# Check promised lead time
p1 = con.execute("SELECT AVG(promised_lead_time_days) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
p2 = con.execute("SELECT AVG(epoch(order_estimated_delivery_date - order_purchase_timestamp)/86400.0) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
p3 = con.execute("SELECT AVG(epoch(order_estimated_delivery_date - order_approved_at)/86400.0) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date;").fetchone()[0]
p4 = con.execute("SELECT AVG(CAST(order_estimated_delivery_date_only - order_purchase_date AS INTEGER)) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND handling_days >= 0 AND transit_days >= 0;").fetchone()[0]

print(f"Promised lead time: p1(date diff)={p1:.4f}, p2(ts diff)={p2:.4f}, p3(approved)={p3:.4f}, p4(clean flow)={p4:.4f}")

# Check what profiling_results.json or Q07 says for promised lead time
import json
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "profiling_results.json"))
with open(json_path, "r", encoding="utf-8") as f:
    prof = json.load(f)
if "delivery_sla" in prof:
    print("delivery_sla keys:", prof["delivery_sla"].keys())
    if "duration_stats_clean" in prof["delivery_sla"]:
        print("duration_stats_clean:", prof["delivery_sla"]["duration_stats_clean"])
