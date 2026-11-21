import os
import pandas as pd

RAW_DIR = r"../../data/raw"
orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
order_reviews = pd.read_csv(os.path.join(RAW_DIR, "olist_order_reviews_dataset.csv"))

for col in ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

order_reviews["review_creation_date"] = pd.to_datetime(order_reviews["review_creation_date"], errors="coerce")
order_reviews["review_answer_timestamp"] = pd.to_datetime(order_reviews["review_answer_timestamp"], errors="coerce")

dedup_reviews = order_reviews.sort_values(
    ["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
    ascending=[True, False, False, False]
).drop_duplicates(subset=["order_id"], keep="first").copy()

delivered = orders[(orders["order_status"] == "delivered") & (orders["order_delivered_customer_date"].notnull())].copy()

# Under report's original timestamp definition:
delivered["is_late_ts"] = delivered["order_delivered_customer_date"] > delivered["order_estimated_delivery_date"]
delivered["is_late_date"] = delivered["order_delivered_customer_date"].dt.normalize() > delivered["order_estimated_delivery_date"].dt.normalize()

deliv_rev = delivered.merge(dedup_reviews, on="order_id", how="inner")

# Check review_created_before_delivery:
# review_creation_date is midnight 00:00:00.
# If comparing review_creation_date < order_delivered_customer_date directly (or date normalize):
deliv_rev["rev_before_deliv_ts"] = deliv_rev["review_creation_date"] < deliv_rev["order_delivered_customer_date"]
deliv_rev["rev_before_deliv_date"] = deliv_rev["review_creation_date"].dt.normalize() < deliv_rev["order_delivered_customer_date"].dt.normalize()

print("--- Under Report's Original Timestamp Late Definition (7,661 reviewed late orders) ---")
late_ts = deliv_rev[deliv_rev["is_late_ts"]]
print("Late ts total reviewed:", len(late_ts))
print("Late ts review_creation_date < order_delivered_customer_date count:", late_ts["rev_before_deliv_ts"].sum(), f"({late_ts['rev_before_deliv_ts'].mean()*100:.2f}%)")
print("Late ts rev before delivery avg score:", late_ts[late_ts["rev_before_deliv_ts"]]["review_score"].mean())
print("Late ts rev after delivery avg score:", late_ts[~late_ts["rev_before_deliv_ts"]]["review_score"].mean())

ontime_ts = deliv_rev[~deliv_rev["is_late_ts"]]
print("On-time ts total reviewed:", len(ontime_ts))
print("On-time ts review before delivery count:", ontime_ts["rev_before_deliv_ts"].sum(), f"({ontime_ts['rev_before_deliv_ts'].mean()*100:.2f}%)")

print("\n--- Under Date-Level Late Definition (6,381 reviewed late orders) ---")
late_date = deliv_rev[deliv_rev["is_late_date"]]
print("Late date total reviewed:", len(late_date))
print("Late date review_creation_date < delivered_date count:", late_date["rev_before_deliv_date"].sum(), f"({late_date['rev_before_deliv_date'].mean()*100:.2f}%)")
print("Late date rev before delivery avg score:", late_date[late_date["rev_before_deliv_date"]]["review_score"].mean())
print("Late date rev after delivery avg score:", late_date[~late_date["rev_before_deliv_date"]]["review_score"].mean())

ontime_date = deliv_rev[~deliv_rev["is_late_date"]]
print("On-time date total reviewed:", len(ontime_date))
print("On-time date review before delivery count:", ontime_date["rev_before_deliv_date"].sum(), f"({ontime_date['rev_before_deliv_date'].mean()*100:.2f}%)")
print("On-time date rev before delivery avg score:", ontime_date[ontime_date["rev_before_deliv_date"]]["review_score"].mean())
print("On-time date rev after delivery avg score:", ontime_date[~ontime_date["rev_before_deliv_date"]]["review_score"].mean())
