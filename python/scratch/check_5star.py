import os, duckdb
INPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "powerbi_input"))
con = duckdb.connect()

con.execute(f"CREATE TABLE fact_order_delivery AS SELECT * FROM read_csv_auto('{INPUT_DIR}/fact_order_delivery.csv');")

ontime_5 = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_on_time AND has_review AND review_score = 5;").fetchone()[0]
late_5 = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late AND has_review AND review_score = 5;").fetchone()[0]
tot_del_5 = con.execute("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered AND is_valid_delivery_date AND has_review AND review_score = 5;").fetchone()[0]

print(f"5-star reviews: ontime={ontime_5}, late={late_5}, sum={ontime_5+late_5}, tot_del_5={tot_del_5}")
print(f"Shares: ontime={ontime_5/89443*100:.2f}%, late={late_5/6381*100:.2f}%, tot={tot_del_5/95824*100:.2f}%")
