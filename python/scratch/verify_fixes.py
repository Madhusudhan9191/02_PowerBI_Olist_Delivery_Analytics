import os
import json
import pandas as pd
import numpy as np

RAW_DIR = r"../../data/raw"

# Load tables
customers = pd.read_csv(os.path.join(RAW_DIR, "olist_customers_dataset.csv"))
geolocation = pd.read_csv(os.path.join(RAW_DIR, "olist_geolocation_dataset.csv"))
orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
order_items = pd.read_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"))
order_payments = pd.read_csv(os.path.join(RAW_DIR, "olist_order_payments_dataset.csv"))
order_reviews = pd.read_csv(os.path.join(RAW_DIR, "olist_order_reviews_dataset.csv"))
products = pd.read_csv(os.path.join(RAW_DIR, "olist_products_dataset.csv"))
sellers = pd.read_csv(os.path.join(RAW_DIR, "olist_sellers_dataset.csv"))

# Parse datetime columns in orders
datetime_cols = [
    "order_purchase_timestamp", "order_approved_at", 
    "order_delivered_carrier_date", "order_delivered_customer_date", 
    "order_estimated_delivery_date"
]
for col in datetime_cols:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

# Parse datetime columns in reviews
order_reviews["review_creation_date"] = pd.to_datetime(order_reviews["review_creation_date"], errors="coerce")
order_reviews["review_answer_timestamp"] = pd.to_datetime(order_reviews["review_answer_timestamp"], errors="coerce")

print("--- 1. DATE-LEVEL LATE / ON-TIME DEFINITION ---")
delivered = orders[(orders["order_status"] == "delivered") & (orders["order_delivered_customer_date"].notnull())].copy()
print(f"Total delivered orders with valid delivery date: {len(delivered)}")

# Date-level comparison
delivered["delivered_date_only"] = delivered["order_delivered_customer_date"].dt.normalize()
delivered["estimated_date_only"] = delivered["order_estimated_delivery_date"].dt.normalize()

delivered["is_late_date"] = delivered["delivered_date_only"] > delivered["estimated_date_only"]
delivered["is_on_time_date"] = delivered["delivered_date_only"] <= delivered["estimated_date_only"]

late_count_date = delivered["is_late_date"].sum()
ontime_count_date = delivered["is_on_time_date"].sum()
late_pct_date = late_count_date / len(delivered) * 100
ontime_pct_date = ontime_count_date / len(delivered) * 100

print(f"Date-level Late: {late_count_date:,} ({late_pct_date:.2f}%)")
print(f"Date-level On-Time: {ontime_count_date:,} ({ontime_pct_date:.2f}%)")

# Delay in days for late orders (date level)
delivered["delay_days_date"] = (delivered["delivered_date_only"] - delivered["estimated_date_only"]).dt.total_seconds() / 86400.0
late_delays_date = delivered[delivered["is_late_date"]]["delay_days_date"]
print(f"Late delay days (date level): min={late_delays_date.min()}, median={late_delays_date.median()}, mean={late_delays_date.mean():.3f}, max={late_delays_date.max()}")

print("\n--- 2. REVIEW DEDUPLICATION & REVIEW SHARES (DATE-LEVEL) ---")
# Deduplicate reviews: latest review_answer_timestamp, tie breakers: creation date, review_id
dedup_reviews = order_reviews.sort_values(
    ["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
    ascending=[True, False, False, False]
).drop_duplicates(subset=["order_id"], keep="first").copy()

print(f"Deduplicated reviews count: {len(dedup_reviews)}")

# Merge with delivered orders
deliv_rev = delivered.merge(dedup_reviews, on="order_id", how="inner")
print(f"Delivered orders with review: {len(deliv_rev)}")

ontime_rev = deliv_rev[deliv_rev["is_on_time_date"]]
late_rev = deliv_rev[deliv_rev["is_late_date"]]

print(f"On-time reviewed count: {len(ontime_rev)}, Average review score: {ontime_rev['review_score'].mean():.4f}")
print(f"Late reviewed count: {len(late_rev)}, Average review score: {late_rev['review_score'].mean():.4f}")
print(f"Review score gap: {late_rev['review_score'].mean() - ontime_rev['review_score'].mean():.4f}")

# Distribution of star ratings
def get_star_shares(df):
    total = len(df)
    s12 = ((df["review_score"] == 1) | (df["review_score"] == 2)).sum()
    s3 = (df["review_score"] == 3).sum()
    s4 = (df["review_score"] == 4).sum()
    s5 = (df["review_score"] == 5).sum()
    return {
        "N": total,
        "1-2_stars": s12, "1-2_pct": s12 / total * 100,
        "3_stars": s3, "3_pct": s3 / total * 100,
        "4_stars": s4, "4_pct": s4 / total * 100,
        "5_stars": s5, "5_pct": s5 / total * 100
    }

ontime_shares = get_star_shares(ontime_rev)
late_shares = get_star_shares(late_rev)
print("On-time star shares:", ontime_shares)
print("Late star shares:", late_shares)

print("\n--- 3. REPORTING WINDOW ORDER COUNT (2017-01-01 to 2018-08-31) ---")
# Window filtering
window_orders = orders[
    (orders["order_purchase_timestamp"] >= "2017-01-01 00:00:00") & 
    (orders["order_purchase_timestamp"] <= "2018-08-31 23:59:59")
]
print(f"Orders in 2017-01-01 to 2018-08-31: {len(window_orders)} ({len(window_orders)/len(orders)*100:.2f}%)")

print("\n--- 4. GEOLOCATION GAPS ---")
geo_prefixes = set(geolocation["geolocation_zip_code_prefix"])
cust_prefixes = set(customers["customer_zip_code_prefix"])
seller_prefixes = set(sellers["seller_zip_code_prefix"])

missing_cust_prefixes = cust_prefixes - geo_prefixes
missing_seller_prefixes = seller_prefixes - geo_prefixes

print(f"Missing customer zip prefixes: {len(missing_cust_prefixes)}")
custs_affected = customers[customers["customer_zip_code_prefix"].isin(missing_cust_prefixes)]
orders_affected = orders[orders["customer_id"].isin(custs_affected["customer_id"])]
print(f"Customers affected: {len(custs_affected)}, Orders affected: {len(orders_affected)}")

print(f"Missing seller zip prefixes: {len(missing_seller_prefixes)}")
sellers_affected = sellers[sellers["seller_zip_code_prefix"].isin(missing_seller_prefixes)]
print(f"Sellers affected: {len(sellers_affected)}")

print("\n--- 5. HANDLING AND TRANSIT TIMES (ALL VS EXCLUDING NEGATIVES) ---")
# Handling time: carrier handoff - approved_at
# Transit time: delivered_customer - carrier handoff
# Calculate in fractional days
delivered["handling_days"] = (delivered["order_delivered_carrier_date"] - delivered["order_approved_at"]).dt.total_seconds() / 86400.0
delivered["transit_days"] = (delivered["order_delivered_customer_date"] - delivered["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0

# Negative durations count
neg_handling = delivered[delivered["handling_days"] < 0]
neg_transit = delivered[delivered["transit_days"] < 0]
print(f"Negative handling rows in delivered: {len(neg_handling)}")
print(f"Negative transit rows in delivered: {len(neg_transit)}")

# Stats with all rows
print(f"Handling (ALL non-null): N={delivered['handling_days'].dropna().shape[0]}, mean={delivered['handling_days'].dropna().mean():.4f}, median={delivered['handling_days'].dropna().median():.4f}")
print(f"Transit (ALL non-null): N={delivered['transit_days'].dropna().shape[0]}, mean={delivered['transit_days'].dropna().mean():.4f}, median={delivered['transit_days'].dropna().median():.4f}")

# Stats excluding negatives
valid_handling = delivered[delivered["handling_days"] >= 0]["handling_days"]
valid_transit = delivered[delivered["transit_days"] >= 0]["transit_days"]
print(f"Handling (EXCLUDING negatives): N={len(valid_handling)}, mean={valid_handling.mean():.4f}, median={valid_handling.median():.4f}")
print(f"Transit (EXCLUDING negatives): N={len(valid_transit)}, mean={valid_transit.mean():.4f}, median={valid_transit.median():.4f}")

print("\n--- 6. REVIEW CREATED BEFORE DELIVERY AUDIT (H1 DEEP DIVE) ---")
# Compare review_creation_date with order_delivered_customer_date
# Note: review_creation_date is date-only (00:00:00)
deliv_rev["review_creation_date_only"] = deliv_rev["review_creation_date"].dt.normalize()
deliv_rev["review_before_delivery"] = deliv_rev["review_creation_date_only"] < deliv_rev["delivered_date_only"]

print("Overall delivered orders reviewed before delivery:")
rev_before_deliv_counts = deliv_rev.groupby(["is_late_date", "review_before_delivery"]).size().unstack(fill_value=0)
print(rev_before_deliv_counts)

# Percentages
print("\nPercentages by delivery timeliness:")
for late_flag, group in deliv_rev.groupby("is_late_date"):
    status_label = "Late" if late_flag else "On-Time"
    total_g = len(group)
    before_g = group["review_before_delivery"].sum()
    after_g = total_g - before_g
    print(f"\nCohort: {status_label} (N={total_g})")
    print(f"  Review BEFORE delivery: {before_g:,} ({before_g/total_g*100:.2f}%) | Avg Review Score: {group[group['review_before_delivery']]['review_score'].mean():.4f}")
    if after_g > 0:
        print(f"  Review ON/AFTER delivery: {after_g:,} ({after_g/total_g*100:.2f}%) | Avg Review Score: {group[~group['review_before_delivery']]['review_score'].mean():.4f}")

# Let's check star distribution for late orders before vs after delivery
late_before = deliv_rev[(deliv_rev["is_late_date"]) & (deliv_rev["review_before_delivery"])]
late_after = deliv_rev[(deliv_rev["is_late_date"]) & (~deliv_rev["review_before_delivery"])]

print("\nLate Orders Review Breakdown:")
print("Late reviewed BEFORE delivery shares:", get_star_shares(late_before))
print("Late reviewed ON/AFTER delivery shares:", get_star_shares(late_after))
