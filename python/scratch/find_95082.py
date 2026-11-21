import os
import pandas as pd

RAW_DIR = r"../../data/raw"
orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
for col in ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

deliv = orders[(orders["order_status"] == "delivered") & (orders["order_delivered_customer_date"].notnull())].copy()

deliv["handling_days"] = (deliv["order_delivered_carrier_date"] - deliv["order_approved_at"]).dt.total_seconds() / 86400.0
deliv["transit_days"] = (deliv["order_delivered_customer_date"] - deliv["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0

# In our previous script:
# clean_both_transit = delivered[(delivered["transit_days"] >= 0) & (delivered["handling_days"] >= 0)]["transit_days"]
# Note that if handling_days is NaN, (handling_days >= 0) is False!
# What if someone defines clean transit as: transit_days >= 0 and handling is NOT < 0 (i.e. handling_days >= 0 or handling_days is null)?
# Or what if carrier_date.notnull() and approved_at.notnull() and customer_date.notnull()?
print("deliv count:", len(deliv))
print("deliv null approved_at:", deliv["order_approved_at"].isnull().sum())
print("deliv null carrier_date:", deliv["order_delivered_carrier_date"].isnull().sum())

# Let's inspect rows where transit_days is not null
has_transit = deliv[deliv["transit_days"].notnull()].copy()
print("has_transit count:", len(has_transit)) # 96,469 (since 1 order has null carrier_date in deliv? Wait: 96,470 - 1 = 96,469)

# Rows where transit < 0
neg_transit = has_transit[has_transit["transit_days"] < 0] # 23 rows

# Rows where handling < 0
neg_handling = has_transit[has_transit["handling_days"] < 0] # 1,350 rows

# Intersection of negative handling and negative transit:
both_neg = has_transit[(has_transit["transit_days"] < 0) & (has_transit["handling_days"] < 0)]
print("Both negative count:", len(both_neg))

# Now: exclude negative transit (23 rows) and exclude negative handling (1,350 rows)
# Notice: len(has_transit) = 96,469.
# 96,469 - 23 - 1,350 + len(both_neg) = 96,469 - 1373 + len(both_neg)
# If len(both_neg) is 12: 96,469 - 1373 + 12 = 95,108.
# But what about null approved_at?
print("has_transit null approved_at:", has_transit["order_approved_at"].isnull().sum())
null_app_in_has_transit = has_transit[has_transit["order_approved_at"].isnull()]
print("Transit days for orders with null approved_at:\n", null_app_in_has_transit["transit_days"].describe())

# Check condition 1: (transit_days >= 0) & (handling_days >= 0)
c1 = has_transit[(has_transit["transit_days"] >= 0) & (has_transit["handling_days"] >= 0)]
print("Condition 1 (handling >= 0 AND transit >= 0): N =", len(c1), "mean =", c1["transit_days"].mean(), "median =", c1["transit_days"].median())

# Check condition 2: (transit_days >= 0) & ~(handling_days < 0)
c2 = has_transit[(has_transit["transit_days"] >= 0) & ~(has_transit["handling_days"] < 0)]
print("Condition 2 (transit >= 0 AND NOT handling < 0): N =", len(c2), "mean =", c2["transit_days"].mean(), "median =", c2["transit_days"].median())

# Check condition 3: What if we filter out negative handling (1350) and negative transit (23)?
# Let's find exactly which subset has N = 95,082 and median = 7.1103!
# Let's test combinations
for drop_null_approved in [False, True]:
    for drop_null_carrier in [False, True]:
        sub = deliv.copy()
        if drop_null_approved:
            sub = sub[sub["order_approved_at"].notnull()]
        if drop_null_carrier:
            sub = sub[sub["order_delivered_carrier_date"].notnull()]
        
        # Test excluding handling < 0 and transit < 0
        s_excl = sub[(sub["handling_days"] >= 0) & (sub["transit_days"] >= 0)]
        if len(s_excl) in [95082, 95084]:
            print(f"drop_app={drop_null_approved}, drop_carr={drop_null_carrier}: N={len(s_excl)}, mean={s_excl['transit_days'].mean():.4f}, median={s_excl['transit_days'].median():.4f}")

# What if transit_days > 0 and handling_days > 0 (strictly positive)?
s_strict = deliv[(deliv["handling_days"] > 0) & (deliv["transit_days"] > 0)]
print(f"Strictly positive (> 0): N={len(s_strict)}, mean={s_strict['transit_days'].mean():.4f}, median={s_strict['transit_days'].median():.4f}")

# Let's check where 95,082 comes from!
# Notice: 95,084 - 95,082 = 2 rows!
# What are the 2 rows?
# Could it be handling == 0 or transit == 0?
print("transit_days == 0 count:", (deliv["transit_days"] == 0).sum())
print("handling_days == 0 count:", (deliv["handling_days"] == 0).sum())
# What about (deliv['order_delivered_carrier_date'] >= deliv['order_approved_at']) & (deliv['order_delivered_customer_date'] >= deliv['order_delivered_carrier_date'])?
