# Data Dictionary — Olist Delivery Analytics

This document describes every table and column in the PostgreSQL analytical warehouse
and Power BI semantic model, including data grains, source lineage, transformation logic,
data types, and analytical roles.

> **Cohort Governance Note:**
> - **Total Universe:** 99,441 orders placed between 2016-09-04 and 2018-10-17.
> - **Valid Delivered Cohort ($N = 96,470$):** `is_delivered = TRUE AND is_valid_delivery_date = TRUE`.
>   Restricted to delivered orders with non-null actual and promised delivery timestamps.
> - **Clean Fulfillment Cohort ($N = 95,082$):** Valid delivered orders with non-negative
>   merchant handling (`handling_days >= 0`) and carrier transit (`transit_days >= 0`),
>   excluding 1,388 orders with missing carrier pickup timestamps.

---

## Table of Contents
1. [fact_order_delivery](#1-fact_order_delivery)
2. [fact_order_items](#2-fact_order_items)
3. [fact_order_payments](#3-fact_order_payments)
4. [dim_customer](#4-dim_customer)
5. [dim_seller](#5-dim_seller)
6. [dim_product](#6-dim_product)
7. [dim_geography](#7-dim_geography)
8. [dim_date](#8-dim_date)
9. [Analytical Groupings & Dimension Fields](#9-analytical-groupings--dimension-fields)
10. [DAX Measures Reference](#10-dax-measures-reference)

---

## 1. `fact_order_delivery`

**Row count:** 99,441  
**Grain:** One row per order (`order_id`)  
**Source:** PostgreSQL `public.fact_order_delivery` → `data/processed/powerbi_input/fact_order_delivery.csv`  
**Role:** Primary transactional delivery fact table for SLA compliance, transit milestones, delay severity, and customer satisfaction ratings.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `order_id` | TEXT (PK) | No | Unique 32-character hexadecimal order identifier (source: `raw_orders.order_id`). |
| `customer_id` | TEXT | No | Transactional customer transaction key (source: `raw_orders.customer_id`). |
| `customer_unique_id` | TEXT (FK → dim_customer) | No | Persistent customer entity identifier (source: `raw_customers.customer_unique_id`). |
| `order_customer_state` | TEXT | No | 2-letter Brazilian state abbreviation of destination delivery address (e.g. SP, RJ, MG). |
| `order_customer_city` | TEXT | No | Delivery destination city name. |
| `order_customer_zip_prefix` | INT | No | First 5 digits of customer postal code (links to `dim_geography`). |
| `order_status` | TEXT | No | Marketplace status: `delivered` (96,478), `shipped` (1,107), `canceled` (625), `unavailable` (609), `invoiced` (314), `processing` (301), `created` (5), `approved` (2). |
| `order_purchase_timestamp` | DATETIME | No | UTC timestamp when order was placed by customer. |
| `order_approved_at` | DATETIME | Yes | UTC timestamp when payment was approved by gateway/financial institution (NULL for 160 unapproved/canceled orders). |
| `order_delivered_carrier_date`| DATETIME | Yes | UTC timestamp when merchant handed package to carrier (NULL for 1,783 orders). |
| `order_delivered_customer_date`| DATETIME | Yes | UTC timestamp of confirmed final delivery to customer (NULL for 2,965 non-delivered orders and 8 anomalies). |
| `order_estimated_delivery_date`| DATETIME | No | Promised delivery deadline communicated to customer at purchase. |
| `order_purchase_date` | DATE (FK → dim_date) | No | Truncated date of purchase (`CAST(order_purchase_timestamp AS DATE)`), joining to `dim_date.full_date`. |
| `order_delivered_customer_date_only`| DATE | Yes | Truncated date of customer delivery. |
| `order_estimated_delivery_date_only`| DATE | No | Truncated promised delivery date. |
| `promised_lead_time_days` | FLOAT | No | Days between purchase and promised date (`order_estimated_delivery_date_only − order_purchase_date`). National mean: 24.37 days. |
| `is_delivered` | BOOLEAN | No | TRUE if `order_status = 'delivered'`. |
| `is_valid_delivery_date` | BOOLEAN | No | TRUE if `order_delivered_customer_date` IS NOT NULL and `order_delivered_customer_date >= order_purchase_timestamp`. |
| `is_on_time` | BOOLEAN | No | TRUE if delivered on or before promised deadline (`order_delivered_customer_date_only <= order_estimated_delivery_date_only`). National: 89,936 orders (93.23%). |
| `is_late` | BOOLEAN | No | TRUE if delivered after promised deadline (`order_delivered_customer_date_only > order_estimated_delivery_date_only`). National: 6,534 orders (6.77%). |
| `delay_days` | FLOAT | Yes | Days late for late orders (`order_delivered_customer_date_only − order_estimated_delivery_date_only`). NULL for on-time orders. Mean: 10.62 days. |
| `estimate_variance_days` | FLOAT | Yes | Signed variance (`promised_lead_time_days − cycle_days`). Positive = delivered early/on-time; negative = late. |
| `handling_days` | FLOAT | Yes | Merchant processing duration: `CAST(order_delivered_carrier_date AS DATE) − CAST(order_approved_at AS DATE)`. Mean clean: 2.85 days. |
| `transit_days` | FLOAT | Yes | Carrier shipping duration: `CAST(order_delivered_customer_date AS DATE) − CAST(order_delivered_carrier_date AS DATE)`. Mean clean: 9.37 days. |
| `cycle_days` | FLOAT | Yes | Total customer fulfillment cycle: `order_delivered_customer_date_only − order_purchase_date`. Mean valid delivered: 12.56 days; mean clean: 12.61 days. |
| `carrier_before_purchase` | BOOLEAN | No | Data quality flag: carrier pickup timestamp predates order purchase. |
| `carrier_before_approved` | BOOLEAN | No | Data quality flag: carrier pickup timestamp predates payment approval. |
| `delivery_before_purchase` | BOOLEAN | No | Data quality flag: delivery timestamp predates order purchase. |
| `delivery_before_carrier` | BOOLEAN | No | Data quality flag: delivery timestamp predates carrier pickup. |
| `delivery_before_approved` | BOOLEAN | No | Data quality flag: delivery timestamp predates payment approval. |
| `has_negative_handling` | BOOLEAN | No | TRUE if `handling_days < 0` (1,350 anomaly orders). Excluded from clean fulfillment. |
| `has_negative_transit` | BOOLEAN | No | TRUE if `transit_days < 0` (23 anomaly orders). Excluded from clean fulfillment. |
| `is_anomalous_sequence` | BOOLEAN | No | TRUE if any temporal milestone sequence is physically impossible. |
| `is_clean_fulfillment` | BOOLEAN | No | Clean fulfillment flag: TRUE if order is delivered, has non-null customer delivery date, non-null payment approval, non-null carrier handoff, handling days >= 0, and transit days >= 0 ($N = 95,082$). Used across all bottleneck and lead time measures to avoid DAX null-coercion. |
| `is_steady_state_window` | BOOLEAN | No | Operational window flag: TRUE for orders with `order_purchase_timestamp >= '2017-01-01'`. Used as Page 1 dashboard filter. |
| `order_route_distance_km` | FLOAT | Yes | Straight-line distance between seller and customer zip code centroids via Haversine formula. |
| `order_distance_band` | TEXT | No | Distance tier: `1. Local (<250km)`, `2. Regional (250-500km)`, `3. Medium (500-1000km)`, `4. Long (1000-2000km)`, `5. Remote (2000km+)`, `Unknown`. |
| `order_delivery_status_category`| TEXT | No | Categorical visual dimension: `On-Time` (89,936 / 90.44%), `Late` (6,534 / 6.57%), `Non-Delivered` (2,963 / 2.98%), `Delivered (Missing Date)` (8 / 0.01%). Powers Page 1 donut chart. |
| `review_id` | TEXT | Yes | Primary review ID associated with order (deduplicated by latest creation date). |
| `review_score` | INT | Yes | Rating 1 to 5 stars (mean on-time: 4.2904, mean late: 2.2705). |
| `review_creation_date` | DATETIME | Yes | Timestamp review survey invite was created by platform. |
| `review_answer_timestamp` | DATETIME | Yes | Timestamp customer submitted review survey response. |
| `has_review` | BOOLEAN | No | TRUE if order has an associated review record (98,673 orders total; 95,823 delivered). |
| `review_created_before_delivery`| BOOLEAN | Yes | Timing flag: TRUE if `review_creation_date < order_delivered_customer_date`. (74.46% of late delivered reviews). |

---

## 2. `fact_order_items`

**Row count:** 112,650  
**Grain:** One row per order line item (`order_id, order_item_id`)  
**Source:** PostgreSQL `public.fact_order_items` → `data/processed/powerbi_input/fact_order_items.csv`  
**Role:** Line-item fact table linking orders to sellers, products, pricing, freight economics, and dispatch compliance.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `order_id` | TEXT (FK → fact_order_delivery)| No | Foreign key linking to parent delivery order. Participates in **bidirectional** relationship. |
| `order_item_id` | INT (PK component) | No | Sequential item position number within order (1, 2, 3...). |
| `product_id` | TEXT (FK → dim_product) | No | Foreign key to catalog product dimension. |
| `seller_id` | TEXT (FK → dim_seller) | No | Foreign key to fulfilling merchant dimension. |
| `customer_unique_id` | TEXT | No | Denormalized customer entity ID. |
| `order_purchase_date` | DATE | No | Date order was placed. |
| `shipping_limit_date` | DATETIME | No | Seller dispatch SLA deadline assigned by platform for handing item to carrier. |
| `price` | FLOAT | No | Item selling price in Brazilian Reais (BRL). Sums to Gross Item Revenue: R$ 13,591,643.70. |
| `freight_value` | FLOAT | No | Shipping charge billed for this item in BRL. Sums to Total Freight: R$ 2,251,909.54. |
| `total_item_spend` | FLOAT | No | `price + freight_value`. Sums to Customer Item Spend: R$ 15,843,553.24. |
| `freight_to_price_ratio` | FLOAT | No | Line item freight burden ratio: `freight_value / price`. National median: 19.3%. |
| `freight_per_kg` | FLOAT | Yes | Freight intensity in BRL per kilogram: `freight_value / (product_weight_g / 1000)`. |
| `is_late_dispatch` | BOOLEAN | No | Merchant SLA compliance flag: TRUE if actual carrier pickup occurred after `shipping_limit_date`. |
| `customer_zip_prefix` | INT | No | Customer zip code prefix. |
| `seller_zip_prefix` | INT | No | Seller zip code prefix. |
| `route_distance_km` | FLOAT | Yes | Haversine distance between seller and customer postal code centroids. |
| `distance_band` | TEXT | No | Distance tier classification for line item route. |
| `is_interstate` | BOOLEAN | No | Trade flow flag: TRUE if seller state differs from customer state; FALSE if intrastate (61,022 interstate orders, 34,060 intrastate orders across 95,082 clean fulfillment orders). |

---

## 3. `fact_order_payments`

**Row count:** 103,886  
**Grain:** One row per payment transaction (`order_id, payment_sequential`)  
**Source:** PostgreSQL `public.fact_order_payments` → `data/processed/powerbi_input/fact_order_payments.csv`  
**Role:** Payment settlement fact table tracking payment methods, installment credit, and captured transaction values.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `order_id` | TEXT (FK → fact_order_delivery)| No | Foreign key linking to parent order. |
| `payment_sequential` | INT (PK component) | No | Sequence number for multi-tender split payments (1, 2, 3...). |
| `payment_type` | TEXT | No | Payment method tender: `credit_card` (76,795), `boleto` (19,784), `voucher` (5,775), `debit_card` (1,529), `not_defined` (3). |
| `payment_installments` | INT | No | Number of installment payment financing terms (1 to 24 installments). |
| `payment_value` | FLOAT | No | Settled payment transaction amount in BRL. Sums to Captured Payment Value: R$ 16,008,872.12. |

---

## 4. `dim_customer`

**Row count:** 96,096  
**Grain:** One row per unique customer entity (`customer_unique_id`)  
**Source:** PostgreSQL `public.dim_customer` → `data/processed/powerbi_input/dim_customer.csv`  
**Role:** Customer master entity dimension tracking geographic location, lifetime purchase history, repeat buyer status, and cohort maturity.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `customer_unique_id` | TEXT (PK) | No | True individual customer key (resolved across multiple transactional `customer_id` values). |
| `primary_city` | TEXT | No | Primary delivery city associated with customer. |
| `primary_state` | TEXT | No | Primary state abbreviation. |
| `primary_zip_code_prefix`| INT (FK → dim_geography)| No | Primary 5-digit zip code prefix. |
| `first_order_timestamp` | DATETIME | No | Timestamp of earliest order placed by this customer. |
| `last_order_timestamp` | DATETIME | No | Timestamp of most recent order placed. |
| `lifetime_orders` | INT | No | Total lifetime orders placed across dataset duration. |
| `is_repeat_customer` | BOOLEAN | No | TRUE if `lifetime_orders > 1`. (2,997 repeat buyers; 3.12% repeat rate). |
| `has_delivered_order` | BOOLEAN | No | TRUE if customer had at least one order successfully delivered. |
| `first_delivered_order_id`| TEXT | Yes | `order_id` of customer's first delivered order. |
| `first_delivered_order_date`| DATE | Yes | Date of customer's first delivered order. |
| `first_order_on_time` | BOOLEAN | Yes | Delivery timeliness of first delivered order: TRUE = on-time, FALSE = late. |
| `first_order_late` | BOOLEAN | Yes | Complementary flag: TRUE = late first delivery. |
| `total_delivered_orders` | INT | No | Count of successfully delivered orders for customer. |
| `has_repeat_delivered_order`| BOOLEAN | No | TRUE if customer placed subsequent orders that were delivered (powers Delivered Repeat Rate). |
| `has_repeat_all_order` | BOOLEAN | No | TRUE if customer placed any subsequent order regardless of final status. |
| `is_mature_cohort` | BOOLEAN | No | Cohort maturity flag: TRUE if `first_order_timestamp < '2017-10-01'`, ensuring $\ge 11$ months of follow-up observation. |

---

## 5. `dim_seller`

**Row count:** 3,095  
**Grain:** One row per marketplace seller (`seller_id`)  
**Source:** PostgreSQL `public.dim_seller` → `data/processed/powerbi_input/dim_seller.csv`  
**Role:** Merchant profile dimension tracking volume tier classification, geographic location, and lifetime order volumes.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `seller_id` | TEXT (PK) | No | Unique 32-character merchant identifier. |
| `seller_zip_code_prefix`| INT (FK → dim_geography)| No | First 5 digits of merchant dispatch warehouse postal code. |
| `seller_city` | TEXT | No | Merchant city name. |
| `seller_state` | TEXT | No | Merchant state abbreviation (SP represents 59.7% of all sellers). |
| `seller_lifetime_orders`| INT | No | Total order count fulfilled by merchant across dataset. |
| `seller_tier` | TEXT | No | Volume segmentation tier: `Tier 1: High Volume (500+ orders)` (26 sellers), `Tier 2: Mid Volume (100-499 orders)` (184 sellers), `Tier 3: Low Volume (30-99 orders)` (424 sellers), `Tier 4: Micro Volume (<30 orders)` (2,461 sellers). |

---

## 6. `dim_product`

**Row count:** 32,951  
**Grain:** One row per catalog product (`product_id`)  
**Source:** PostgreSQL `public.dim_product` → `data/processed/powerbi_input/dim_product.csv`  
**Role:** Catalog dimension detailing product taxonomy, English category translation, and physical package dimensions for freight analysis.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `product_id` | TEXT (PK) | No | Unique 32-character product SKU identifier. |
| `product_category_name_pt`| TEXT | Yes | Original Portuguese category name (73 distinct categories). |
| `product_category_name_en`| TEXT | Yes | English translation mapped via `product_category_name_translation.csv` (e.g. `bed_bath_table`, `health_beauty`, `sports_leisure`). |
| `product_name_lenght` | INT | Yes | Character length of product catalog title. |
| `product_description_lenght`| INT | Yes | Character length of catalog product description. |
| `product_photos_qty` | INT | Yes | Number of published catalog photos. |
| `product_weight_g` | FLOAT | Yes | Product weight in grams (used to calculate freight intensity and weight tier). |
| `product_length_cm` | FLOAT | Yes | Physical package length in centimeters. |
| `product_height_cm` | FLOAT | Yes | Physical package height in centimeters. |
| `product_width_cm` | FLOAT | Yes | Physical package width in centimeters. |

---

## 7. `dim_geography`

**Row count:** 19,015  
**Grain:** One row per postal code prefix (`zip_code_prefix`)  
**Source:** PostgreSQL `public.dim_geography` → `data/processed/powerbi_input/dim_geography.csv`  
**Role:** Geographic reference master resolving Brazilian postal code centroids, median geographic coordinates, and administrative city/state mappings.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `zip_code_prefix` | INT (PK) | No | First 5 digits of Brazilian CEP postal code. |
| `median_lat` | FLOAT | No | Robust median latitude coordinate calculated from raw geolocation points. |
| `median_lng` | FLOAT | No | Robust median longitude coordinate. |
| `primary_city` | TEXT | No | Modal city name associated with postal prefix. |
| `primary_state` | TEXT | No | 2-letter state abbreviation (27 states / federal district). |
| `coordinate_count` | INT | No | Number of raw GPS survey points aggregated to compute centroid coordinates. |

---

## 8. `dim_date`

**Row count:** 1,021  
**Grain:** One row per calendar date (`full_date`)  
**Date Range:** `2016-01-01` to `2018-10-17` (bounded strictly at dataset maximum date)  
**Source:** PostgreSQL `public.dim_date` → `data/processed/powerbi_input/dim_date.csv`  
**Role:** Calendar dimension providing standard time intelligence, calendar hierarchies, and monthly trend groupings.

| Column | Data Type | Nullable | Description & Lineage |
|---|---|---|---|
| `date_key` | INT (PK) | No | Integer surrogate date key in `YYYYMMDD` format (e.g. 20171124). |
| `full_date` | DATE | No | Calendar date value joining to `fact_order_delivery.order_purchase_date`. |
| `year_num` | INT | No | Calendar year (2016, 2017, 2018). |
| `quarter_num` | INT | No | Calendar quarter number (1, 2, 3, 4). |
| `quarter_name` | TEXT | No | Quarter label (e.g. `Q1`, `Q2`, `Q3`, `Q4`). |
| `month_num` | INT | No | Calendar month index (1 to 12). |
| `month_name` | TEXT | No | Full month name (`January`, `February`, etc.). |
| `year_month` | TEXT | No | Year-month label for visual chronological sorting (`YYYY-MM`). |
| `week_of_year` | INT | No | ISO calendar week number (1 to 53). |
| `day_of_month` | INT | No | Day of month (1 to 31). |
| `day_of_week` | INT | No | Day of week integer (1 = Monday, 7 = Sunday). |
| `day_name` | TEXT | No | Full day name (`Monday`, `Tuesday`, etc.). |
| `is_weekend` | BOOLEAN | No | TRUE if Saturday or Sunday; FALSE for weekdays. |

---

## 9. Analytical Groupings & Dimension Fields

To ensure performant dimensional filtering and standardized report hierarchies, three analytical categorical groupings are maintained within the model:

### Distance Band Hierarchy (`order_distance_band`, `distance_band`)
Applied at order and line-item grain via straight-line Haversine centroid calculation:
1. `1. Local (<250km)` — 247 km average route, 95.51% SLA, 4.4 transit days
2. `2. Regional (250-500km)` — 487 km average route, 94.63% SLA, 9.1 transit days
3. `3. Medium (500-1000km)` — 868 km average route, 93.92% SLA, 11.1 transit days
4. `4. Long (1000-2000km)` — 1,345 km average route, 87.84% SLA, 14.6 transit days
5. `5. Remote (2000km+)` — 2,291 km average route, 88.19% SLA, 17.8 transit days
6. `Unknown` — Missing zip code centroid coordinates (11.6 transit days)

### Merchant Volume Tiers (`seller_tier`)
Categorizes active marketplace sellers by lifetime delivered order volume:
- `Tier 1: High Volume (500+ orders)`: 26 sellers, 8.07% late dispatch rate
- `Tier 2: Mid Volume (100-499 orders)`: 184 sellers, 9.31% late dispatch rate
- `Tier 3: Low Volume (30-99 orders)`: 424 sellers, 9.86% late dispatch rate
- `Tier 4: Micro Volume (<30 orders)`: 2,461 sellers, 11.07% late dispatch rate

### Product Weight Tiers (`weight_tier`)
Categorizes catalog items for freight rate escalation analysis:
- `Light (<1kg)`: Low package handling burden
- `Medium (1-5kg)`: Standard packaged freight
- `Heavy (>5kg)`: Bulky package freight

---

## 10. DAX Measures Reference

The semantic model contains **71 DAX measures** organized into 8 display folders within the `_Measures` table:

| Folder | Measure Count | Key Measures |
|---|---|---|
| `01_Volume_and_Spend` | 13 | `Total Orders`, `Valid Delivered Orders`, `Gross Item Revenue`, `Total Customer Spend`, `Captured Payment Value`, `Total Unique Customers`, `Total Active Sellers` |
| `02_Delivery_SLA` | 9 | `On-Time Delivery Rate %`, `Late Delivery Rate %`, `Average Delay Days (Late Orders)`, `Average Promised Lead Time Days`, `Average Actual Cycle Days`, `ETA Safety Buffer Days` |
| `03_Review_Satisfaction` | 19 | `Average Review Score (On-Time)`, `Average Review Score (Late)`, `Review Score Gap (Late vs On-Time)`, `Negative Review Share %`, `5-Star Review Share %`, `Pre-Delivery Late Review Share %`, `Avg Review Score (Pre-Delivery Late)`, `Avg Review Score (Post-Delivery Late)` |
| `04_Fulfillment_Bottlenecks` | 6 | `Clean Fulfillment Orders`, `Average Handling Days`, `Average Transit Days`, `Average Fulfillment Cycle Days`, `Handling Share of Fulfillment %`, `Transit Share of Fulfillment %` |
| `05_Regional_and_Seller` | 7 | `Interstate On-Time Rate %`, `Intrastate On-Time Rate %`, `Expected On-Time Rate %`, `Mix-Adjusted Performance Gap pp`, `Late Dispatch Rate %` |
| `06_Freight_Economics` | 3 | `Average Route Distance km`, `Total Billed Weight kg`, `Average Freight per kg` |
| `07_Customer_Retention` | 11 | `Repeat Customer Rate %`, `Delivered Repeat Rate Gap pp`, `Mature Repeat Rate % (On-Time First Order)`, `Mature Repeat Rate % (Late First Order)`, `Mature Delivered Repeat Rate Gap pp` |
| `08_Governance` | 3 | `Sample Size Status`, `Sample Size Label` |

For complete measure code definitions and implementation details, see [`powerbi/dax/measures.dax`](../powerbi/dax/measures.dax) and [`documentation/three_way_reconciliation_report.md`](three_way_reconciliation_report.md).
