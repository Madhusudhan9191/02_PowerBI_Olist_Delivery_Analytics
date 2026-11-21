import pandas as pd
import os

RAW_DIR = r"../../data/raw"

orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
items = pd.read_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"))
payments = pd.read_csv(os.path.join(RAW_DIR, "olist_order_payments_dataset.csv"))

# Orders without items
orders_with_items = set(items["order_id"])
orders_no_items = orders[~orders["order_id"].isin(orders_with_items)]
print("Orders without items count:", len(orders_no_items))
print("Status breakdown of orders without items:\n", orders_no_items["order_status"].value_counts())

# Payments for orders without items
payments_for_no_item_orders = payments[payments["order_id"].isin(orders_no_items["order_id"])]
print("Payments count for orders without items:", len(payments_for_no_item_orders))
print("Total payment value for orders without items: R$", round(payments_for_no_item_orders["payment_value"].sum(), 2))

# Difference when both item spend and payments exist for the same order
item_spend_per_order = items.groupby("order_id").apply(lambda g: (g["price"] + g["freight_value"]).sum())
payment_per_order = payments.groupby("order_id")["payment_value"].sum()

comp = pd.DataFrame({"item_spend": item_spend_per_order, "payment": payment_per_order}).dropna()
comp["diff"] = comp["payment"] - comp["item_spend"]
print("\nOrders with both items and payments:", len(comp))
print("Sum of item_spend for these orders: R$", round(comp["item_spend"].sum(), 2))
print("Sum of payment for these orders: R$", round(comp["payment"].sum(), 2))
print("Difference (payment - item_spend) for common orders: R$", round(comp["diff"].sum(), 2))

mismatches = comp[comp["diff"].abs() > 0.01]
print("Count of orders where payment != item_spend:", len(mismatches))
print("Mismatches summary:\n", mismatches["diff"].describe())
