import os
import json
import numpy as np
import pandas as pd

RAW_DIR = r"../../data/raw"

customers = pd.read_csv(os.path.join(RAW_DIR, "olist_customers_dataset.csv"))
orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
order_items = pd.read_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"))
order_reviews = pd.read_csv(os.path.join(RAW_DIR, "olist_order_reviews_dataset.csv"))
products = pd.read_csv(os.path.join(RAW_DIR, "olist_products_dataset.csv"))
sellers = pd.read_csv(os.path.join(RAW_DIR, "olist_sellers_dataset.csv"))
translations = pd.read_csv(os.path.join(RAW_DIR, "product_category_name_translation.csv"))
geolocation = pd.read_csv(os.path.join(RAW_DIR, "olist_geolocation_dataset.csv"))

# Parse datetimes
for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

order_reviews["review_creation_date"] = pd.to_datetime(order_reviews["review_creation_date"], errors="coerce")
order_reviews["review_answer_timestamp"] = pd.to_datetime(order_reviews["review_answer_timestamp"], errors="coerce")

# Deduplicate reviews
dedup_rev = order_reviews.sort_values(
    ["order_id", "review_answer_timestamp", "review_creation_date", "review_id"],
    ascending=[True, False, False, False]
).drop_duplicates(subset=["order_id"], keep="first").copy()

# Delivered orders with valid delivery dates
deliv = orders[(orders["order_status"] == "delivered") & (orders["order_delivered_customer_date"].notnull())].copy()
deliv["delivered_date_only"] = deliv["order_delivered_customer_date"].dt.normalize()
deliv["estimated_date_only"] = deliv["order_estimated_delivery_date"].dt.normalize()
deliv["is_late"] = deliv["delivered_date_only"] > deliv["estimated_date_only"]
deliv["is_on_time"] = deliv["delivered_date_only"] <= deliv["estimated_date_only"]

deliv["handling_days"] = (deliv["order_delivered_carrier_date"] - deliv["order_approved_at"]).dt.total_seconds() / 86400.0
deliv["transit_days"] = (deliv["order_delivered_customer_date"] - deliv["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0
deliv["cycle_days"] = (deliv["order_delivered_customer_date"] - deliv["order_purchase_timestamp"]).dt.total_seconds() / 86400.0

print("=================================================================")
print("CHECK 1: Q05 CATEGORIES WITH LATE N >= 30")
print("=================================================================")
# Product translation map
trans_map = dict(zip(translations["product_category_name"], translations["product_category_name_english"]))
trans_map["pc_gamer"] = "pc_gamer"
trans_map["portateis_cozinha_e_preparadores_de_alimentos"] = "kitchen_small_appliances"

prods = products.copy()
prods["category_en"] = prods["product_category_name"].map(trans_map).fillna("uncategorized")

items_prod = order_items.merge(prods[["product_id", "category_en"]], on="product_id", how="left")
order_cat = items_prod[["order_id", "category_en"]].drop_duplicates()

deliv_rev = deliv.merge(dedup_rev[["order_id", "review_score"]], on="order_id", how="inner")
cat_df = deliv_rev.merge(order_cat, on="order_id", how="inner")

cat_summary = cat_df.groupby("category_en").apply(
    lambda g: pd.Series({
        "total_orders": len(g),
        "ontime_orders": (g["is_on_time"]).sum(),
        "ontime_score": g[g["is_on_time"]]["review_score"].mean(),
        "late_orders": (g["is_late"]).sum(),
        "late_score": g[g["is_late"]]["review_score"].mean()
    })
).reset_index()

cat_summary["score_gap"] = cat_summary["late_score"] - cat_summary["ontime_score"]

# Filter total >= 30
cat_ge_30_total = cat_summary[cat_summary["total_orders"] >= 30]
print(f"Categories with total orders >= 30: {len(cat_ge_30_total)}")

# Categorize by late orders N
cat_ge_30_total["late_tier"] = np.where(
    cat_ge_30_total["late_orders"] >= 100, "interpretable",
    np.where(cat_ge_30_total["late_orders"] >= 30, "exploratory", "suppress")
)

tier_counts = cat_ge_30_total["late_tier"].value_counts()
print("Late orders tier breakdown:\n", tier_counts)

qualifying_29 = cat_ge_30_total[cat_ge_30_total["late_tier"] != "suppress"]
print(f"Qualifying categories (late N >= 30): {len(qualifying_29)}")
print(f"Gap range: min={qualifying_29['score_gap'].min():.2f}, max={qualifying_29['score_gap'].max():.2f}")
print("Min gap category:", qualifying_29.loc[qualifying_29['score_gap'].idxmax()][["category_en", "score_gap", "late_orders"]])
print("Max gap category:", qualifying_29.loc[qualifying_29['score_gap'].idxmin()][["category_en", "score_gap", "late_orders"]])

print("\n=================================================================")
print("CHECK 2: Q09 ORDER ROUTE CLASSIFICATION (NO DOUBLE COUNTING)")
print("=================================================================")
# Clean delivered orders (N = 95,082)
clean_deliv = deliv[(deliv["handling_days"] >= 0) & (deliv["transit_days"] >= 0)].copy()
print(f"Clean delivered orders count: {len(clean_deliv)}")

# Get item states
item_states = order_items.merge(sellers[["seller_id", "seller_state"]], on="seller_id", how="left")
item_states = item_states.merge(orders[["order_id", "customer_id"]], on="order_id", how="left")
item_states = item_states.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
item_states["is_item_interstate"] = item_states["seller_state"] != item_states["customer_state"]

# Order-level route classification
order_route_agg = item_states.groupby("order_id").agg(
    any_interstate=("is_item_interstate", "any"),
    all_interstate=("is_item_interstate", "all"),
    item_count=("order_item_id", "count"),
    seller_count=("seller_id", "nunique")
).reset_index()

order_route_agg["has_mixed_origin"] = (order_route_agg["any_interstate"]) & (~order_route_agg["all_interstate"])
order_route_agg["route_class"] = np.where(order_route_agg["any_interstate"], "Interstate Flow", "Intrastate Flow")

clean_deliv_route = clean_deliv.merge(order_route_agg, on="order_id", how="inner")
print(f"Clean delivered orders matched: {len(clean_deliv_route)}")

route_counts = clean_deliv_route["route_class"].value_counts()
print("Clean delivered orders by route class:\n", route_counts)
print(f"Sum of route classes: {route_counts.sum()} (must equal {len(clean_deliv)})")
print(f"Mixed origin orders in clean delivered: {clean_deliv_route['has_mixed_origin'].sum()}")

# Lead times by route class
for rc, grp in clean_deliv_route.groupby("route_class"):
    print(f"\nRoute Class: {rc} (N={len(grp)})")
    print(f"  Handling: mean={grp['handling_days'].mean():.2f}, median={grp['handling_days'].median():.2f}")
    print(f"  Transit:  mean={grp['transit_days'].mean():.2f}, median={grp['transit_days'].median():.2f}")
    print(f"  Cycle:    mean={grp['cycle_days'].mean():.2f}, median={grp['cycle_days'].median():.2f}")
    print(f"  On-time:  {grp['is_on_time'].mean()*100:.2f}%")

print("\n=================================================================")
print("CHECK 3: Q06 & Q07 ORDER-LEVEL CUSTOMER STATE")
print("=================================================================")
# Compare customer.primary_state vs orders -> customers.customer_state
deliv_cust = deliv.merge(customers[["customer_id", "customer_state"]], on="customer_id", how="left")
print("Order-level customer state SP count:", (deliv_cust["customer_state"] == "SP").sum())
print("Order-level customer state MA on-time rate:", f"{deliv_cust[deliv_cust['customer_state'] == 'MA']['is_on_time'].mean()*100:.2f}% (N={len(deliv_cust[deliv_cust['customer_state'] == 'MA'])})")

print("\n=================================================================")
print("CHECK 4: Q07 PROMISED VS ACTUAL LEAD TIME (AM & RO)")
print("=================================================================")
deliv_cust["promised_lead_days"] = (deliv_cust["order_estimated_delivery_date"] - deliv_cust["order_purchase_timestamp"]).dt.total_seconds() / 86400.0
for st in ["AM", "RO", "RJ", "SP", "AL"]:
    s_df = deliv_cust[deliv_cust["customer_state"] == st]
    print(f"State {st}: N={len(s_df)}, Promised ETA mean={s_df['promised_lead_days'].mean():.1f}d, Actual Cycle mean={s_df['cycle_days'].mean():.1f}d, On-time={s_df['is_on_time'].mean()*100:.2f}%")

print("\n=================================================================")
print("CHECK 5: Q12 RETENTION WITH 95% CI & DELIVERED-ONLY & COHORT RESTRICTION")
print("=================================================================")
# Identify initial completed order per customer_unique_id
cust_orders = orders.merge(customers[["customer_id", "customer_unique_id"]], on="customer_id", how="left")

# Initial delivered order
init_order = deliv.merge(customers[["customer_id", "customer_unique_id"]], on="customer_id", how="left")
init_order = init_order.sort_values(["customer_unique_id", "order_purchase_timestamp", "order_id"]).drop_duplicates(subset=["customer_unique_id"], keep="first")
print(f"Initial delivered orders count: {len(init_order)}")

# All subsequent orders per customer
all_cust_orders = cust_orders.merge(init_order[["customer_unique_id", "order_purchase_timestamp"]], on="customer_unique_id", suffixes=("", "_init"))
subsequent = all_cust_orders[all_cust_orders["order_purchase_timestamp"] > all_cust_orders["order_purchase_timestamp_init"]]

# Subsequent any vs subsequent delivered
repeat_any_custs = set(subsequent["customer_unique_id"])
repeat_deliv_custs = set(subsequent[subsequent["order_status"] == "delivered"]["customer_unique_id"])

init_order["repeat_any"] = init_order["customer_unique_id"].isin(repeat_any_custs)
init_order["repeat_deliv"] = init_order["customer_unique_id"].isin(repeat_deliv_custs)

# Observation horizon (months between init order and dataset end 2018-10-17)
dataset_max_date = orders["order_purchase_timestamp"].max()
init_order["obs_months"] = (dataset_max_date - init_order["order_purchase_timestamp"]).dt.total_seconds() / (86400.0 * 30.4375)

print("\nFull Cohort Analysis:")
for late_val in [False, True]:
    label = "Late" if late_val else "On-Time"
    grp = init_order[init_order["is_late"] == late_val]
    n = len(grp)
    r_any = grp["repeat_any"].sum()
    r_deliv = grp["repeat_deliv"].sum()
    p_any = r_any / n * 100
    p_deliv = r_deliv / n * 100
    obs_m = grp["obs_months"].mean()
    print(f"  {label} (N={n:,}):")
    print(f"    Repeat Any: {r_any} ({p_any:.2f}%)")
    print(f"    Repeat Delivered: {r_deliv} ({p_deliv:.2f}%)")
    print(f"    Avg Follow-up Window: {obs_m:.2f} months")

# Two-proportion z-interval for full cohort delivered repeat
p1 = init_order[~init_order["is_late"]]["repeat_deliv"].mean()
n1 = len(init_order[~init_order["is_late"]])
p2 = init_order[init_order["is_late"]]["repeat_deliv"].mean()
n2 = len(init_order[init_order["is_late"]])
gap_deliv = (p2 - p1) * 100
se_deliv = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2) * 100
ci_lower_deliv = gap_deliv - 1.96 * se_deliv
ci_upper_deliv = gap_deliv + 1.96 * se_deliv
print(f"\nFull Cohort Delivered Repeat Gap: {gap_deliv:.2f} pp [95% CI: {ci_lower_deliv:.2f} to {ci_upper_deliv:.2f}]")

# Restricted cohort: First order before 2017-10-01 (>= 11 months of follow-up)
restricted = init_order[init_order["order_purchase_timestamp"] < "2017-10-01"].copy()
print(f"\nRestricted Cohort (First order < 2017-10-01, >= 11 months follow-up): Total N={len(restricted):,}")
for late_val in [False, True]:
    label = "Late" if late_val else "On-Time"
    grp = restricted[restricted["is_late"] == late_val]
    n = len(grp)
    r_deliv = grp["repeat_deliv"].sum()
    p_deliv = r_deliv / n * 100
    obs_m = grp["obs_months"].mean()
    print(f"  {label} (N={n:,}): Repeat Delivered = {r_deliv} ({p_deliv:.2f}%), Avg Follow-up = {obs_m:.2f} months")

p1_r = restricted[~restricted["is_late"]]["repeat_deliv"].mean()
n1_r = len(restricted[~restricted["is_late"]])
p2_r = restricted[restricted["is_late"]]["repeat_deliv"].mean()
n2_r = len(restricted[restricted["is_late"]])
gap_r = (p2_r - p1_r) * 100
se_r = np.sqrt(p1_r*(1-p1_r)/n1_r + p2_r*(1-p2_r)/n2_r) * 100
ci_lower_r = gap_r - 1.96 * se_r
ci_upper_r = gap_r + 1.96 * se_r
print(f"Restricted Cohort Delivered Repeat Gap: {gap_r:.2f} pp [95% CI: {ci_lower_r:.2f} to {ci_upper_r:.2f}]")

print("\n=================================================================")
print("CHECK 6: H4 FREIGHT PER KG & WEIGHT TIERS")
print("=================================================================")
# Join products weight
items_geo = order_items.merge(orders[["order_id", "customer_id"]], on="order_id", how="left")
items_geo = items_geo.merge(customers[["customer_id", "customer_zip_code_prefix"]], on="customer_id", how="left")
items_geo = items_geo.merge(sellers[["seller_id", "seller_zip_code_prefix"]], on="seller_id", how="left")
items_geo = items_geo.merge(products[["product_id", "product_weight_g"]], on="product_id", how="left")

# Median geo coordinates
geo_centroids = geolocation.groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]].median().reset_index()

items_geo = items_geo.merge(geo_centroids, left_on="customer_zip_code_prefix", right_on="geolocation_zip_code_prefix", how="left")
items_geo = items_geo.merge(geo_centroids, left_on="seller_zip_code_prefix", right_on="geolocation_zip_code_prefix", how="left", suffixes=("_cust", "_sell"))

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

items_geo["distance_km"] = haversine(items_geo["geolocation_lat_cust"], items_geo["geolocation_lng_cust"], items_geo["geolocation_lat_sell"], items_geo["geolocation_lng_sell"])
items_geo = items_geo[items_geo["distance_km"].notnull() & items_geo["product_weight_g"].notnull() & (items_geo["product_weight_g"] > 0)].copy()

items_geo["weight_kg"] = items_geo["product_weight_g"] / 1000.0
items_geo["freight_per_kg"] = items_geo["freight_value"] / items_geo["weight_kg"]

items_geo["distance_band"] = np.where(items_geo["distance_km"] < 250, "1. Local (<250km)",
                             np.where(items_geo["distance_km"] < 500, "2. Regional (250-500km)",
                             np.where(items_geo["distance_km"] < 1000, "3. Medium (500-1000km)",
                             np.where(items_geo["distance_km"] < 2000, "4. Long (1000-2000km)", "5. Remote (2000km+)"))))

items_geo["weight_tier"] = np.where(items_geo["weight_kg"] < 1.0, "1. Light (<1kg)",
                           np.where(items_geo["weight_kg"] < 5.0, "2. Medium (1-5kg)", "3. Heavy (5kg+)"))

print("\nFreight per kg by Distance Band (holding weight tier constant):")
f_agg = items_geo.groupby(["distance_band", "weight_tier"]).agg(
    n=("order_item_id", "count"),
    avg_price=("price", "mean"),
    avg_freight=("freight_value", "mean"),
    avg_weight_kg=("weight_kg", "mean"),
    avg_freight_per_kg=("freight_per_kg", "mean"),
    median_freight_per_kg=("freight_per_kg", "median"),
    freight_to_price=("freight_value", lambda x: x.sum() / items_geo.loc[x.index, "price"].sum() * 100)
).reset_index()
print(f_agg[["distance_band", "weight_tier", "n", "avg_freight", "avg_freight_per_kg", "median_freight_per_kg", "freight_to_price"]])

print("\n=================================================================")
print("CHECK 7: Q08 SELLER TIERS DEFINITION & TIER 3")
print("=================================================================")
# All orders tiering vs delivered orders tiering
all_seller_counts = order_items.groupby("seller_id")["order_id"].nunique()
print("All orders seller tiering (3,095 sellers):")
t1_all = (all_seller_counts >= 500).sum()
t2_all = ((all_seller_counts >= 100) & (all_seller_counts < 500)).sum()
t3_all = ((all_seller_counts >= 30) & (all_seller_counts < 100)).sum()
t4_all = (all_seller_counts < 30).sum()
print(f"  Tier 1 (500+): {t1_all}")
print(f"  Tier 2 (100-499): {t2_all}")
print(f"  Tier 3 (30-99): {t3_all}")
print(f"  Tier 4 (<30): {t4_all}")
print(f"  Total sellers: {t1_all + t2_all + t3_all + t4_all}")
