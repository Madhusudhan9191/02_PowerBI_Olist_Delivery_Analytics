-- ============================================================================
-- SCRIPT 02: Load Raw Data from CSVs
-- PROJECT: Olist E-commerce Delivery Performance & Customer Satisfaction
-- ENVIRONMENT: PostgreSQL 16+
-- AUTHOR: Independent Portfolio Project
-- DESCRIPTION: Loads raw Kaggle CSV files into staging tables using \copy.
-- USAGE IN PSQL:
--   cd <project_root_directory>
--   psql -U postgres -d olist_db -f sql/02_load_raw_data.sql
-- ============================================================================

-- 1. Load Customers (99,441 rows expected)
\copy raw_customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state) FROM 'data/raw/olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 2. Load Geolocation (1,000,163 rows expected)
\copy raw_geolocation (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state) FROM 'data/raw/olist_geolocation_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 3. Load Orders (99,441 rows expected)
\copy raw_orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date) FROM 'data/raw/olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 4. Load Order Items (112,650 rows expected)
\copy raw_order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value) FROM 'data/raw/olist_order_items_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 5. Load Order Payments (103,886 rows expected)
\copy raw_order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value) FROM 'data/raw/olist_order_payments_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 6. Load Order Reviews (99,224 rows expected)
\copy raw_order_reviews (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date, review_answer_timestamp) FROM 'data/raw/olist_order_reviews_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 7. Load Products (32,951 rows expected)
\copy raw_products (product_id, product_category_name, product_name_lenght, product_description_lenght, product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm) FROM 'data/raw/olist_products_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 8. Load Sellers (3,095 rows expected)
\copy raw_sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state) FROM 'data/raw/olist_sellers_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- 9. Load Category Translation (71 rows expected)
\copy raw_product_category_name_translation (product_category_name, product_category_name_english) FROM 'data/raw/product_category_name_translation.csv' WITH (FORMAT csv, HEADER true, ENCODING 'utf-8');

-- Quick verification of row counts post-load:
SELECT 'raw_customers' AS table_name, COUNT(*) AS row_count FROM raw_customers
UNION ALL SELECT 'raw_geolocation', COUNT(*) FROM raw_geolocation
UNION ALL SELECT 'raw_orders', COUNT(*) FROM raw_orders
UNION ALL SELECT 'raw_order_items', COUNT(*) FROM raw_order_items
UNION ALL SELECT 'raw_order_payments', COUNT(*) FROM raw_order_payments
UNION ALL SELECT 'raw_order_reviews', COUNT(*) FROM raw_order_reviews
UNION ALL SELECT 'raw_products', COUNT(*) FROM raw_products
UNION ALL SELECT 'raw_sellers', COUNT(*) FROM raw_sellers
UNION ALL SELECT 'raw_product_category_name_translation', COUNT(*) FROM raw_product_category_name_translation
ORDER BY table_name;
