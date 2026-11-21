import os
import pandas as pd

RAW_DIR = r"../../data/raw"
orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
for col in ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"]:
    orders[col] = pd.to_datetime(orders[col], errors="coerce")

deliv = orders[(orders["order_status"] == "delivered") & (orders["order_delivered_customer_date"].notnull())].copy()

# Variant A: exact timestamp diff
deliv["transit_exact"] = (deliv["order_delivered_customer_date"] - deliv["order_delivered_carrier_date"]).dt.total_seconds() / 86400.0
# Variant B: date-level diff
deliv["transit_date"] = (deliv["order_delivered_customer_date"].dt.normalize() - deliv["order_delivered_carrier_date"].dt.normalize()).dt.total_seconds() / 86400.0

# Variant C: excluding negative handling as well?
deliv["handling_exact"] = (deliv["order_delivered_carrier_date"] - deliv["order_approved_at"]).dt.total_seconds() / 86400.0

print("Transit exact - all non-null:", deliv["transit_exact"].dropna().mean())
print("Transit exact - excluding transit < 0:", deliv[deliv["transit_exact"] >= 0]["transit_exact"].mean())
print("Transit exact - excluding handling < 0 and transit < 0:", deliv[(deliv["transit_exact"] >= 0) & (deliv["handling_exact"] >= 0)]["transit_exact"].mean())

print("Transit date - all non-null:", deliv["transit_date"].dropna().mean())
print("Transit date - excluding transit < 0:", deliv[deliv["transit_date"] >= 0]["transit_date"].mean())
print("Transit date - excluding handling < 0 and transit < 0:", deliv[(deliv["transit_date"] >= 0) & (deliv["handling_exact"] >= 0)]["transit_date"].mean())

# What about ceil/floor or integer days?
print("Transit exact - rounded:", deliv[deliv["transit_exact"] >= 0]["transit_exact"].round().mean())
