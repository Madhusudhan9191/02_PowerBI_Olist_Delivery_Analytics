import pandas as pd
import os

RAW_DIR = r"../../data/raw"

products = pd.read_csv(os.path.join(RAW_DIR, "olist_products_dataset.csv"))
translations = pd.read_csv(os.path.join(RAW_DIR, "product_category_name_translation.csv"))
items = pd.read_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"))

prod_cats = set(products["product_category_name"].dropna())
trans_cats = set(translations["product_category_name"])
missing = prod_cats - trans_cats
print("Missing categories in translation table:", missing)

for cat in missing:
    prods_in_cat = products[products["product_category_name"] == cat]["product_id"]
    items_in_cat = items[items["product_id"].isin(prods_in_cat)]
    print(f"Category '{cat}': {len(prods_in_cat)} products, {len(items_in_cat)} order items")

# Check null product categories
null_prods = products[products["product_category_name"].isnull()]["product_id"]
null_items = items[items["product_id"].isin(null_prods)]
print(f"Null category products: {len(null_prods)} products, {len(null_items)} order items")
