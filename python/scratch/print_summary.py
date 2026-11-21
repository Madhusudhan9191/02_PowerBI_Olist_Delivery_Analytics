import json

with open(r"02_PowerBI_Olist_Delivery_Analytics\data\processed\profiling_results.json") as f:
    d = json.load(f)

print("=== TABLE PROFILES ===")
for tbl, info in d["table_profiles"].items():
    print(f"\nTable: {tbl} ({info['file']}) - Rows: {info['rows']:,}, Cols: {info['columns_count']}, Duplicates: {info['exact_duplicates']}")
    for col, cinfo in info["columns"].items():
        print(f"  {col:35} | {cinfo['dtype']:10} | Nulls: {cinfo['null_count']:6} ({cinfo['null_pct']:6.2f}%) | Unique: {cinfo['n_unique']:6}")

print("\n=== KEY UNIQUENESS ===")
for k, v in d["key_uniqueness"].items():
    print(f"{k:45} | Total: {v['total']:7} | Unique: {v['unique']:7} | Is Unique: {v['is_unique']}")

print("\n=== REFERENTIAL INTEGRITY ===")
for k, v in d["referential_integrity"].items():
    print(f"{k:40} | {v}")

print("\n=== ORDER STATUS DISTRIBUTION ===")
for k, v in d["order_status_distribution"].items():
    print(f"{k:15} | Count: {v['count']:6} ({v['pct']:6.2f}%)")

print("\n=== MONTHLY COVERAGE ===")
for ym, v in d["monthly_coverage"].items():
    print(f"{ym} | Orders: {v['order_count']:6} | Thin: {v['is_thin']}")

print("\n=== CARDINALITY DISTRIBUTIONS ===")
print("Items per order:", d["items_per_order"])
print("Payments per order:", d["payments_per_order"])
print("Reviews per order:", d["reviews_per_order"])

print("\n=== NULL DATES BY STATUS ===")
for k, v in d["null_dates_by_status"].items():
    print(f"{k:15} | {v}")

print("\n=== DATE ANOMALIES ===")
for k, v in d["date_sequence_anomalies"].items():
    print(f"{k:35} | Count: {v}")

print("\n=== DELIVERY SLA ===")
for k, v in d["delivery_sla"].items():
    print(f"{k:35} | {v}")

print("\n=== CONTROL TOTALS ===")
for k, v in d["control_totals"].items():
    print(f"{k:35} | {v}")
