import os
import json
import pandas as pd
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DOCS_DIR = os.path.join(BASE_DIR, "documentation")

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

files = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv"
}

dfs = {}
for name, fname in files.items():
    fpath = os.path.join(RAW_DIR, fname)
    dfs[name] = pd.read_csv(fpath)
    print(f"Loaded {name}: {dfs[name].shape[0]:,} rows, {dfs[name].shape[1]} cols")

results = {}

# 1. Per-table profile
table_profiles = {}
for name, df in dfs.items():
    null_counts = df.isnull().sum().to_dict()
    null_pcts = {k: round(v / len(df) * 100, 3) for k, v in null_counts.items()}
    cols_info = {}
    for col in df.columns:
        cols_info[col] = {
            "dtype": str(df[col].dtype),
            "null_count": int(null_counts[col]),
            "null_pct": float(null_pcts[col]),
            "n_unique": int(df[col].nunique(dropna=True))
        }
    
    table_profiles[name] = {
        "file": files[name],
        "rows": len(df),
        "columns_count": len(df.columns),
        "columns": cols_info,
        "exact_duplicates": int(df.duplicated().sum())
    }

results["table_profiles"] = table_profiles

# 2. Key Uniqueness Analysis
key_uniqueness = {
    "customers.customer_id": {
        "total": len(dfs["customers"]),
        "unique": int(dfs["customers"]["customer_id"].nunique()),
        "is_unique": bool(len(dfs["customers"]) == dfs["customers"]["customer_id"].nunique())
    },
    "customers.customer_unique_id": {
        "total": len(dfs["customers"]),
        "unique": int(dfs["customers"]["customer_unique_id"].nunique()),
        "is_unique": bool(len(dfs["customers"]) == dfs["customers"]["customer_unique_id"].nunique())
    },
    "orders.order_id": {
        "total": len(dfs["orders"]),
        "unique": int(dfs["orders"]["order_id"].nunique()),
        "is_unique": bool(len(dfs["orders"]) == dfs["orders"]["order_id"].nunique())
    },
    "order_items (order_id + order_item_id)": {
        "total": len(dfs["order_items"]),
        "unique": int(dfs["order_items"].groupby(["order_id", "order_item_id"]).ngroups),
        "is_unique": bool(len(dfs["order_items"]) == dfs["order_items"].groupby(["order_id", "order_item_id"]).ngroups)
    },
    "order_payments (order_id + payment_sequential)": {
        "total": len(dfs["order_payments"]),
        "unique": int(dfs["order_payments"].groupby(["order_id", "payment_sequential"]).ngroups),
        "is_unique": bool(len(dfs["order_payments"]) == dfs["order_payments"].groupby(["order_id", "payment_sequential"]).ngroups)
    },
    "order_reviews.review_id": {
        "total": len(dfs["order_reviews"]),
        "unique": int(dfs["order_reviews"]["review_id"].nunique()),
        "is_unique": bool(len(dfs["order_reviews"]) == dfs["order_reviews"]["review_id"].nunique())
    },
    "order_reviews.order_id": {
        "total": len(dfs["order_reviews"]),
        "unique": int(dfs["order_reviews"]["order_id"].nunique()),
        "is_unique": bool(len(dfs["order_reviews"]) == dfs["order_reviews"]["order_id"].nunique())
    },
    "products.product_id": {
        "total": len(dfs["products"]),
        "unique": int(dfs["products"]["product_id"].nunique()),
        "is_unique": bool(len(dfs["products"]) == dfs["products"]["product_id"].nunique())
    },
    "sellers.seller_id": {
        "total": len(dfs["sellers"]),
        "unique": int(dfs["sellers"]["seller_id"].nunique()),
        "is_unique": bool(len(dfs["sellers"]) == dfs["sellers"]["seller_id"].nunique())
    },
    "category_translation.product_category_name": {
        "total": len(dfs["category_translation"]),
        "unique": int(dfs["category_translation"]["product_category_name"].nunique()),
        "is_unique": bool(len(dfs["category_translation"]) == dfs["category_translation"]["product_category_name"].nunique())
    }
}
results["key_uniqueness"] = key_uniqueness

# 3. Referential Integrity (Foreign Key / Join Cardinality & Orphans)
orders_customers = set(dfs["orders"]["customer_id"])
all_customers = set(dfs["customers"]["customer_id"])
orphan_orders_customers = len(orders_customers - all_customers)
unused_customers = len(all_customers - orders_customers)

orders_ids = set(dfs["orders"]["order_id"])
items_order_ids = set(dfs["order_items"]["order_id"])
orphan_items_orders = len(items_order_ids - orders_ids)
orders_without_items = len(orders_ids - items_order_ids)

sellers_ids = set(dfs["sellers"]["seller_id"])
items_seller_ids = set(dfs["order_items"]["seller_id"])
orphan_items_sellers = len(items_seller_ids - sellers_ids)

product_ids = set(dfs["products"]["product_id"])
items_product_ids = set(dfs["order_items"]["product_id"])
orphan_items_products = len(items_product_ids - product_ids)

payments_order_ids = set(dfs["order_payments"]["order_id"])
orphan_payments_orders = len(payments_order_ids - orders_ids)
orders_without_payments = len(orders_ids - payments_order_ids)

reviews_order_ids = set(dfs["order_reviews"]["order_id"])
orphan_reviews_orders = len(reviews_order_ids - orders_ids)
orders_without_reviews = len(orders_ids - reviews_order_ids)

prod_cats = set(dfs["products"]["product_category_name"].dropna())
trans_cats = set(dfs["category_translation"]["product_category_name"])
missing_translations = len(prod_cats - trans_cats)
missing_translation_cats = sorted(list(prod_cats - trans_cats))

geo_prefixes = set(dfs["geolocation"]["geolocation_zip_code_prefix"])
cust_prefixes = set(dfs["customers"]["customer_zip_code_prefix"])
seller_prefixes = set(dfs["sellers"]["seller_zip_code_prefix"])

missing_cust_prefixes = cust_prefixes - geo_prefixes
missing_seller_prefixes = seller_prefixes - geo_prefixes

custs_with_missing_geo = dfs["customers"][dfs["customers"]["customer_zip_code_prefix"].isin(missing_cust_prefixes)]
orders_with_missing_cust_geo = dfs["orders"][dfs["orders"]["customer_id"].isin(custs_with_missing_geo["customer_id"])]
sellers_with_missing_geo = dfs["sellers"][dfs["sellers"]["seller_zip_code_prefix"].isin(missing_seller_prefixes)]

referential_integrity = {
    "orders_with_invalid_customer": orphan_orders_customers,
    "customers_without_orders": unused_customers,
    "items_with_invalid_order": orphan_items_orders,
    "orders_without_items": orders_without_items,
    "items_with_invalid_seller": orphan_items_sellers,
    "items_with_invalid_product": orphan_items_products,
    "payments_with_invalid_order": orphan_payments_orders,
    "orders_without_payments": orders_without_payments,
    "reviews_with_invalid_order": orphan_reviews_orders,
    "orders_without_reviews": orders_without_reviews,
    "missing_category_translations_count": missing_translations,
    "missing_category_translation_names": missing_translation_cats,
    "missing_customer_zip_prefixes_count": len(missing_cust_prefixes),
    "customers_affected_by_missing_geo": len(custs_with_missing_geo),
    "orders_affected_by_missing_cust_geo": len(orders_with_missing_cust_geo),
    "missing_seller_zip_prefixes_count": len(missing_seller_prefixes),
    "sellers_affected_by_missing_geo": len(sellers_with_missing_geo)
}
results["referential_integrity"] = referential_integrity

# 4. Order Status Distribution
status_counts = dfs["orders"]["order_status"].value_counts().to_dict()
status_dist = {k: {"count": int(v), "pct": round(float(v) / len(dfs["orders"]) * 100, 4)} for k, v in status_counts.items()}
results["order_status_distribution"] = status_dist

# 5. Date Coverage & Monthly Order Volumes
orders_df = dfs["orders"].copy()
for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", 
            "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders_df[col] = pd.to_datetime(orders_df[col], errors="coerce")

orders_df["purchase_year_month"] = orders_df["order_purchase_timestamp"].dt.to_period("M").astype(str)
monthly_counts = orders_df["purchase_year_month"].value_counts().sort_index().to_dict()

monthly_coverage = {}
for ym, cnt in monthly_counts.items():
    monthly_coverage[ym] = {
        "order_count": int(cnt),
        "is_thin": bool(cnt < 100)
    }
results["monthly_coverage"] = monthly_coverage

# Core steady-state window: 2017-01-01 to 2018-08-31
window_mask = (orders_df["order_purchase_timestamp"] >= "2017-01-01 00:00:00") & (orders_df["order_purchase_timestamp"] <= "2018-08-31 23:59:59")
window_order_count = int(window_mask.sum())
window_order_pct = round(window_order_count / len(orders_df) * 100, 4)

results["reporting_window"] = {
    "start_date": "2017-01-01",
    "end_date": "2018-08-31",
    "order_count": window_order_count,
    "order_pct": window_order_pct,
    "thin_orders_excluded": int(len(orders_df) - window_order_count)
}

# 6. Granularity / Cardinality Distributions
items_per_order = dfs["order_items"].groupby("order_id")["order_item_id"].count()
results["items_per_order"] = {
    "orders_with_items_count": len(items_per_order),
    "min": int(items_per_order.min()),
    "q25": float(items_per_order.quantile(0.25)),
    "median": float(items_per_order.median()),
    "mean": round(float(items_per_order.mean()), 3),
    "q75": float(items_per_order.quantile(0.75)),
    "max": int(items_per_order.max()),
    "pct_1_item": round(float((items_per_order == 1).mean() * 100), 2),
    "pct_2_plus_items": round(float((items_per_order > 1).mean() * 100), 2)
}

payments_per_order = dfs["order_payments"].groupby("order_id")["payment_sequential"].count()
results["payments_per_order"] = {
    "orders_with_payments_count": len(payments_per_order),
    "min": int(payments_per_order.min()),
    "q25": float(payments_per_order.quantile(0.25)),
    "median": float(payments_per_order.median()),
    "mean": round(float(payments_per_order.mean()), 3),
    "q75": float(payments_per_order.quantile(0.75)),
    "max": int(payments_per_order.max()),
    "pct_1_payment": round(float((payments_per_order == 1).mean() * 100), 2),
    "pct_2_plus_payments": round(float((payments_per_order > 1).mean() * 100), 2)
}

reviews_per_order = dfs["order_reviews"].groupby("order_id")["review_id"].count()
results["reviews_per_order"] = {
    "distinct_orders_reviewed": len(reviews_per_order),
    "orders_with_0_reviews": orders_without_reviews,
    "orders_with_1_review": int((reviews_per_order == 1).sum()),
    "orders_with_gt_1_review": int((reviews_per_order > 1).sum()),
    "max_reviews_per_order": int(reviews_per_order.max()),
    "review_id_unique_count": int(dfs["order_reviews"]["review_id"].nunique()),
    "review_rows_count": len(dfs["order_reviews"])
}

# 7. Null delivery dates breakdown by order status
null_delivery_by_status = orders_df.groupby("order_status")[
    ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]
].agg(
    total_orders=("order_approved_at", "size"),
    null_approved_at=("order_approved_at", lambda s: int(s.isnull().sum())),
    null_carrier_date=("order_delivered_carrier_date", lambda s: int(s.isnull().sum())),
    null_customer_delivery=("order_delivered_customer_date", lambda s: int(s.isnull().sum())),
    null_estimated_delivery=("order_estimated_delivery_date", lambda s: int(s.isnull().sum()))
).to_dict(orient="index")
results["null_dates_by_status"] = null_delivery_by_status

# 8. Impossible / Anomalous Date Sequences
anomalies = {
    "approved_before_purchase": int((orders_df["order_approved_at"] < orders_df["order_purchase_timestamp"]).sum()),
    "carrier_before_purchase": int((orders_df["order_delivered_carrier_date"] < orders_df["order_purchase_timestamp"]).sum()),
    "carrier_before_approved": int((orders_df["order_delivered_carrier_date"] < orders_df["order_approved_at"]).sum()),
    "delivery_before_purchase": int((orders_df["order_delivered_customer_date"] < orders_df["order_purchase_timestamp"]).sum()),
    "delivery_before_carrier": int((orders_df["order_delivered_customer_date"] < orders_df["order_delivered_carrier_date"]).sum()),
    "delivery_before_approved": int((orders_df["order_delivered_customer_date"] < orders_df["order_approved_at"]).sum()),
    "estimated_before_purchase": int((orders_df["order_estimated_delivery_date"] < orders_df["order_purchase_timestamp"]).sum())
}
results["date_sequence_anomalies"] = anomalies

# 9. Delivered Orders SLA: DATE-LEVEL (Primary) & TIMESTAMP-LEVEL (Comparison)
delivered = orders_df[(orders_df["order_status"] == "delivered") & (orders_df["order_delivered_customer_date"].notnull())].copy()

# Date-level truncation (order_estimated_delivery_date is date-only with 00:00:00)
delivered["delivered_date_only"] = delivered["order_delivered_customer_date"].dt.normalize()
delivered["estimated_date_only"] = delivered["order_estimated_delivery_date"].dt.normalize()

delivered["is_late_date"] = delivered["delivered_date_only"] > delivered["estimated_date_only"]
delivered["is_on_time_date"] = delivered["delivered_date_only"] <= delivered["estimated_date_only"]
delivered["delay_days_date"] = (delivered["delivered_date_only"] - delivered["estimated_date_only"]).dt.total_seconds() / 86400.0

on_time_count_date = int(delivered["is_on_time_date"].sum())
late_count_date = int(delivered["is_late_date"].sum())
on_time_rate_date = round(on_time_count_date / len(delivered) * 100, 4)
late_rate_date = round(late_count_date / len(delivered) * 100, 4)

late_delays_date = delivered[delivered["is_late_date"]]["delay_days_date"]
delay_stats_date = {
    "min_days": float(late_delays_date.min()),
    "median_days": float(late_delays_date.median()),
    "mean_days": round(float(late_delays_date.mean()), 3),
    "p90_days": float(late_delays_date.quantile(0.90)),
    "max_days": float(late_delays_date.max())
}

# Timestamp-level (for sensitivity reference)
delivered["is_late_ts"] = delivered["order_delivered_customer_date"] > delivered["order_estimated_delivery_date"]
delivered["is_on_time_ts"] = delivered["order_delivered_customer_date"] <= delivered["order_estimated_delivery_date"]
on_time_count_ts = int(delivered["is_on_time_ts"].sum())
late_count_ts = int(delivered["is_late_ts"].sum())

# Durations in fractional days
delivered["handling_days"] = (delivered["order_delivered_carrier_date"] - delivered["order_approved_at"]).dt.total_seconds() / 86400.0
delivered["transit_days"] = (delivered["order_delivered_customer_date"] - delivered["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0
delivered["cycle_days"] = (delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]).dt.total_seconds() / 86400.0

# Count negative duration rows among delivered orders
neg_handling_count = int((delivered["handling_days"] < 0).sum())
neg_transit_count = int((delivered["transit_days"] < 0).sum())

# Duration stats: ALL non-null rows
duration_stats_all = {
    "handling_N": int(delivered["handling_days"].dropna().shape[0]),
    "avg_handling_days": round(float(delivered["handling_days"].dropna().mean()), 4),
    "median_handling_days": round(float(delivered["handling_days"].dropna().median()), 4),
    "transit_N": int(delivered["transit_days"].dropna().shape[0]),
    "avg_transit_days": round(float(delivered["transit_days"].dropna().mean()), 4),
    "median_transit_days": round(float(delivered["transit_days"].dropna().median()), 4),
    "cycle_N": int(delivered["cycle_days"].dropna().shape[0]),
    "avg_cycle_days": round(float(delivered["cycle_days"].dropna().mean()), 4),
    "median_cycle_days": round(float(delivered["cycle_days"].dropna().median()), 4)
}

# Duration stats: EXCLUDING negative anomalies
valid_handling = delivered[delivered["handling_days"] >= 0]["handling_days"]
valid_transit = delivered[delivered["transit_days"] >= 0]["transit_days"]
clean_both_transit = delivered[(delivered["transit_days"] >= 0) & (delivered["handling_days"] >= 0)]["transit_days"]

duration_stats_clean = {
    "neg_handling_rows_excluded": neg_handling_count,
    "handling_clean_N": len(valid_handling),
    "avg_handling_clean_days": round(float(valid_handling.mean()), 4),
    "median_handling_clean_days": round(float(valid_handling.median()), 4),
    "neg_transit_rows_excluded": neg_transit_count,
    "transit_clean_N": len(valid_transit),
    "avg_transit_clean_days": round(float(valid_transit.mean()), 4),
    "median_transit_clean_days": round(float(valid_transit.median()), 4),
    "transit_excluding_all_anomalies_N": len(clean_both_transit),
    "transit_excluding_all_anomalies_days": round(float(clean_both_transit.mean()), 4),
    "median_transit_excluding_all_anomalies_days": round(float(clean_both_transit.median()), 4)
}

results["delivery_sla"] = {
    "delivered_status_total": int((orders_df["order_status"] == "delivered").sum()),
    "delivered_with_cust_date": len(delivered),
    "delivered_missing_cust_date": int(orders_df[orders_df["order_status"] == "delivered"]["order_delivered_customer_date"].isnull().sum()),
    "date_level": {
        "on_time_count": on_time_count_date,
        "late_count": late_count_date,
        "on_time_rate_pct": on_time_rate_date,
        "late_rate_pct": late_rate_date,
        "delay_stats_late_orders": delay_stats_date
    },
    "timestamp_level_reference": {
        "on_time_count": on_time_count_ts,
        "late_count": late_count_ts,
        "on_time_rate_pct": round(on_time_count_ts / len(delivered) * 100, 4),
        "late_rate_pct": round(late_count_ts / len(delivered) * 100, 4)
    },
    "duration_stats_all": duration_stats_all,
    "duration_stats_clean": duration_stats_clean
}

# 10. Reviews & Customer Satisfaction (H1 Date-Level Breakdown & Timing Flag)
reviews_df = dfs["order_reviews"].copy()
reviews_df["review_answer_timestamp"] = pd.to_datetime(reviews_df["review_answer_timestamp"], errors="coerce")
reviews_df["review_creation_date"] = pd.to_datetime(reviews_df["review_creation_date"], errors="coerce")

dedup_reviews = reviews_df.sort_values(
    ["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
    ascending=[True, False, False, False]
).drop_duplicates(subset=["order_id"], keep="first").copy()

deliv_rev = delivered.merge(dedup_reviews, on="order_id", how="inner")

# Add review_created_before_delivery flag
deliv_rev["review_creation_date_only"] = deliv_rev["review_creation_date"].dt.normalize()
deliv_rev["review_created_before_delivery"] = deliv_rev["review_creation_date_only"] < deliv_rev["delivered_date_only"]

# Star shares helper
def compute_star_metrics(df):
    N = len(df)
    if N == 0:
        return {"N": 0, "avg_score": None, "pct_1_2_star": None, "pct_5_star": None}
    s12 = int(((df["review_score"] == 1) | (df["review_score"] == 2)).sum())
    s3 = int((df["review_score"] == 3).sum())
    s4 = int((df["review_score"] == 4).sum())
    s5 = int((df["review_score"] == 5).sum())
    return {
        "N": N,
        "avg_score": round(float(df["review_score"].mean()), 4),
        "count_1_2_star": s12,
        "pct_1_2_star": round(s12 / N * 100, 2),
        "count_3_star": s3,
        "pct_3_star": round(s3 / N * 100, 2),
        "count_4_star": s4,
        "pct_4_star": round(s4 / N * 100, 2),
        "count_5_star": s5,
        "pct_5_star": round(s5 / N * 100, 2)
    }

ontime_rev_df = deliv_rev[deliv_rev["is_on_time_date"]]
late_rev_df = deliv_rev[deliv_rev["is_late_date"]]

ontime_metrics = compute_star_metrics(ontime_rev_df)
late_metrics = compute_star_metrics(late_rev_df)

# Split by review_created_before_delivery
ontime_before_df = ontime_rev_df[ontime_rev_df["review_created_before_delivery"]]
ontime_after_df = ontime_rev_df[~ontime_rev_df["review_created_before_delivery"]]

late_before_df = late_rev_df[late_rev_df["review_created_before_delivery"]]
late_after_df = late_rev_df[~late_rev_df["review_created_before_delivery"]]

h1_satisfaction = {
    "total_delivered_reviewed": len(deliv_rev),
    "date_level_ontime": ontime_metrics,
    "date_level_late": late_metrics,
    "score_gap": round(late_metrics["avg_score"] - ontime_metrics["avg_score"], 4),
    "late_review_timing_split": {
        "reviewed_before_delivery": compute_star_metrics(late_before_df),
        "reviewed_before_delivery_pct_of_late": round(len(late_before_df) / len(late_rev_df) * 100, 2),
        "reviewed_on_or_after_delivery": compute_star_metrics(late_after_df),
        "reviewed_on_or_after_delivery_pct_of_late": round(len(late_after_df) / len(late_rev_df) * 100, 2)
    },
    "ontime_review_timing_split": {
        "reviewed_before_delivery": compute_star_metrics(ontime_before_df),
        "reviewed_before_delivery_pct_of_ontime": round(len(ontime_before_df) / len(ontime_rev_df) * 100, 2),
        "reviewed_on_or_after_delivery": compute_star_metrics(ontime_after_df),
        "reviewed_on_or_after_delivery_pct_of_ontime": round(len(ontime_after_df) / len(ontime_rev_df) * 100, 2)
    }
}
results["h1_satisfaction_analysis"] = h1_satisfaction

# 11. Financial & Operational Control Totals (Canonical Benchmark)
total_orders = len(dfs["orders"])
total_items = len(dfs["order_items"])
total_item_revenue = round(float(dfs["order_items"]["price"].sum()), 2)
total_freight_value = round(float(dfs["order_items"]["freight_value"].sum()), 2)
total_customer_spend = round(total_item_revenue + total_freight_value, 2)
total_payment_value = round(float(dfs["order_payments"]["payment_value"].sum()), 2)

delivered_order_ids = set(delivered["order_id"])
delivered_items = dfs["order_items"][dfs["order_items"]["order_id"].isin(delivered_order_ids)]
delivered_item_revenue = round(float(delivered_items["price"].sum()), 2)
delivered_freight_value = round(float(delivered_items["freight_value"].sum()), 2)
delivered_customer_spend = round(delivered_item_revenue + delivered_freight_value, 2)

avg_raw_review_score = round(float(dfs["order_reviews"]["review_score"].mean()), 4)
avg_dedup_review_score = round(float(dedup_reviews["review_score"].mean()), 4)
avg_delivered_dedup_review_score = round(float(deliv_rev["review_score"].mean()), 4)

n_customers = len(dfs["customers"])
n_unique_customers = dfs["customers"]["customer_unique_id"].nunique()
cust_order_counts = dfs["customers"].groupby("customer_unique_id")["customer_id"].count()
repeat_customers = int((cust_order_counts > 1).sum())
repeat_rate = round(repeat_customers / n_unique_customers * 100, 4)

control_totals = {
    "total_orders": total_orders,
    "total_order_items": total_items,
    "total_item_revenue_brl": total_item_revenue,
    "total_freight_value_brl": total_freight_value,
    "total_customer_spend_brl": total_customer_spend,
    "total_payment_value_brl": total_payment_value,
    "payment_minus_spend_diff_brl": round(total_payment_value - total_customer_spend, 2),
    "delivered_orders_with_date": len(delivered),
    "delivered_order_items": len(delivered_items),
    "delivered_item_revenue_brl": delivered_item_revenue,
    "delivered_freight_value_brl": delivered_freight_value,
    "delivered_customer_spend_brl": delivered_customer_spend,
    "date_level_ontime_delivered_orders": on_time_count_date,
    "date_level_late_delivered_orders": late_count_date,
    "date_level_ontime_delivery_rate_pct": on_time_rate_date,
    "date_level_late_delivery_rate_pct": late_rate_date,
    "raw_reviews_count": len(dfs["order_reviews"]),
    "deduplicated_order_reviews_count": len(dedup_reviews),
    "avg_raw_review_score": avg_raw_review_score,
    "avg_dedup_review_score": avg_dedup_review_score,
    "avg_delivered_dedup_review_score": avg_delivered_dedup_review_score,
    "date_level_ontime_reviewed_count": ontime_metrics["N"],
    "date_level_ontime_avg_review_score": ontime_metrics["avg_score"],
    "date_level_ontime_pct_1_2_star": ontime_metrics["pct_1_2_star"],
    "date_level_ontime_pct_5_star": ontime_metrics["pct_5_star"],
    "date_level_late_reviewed_count": late_metrics["N"],
    "date_level_late_avg_review_score": late_metrics["avg_score"],
    "date_level_late_pct_1_2_star": late_metrics["pct_1_2_star"],
    "date_level_late_pct_5_star": late_metrics["pct_5_star"],
    "total_customer_id_count": n_customers,
    "total_customer_unique_id_count": n_unique_customers,
    "repeat_customers_count": repeat_customers,
    "repeat_customer_rate_pct": repeat_rate
}
results["control_totals"] = control_totals

out_json = os.path.join(PROCESSED_DIR, "profiling_results.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Saved updated profiling results to:", out_json)
