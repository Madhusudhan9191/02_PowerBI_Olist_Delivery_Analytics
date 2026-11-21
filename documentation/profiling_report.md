# Comprehensive Data Profiling Report
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Type:** Independent Portfolio Project  
**Author:** Software Engineer transitioning to Data Analyst / Junior Data Scientist  
**Environment:** Python 3.11.4 | Pandas 2.3.3  
**Execution Timestamp:** 2026-11-14  
**Version:** 1.1.0 (Date-Level Delivery SLA & Review Timing Update)  
**Status:** Phase 1 Complete — Re-verified Against Raw CSVs  

---

> [!NOTE]
> **Independent Verification Disclosure:**  
> All statistics, distributions, and control totals in this report were directly computed from the 9 raw CSV files uploaded to `data/raw/` using deterministic Python scripts (`python/01_data_profiling.py`, `python/verify_fixes.py`). Every figure is reproducible.

---

## 1. Executive Summary & Core Profiling Findings

| Profiling Domain | Key Empirical Finding | Analytical & Modeling Impact |
| :--- | :--- | :--- |
| **Data Scale** | 99,441 orders; 112,650 items; 103,886 payments; 99,224 reviews; 96,096 unique customers; 32,951 products; 3,095 sellers; 1,000,163 geolocation records. | Dataset represents medium-scale transactional data requiring star schema dimensional modeling to prevent cartesian fan-out. |
| **Referential Integrity** | Zero orphan child records across all core tables (`order_items`, `order_payments`, `order_reviews` to `orders`; `order_items` to `products` and `sellers`; `orders` to `customers`). | Clean foreign key structure allows robust 1-to-many relationships in PostgreSQL and Power BI. |
| **Delivery SLA Scope** | 96,478 orders have `order_status = 'delivered'` (97.02%). 8 delivered orders have null customer delivery dates; exactly **96,470 delivered orders** have valid delivery timestamps. | Delivery SLAs must strictly evaluate the 96,470 delivered orders with valid delivery dates. Non-delivered orders belong to order lifecycle analysis. |
| **Delivery Timeliness (Date-Level)** | On-time rate: **93.23%** ($N = 89,936$). Late delivery rate: **6.77%** ($N = 6,534$). Delay for late orders: Median **7.0 days** (Mean: 10.62 days; P90: 22.0 days; Max: 188.0 days). | Calendar date comparison correctly respects the 00:00:00 midnight truncation of estimated dates. |
| **Customer Satisfaction (H1)** | On-time delivered orders average review score: **4.2904 / 5.00** ($N = 89,443$). Late delivered orders average review score: **2.2705 / 5.00** ($N = 6,381$). Score gap: **-2.0199 points**. | Negative reviews (1–2 stars) surge from **9.27%** among on-time orders to **62.42%** among late orders (a **6.73-fold increase**). |
| **Review Survey Timing (`review_created_before_delivery`)** | Among reviewed late orders, **74.46% ($N = 4,751$) were reviewed BEFORE delivery occurred**, averaging **1.8396 stars** (75.23% 1–2 stars). Late orders reviewed AFTER delivery ($N = 1,630$) average **3.5264 stars**. | Much of the severe review penalty reflects customers surveyed or venting while still awaiting an overdue parcel. |
| **Fulfillment Durations (H3 Baseline)** | **Handling Time:** Mean 2.80 days (all non-null, $N = 96,455$); **2.85 days** excluding 1,350 negative duration rows ($N = 95,105$).<br>**Transit Time:** Mean 9.33 days (all non-null, $N = 96,469$); **9.36 days** excluding all chronological anomalies ($N = 95,084$). | Carrier transit time accounts for ~76.6% of the clean delivery cycle duration (9.36 / 12.21 days). |
| **Financial Discrepancy** | Total Payments captured: **R$ 16,008,872.12** vs. Total Item Spend (Price + Freight): **R$ 15,843,553.24** (Difference: +R$ 165,318.88). | Fully reconciled: 775 orders have no items in `order_items` (mostly `unavailable` / `canceled`), accounting for R$ 162,591.95 in captured payments; 380 orders have minor installment/rounding differences (R$ 2,870.39); 1 order has items but no payment (R$ 143.46). |
| **Temporal Coverage** | Orders span 2016-09-04 to 2018-10-17. Core steady-state operational reporting window: **2017-01-01 to 2018-08-31** (**99,092 orders**, **99.65%** of dataset). 349 fringe orders excluded. | Prevents seasonality and volume distortions associated with thin pilot/ramp-down months. |
| **Geolocation Gaps** | **157 customer zip prefixes** missing from geolocation table, affecting **278 customers** and **278 orders**. **7 seller zip prefixes** missing, affecting **7 sellers**. | Mapped via city/state centroid fallback in derived geography dimension. |

---

## 2. Per-Table Detailed Profiles

### Summary of Tables Profiled

| Table Name | Raw File Name | Row Count | Col Count | Exact Duplicates | Primary Key / Grain | Uniqueness Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **customers** | `olist_customers_dataset.csv` | 99,441 | 5 | 0 | `customer_id` | 100% Unique (99,441) |
| **orders** | `olist_orders_dataset.csv` | 99,441 | 8 | 0 | `order_id` | 100% Unique (99,441) |
| **order_items** | `olist_order_items_dataset.csv` | 112,650 | 7 | 0 | `(order_id, order_item_id)` | 100% Unique (112,650) |
| **order_payments** | `olist_order_payments_dataset.csv` | 103,886 | 5 | 0 | `(order_id, payment_sequential)` | 100% Unique (103,886) |
| **order_reviews** | `olist_order_reviews_dataset.csv` | 99,224 | 7 | 0 | `(order_id)` via deduplication | `review_id` has 98,410 unique; `order_id` has 98,673 unique |
| **products** | `olist_products_dataset.csv` | 32,951 | 9 | 0 | `product_id` | 100% Unique (32,951) |
| **sellers** | `olist_sellers_dataset.csv` | 3,095 | 4 | 0 | `seller_id` | 100% Unique (3,095) |
| **geolocation** | `olist_geolocation_dataset.csv` | 1,000,163 | 5 | 261,831 | `geolocation_zip_code_prefix` (19,015) | Multi-row coordinate observations per prefix |
| **category_translation** | `product_category_name_translation.csv` | 71 | 2 | 0 | `product_category_name` | 100% Unique (71) |

---

## 3. Referential Integrity & Foreign Key Cardinality

```
orders.customer_id ------------ (1:1) ------------> customers.customer_id   [0 orphans; 0 unused]
order_items.order_id ---------- (N:1) ------------> orders.order_id          [0 orphans; 775 orders without items]
order_items.product_id -------- (N:1) ------------> products.product_id      [0 orphans; 0 unused]
order_items.seller_id --------- (N:1) ------------> sellers.seller_id        [0 orphans; 0 unused]
order_payments.order_id ------- (N:1) ------------> orders.order_id          [0 orphans; 1 order without payments]
order_reviews.order_id -------- (N:1) ------------> orders.order_id          [0 orphans; 768 orders without reviews]
```

### Key Referential Integrity Findings:
1. **Zero Child Orphans:** Across all 112,650 order items, 103,886 payments, 99,224 reviews, and 99,441 orders, there are **0 orphan child records**.
2. **Orders Without Items (775 orders):** 603 `unavailable`, 164 `canceled`, 5 `created`, 2 `invoiced`, 1 `shipped`.
3. **Orders Without Payments (1 order):** `bfbd0f9bdef84302105ad712db648a6c` (delivered status, 1 item: R$ 143.46).
4. **Geolocation Coverage Gaps:**
   - **157 customer zip code prefixes** missing from geolocation table, affecting **278 customers** (and 278 orders).
   - **7 seller zip code prefixes** missing from geolocation table, affecting **7 sellers**.
5. **Product Category Translation Gaps:**
   - 2 Portuguese categories in `products` are absent from `product_category_name_translation.csv`:
     - `pc_gamer` (3 products, 9 items)
     - `portateis_cozinha_e_preparadores_de_alimentos` (10 products, 15 items)
   - 610 products (1,603 order items) have null `product_category_name`.

---

## 4. Delivery SLA Performance: Date-Level vs. Timestamp-Level Comparison

In the raw data, `order_estimated_delivery_date` has a zeroed time component (`00:00:00`). Evaluating on-time delivery at the raw timestamp level incorrectly penalizes orders delivered on the promised day after midnight. 

Evaluating at the **calendar date grain** (`DATE(order_delivered_customer_date) > DATE(order_estimated_delivery_date)`) provides the true business SLA performance:

| Delivery Metric | Timestamp-Level (Sensitive) | Date-Level (Canonical SLA) | Variance / Adjustment |
| :--- | :--- | :--- | :--- |
| **Delivered Cohort (with Date)** | 96,470 | **96,470** | 0 |
| **On-Time Delivered Orders** | 88,644 (91.89%) | **89,936 (93.23%)** | +1,292 orders reclassified as on-time |
| **Late Delivered Orders** | 7,826 (8.11%) | **6,534 (6.77%)** | -1,292 orders corrected |
| **Late Delivery Delay (Median)** | 5.81 days | **7.00 days** | Measured in whole calendar days |
| **Late Delivery Delay (Mean)** | 9.55 days | **10.62 days** | Measured in whole calendar days |
| **Late Delivery Delay (P90)** | 21.54 days | **22.00 days** | Measured in whole calendar days |
| **Late Delivery Delay (Max)** | 188.98 days | **188.00 days** | Measured in whole calendar days |

```python
# Code used to compute canonical Date-Level SLA:
delivered["delivered_date_only"] = delivered["order_delivered_customer_date"].dt.normalize()
delivered["estimated_date_only"] = delivered["order_estimated_delivery_date"].dt.normalize()
delivered["is_late_date"] = delivered["delivered_date_only"] > delivered["estimated_date_only"]
delivered["is_on_time_date"] = delivered["delivered_date_only"] <= delivered["estimated_date_only"]
# Results: Late: 6,534 (6.77%), On-Time: 89,936 (93.23%)
```

---

## 5. Review Ratings & Customer Satisfaction Dynamics (Hypothesis 1)

Deduplicating reviews to the latest review per order yields **98,673 reviewed orders**, of which **95,824 belong to the delivered cohort**.

### 5.1 Review Score Distribution by Delivery Timeliness (Date-Level)

| Metric / Star Rating | On-Time Delivered Orders | Late Delivered Orders | Total Delivered Cohort | Score Delta / Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Reviewed Orders ($N$)** | **89,443** | **6,381** | **95,824** | — |
| **Average Review Score** | **4.2904** | **2.2705** | **4.1559** | **-2.0199 points** |
| **1–2 Stars (Negative %)** | **9.27%** (8,289) | **62.42%** (3,983) | 12.81% (12,272) | **+53.15% (6.73x surge)** |
| **3 Stars (Neutral %)** | **8.07%** (7,222) | **10.88%** (694) | 8.26% (7,916) | +2.81% |
| **4 Stars (Positive %)** | **20.39%** (18,239) | **10.17%** (649) | 19.71% (18,888) | -10.22% |
| **5 Stars (Delight %)** | **62.27%** (55,693) | **16.53%** (1,055) | 59.22% (56,748) | **-45.74%** |

### 5.2 Deep Dive: Review Submission Timing (`review_created_before_delivery`)

By comparing `review_creation_date` against `order_delivered_customer_date`, we observe a profound operational phenomenon:

```python
deliv_rev["review_creation_date_only"] = deliv_rev["review_creation_date"].dt.normalize()
deliv_rev["review_created_before_delivery"] = deliv_rev["review_creation_date_only"] < deliv_rev["delivered_date_only"]
```

| Delivery Cohort | Reviewed Before Delivery ($N$) | % of Cohort | Avg Review Score | % 1–2 Stars | Reviewed On/After Delivery ($N$) | % of Cohort | Avg Review Score | % 1–2 Stars |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **On-Time Orders** | 225 | 0.25% | 3.9378 | 15.11% | **89,218** | 99.75% | **4.2913** | 9.25% |
| **Late Orders** | **4,751** | **74.46%** | **1.8396** | **75.23%** | **1,630** | 25.54% | **3.5264** | 25.09% |

> [!IMPORTANT]
> **Key Analytical Takeaway for Hypothesis 1:**  
> 74% of reviews on late orders were created after the estimated date but before delivery (4,692 after the estimated date, 5 on the estimated date, and 54 before the estimated date), and score much lower than post-delivery reviews (1.84 vs 3.53). The data cannot tell us why. The late-order review penalty is heavily concentrated in these pre-delivery reviews.

---

## 6. Fulfillment Durations & Anomaly Isolation (Hypothesis 3 Baseline)

### 6.1 Chronological Violations in Fulfillment Milestones
- **Carrier dispatch before order approval:** 1,350 delivered orders ($t_{\text{carrier}} < t_{\text{approved}}$).
- **Customer delivery before carrier dispatch:** 23 delivered orders ($t_{\text{delivered}} < t_{\text{carrier}}$).

### 6.2 Fulfillment Durations With and Without Anomalies

| Duration Metric | All Non-Null Rows ($N$) | Mean (Days) | Median (Days) | Clean / Excluded Anomalies ($N$) | Clean Mean (Days) | Clean Median (Days) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Seller Handling Time** | 96,455 | 2.7990 | 1.8158 | **95,105** (excl. 1,350 negative) | **2.8534** | 1.8491 |
| **Carrier Transit Time** | 96,469 | 9.3303 | 7.0998 | **96,446** (excl. 23 negative) | **9.3333** | 7.1003 |
| **Transit Time (All Clean)**| 96,469 | 9.3303 | 7.0998 | **95,082** (excl. handling & transit < 0) | **9.3641** | 7.1103 |
| **Total Order Cycle Time** | 96,470 | 12.5583 | 10.2173 | **96,470** (purchase to delivery) | **12.5583** | 10.2173 |

*Conclusion:* In clean operations, carrier transit duration averages **9.36 days** (~76.6% of the cycle), while merchant handling averages **2.85 days** (~23.4% of the cycle).

---

## 7. Reporting Window Definition & Volume Audit

```python
# Code used for window filtering:
window_mask = (orders["order_purchase_timestamp"] >= "2017-01-01 00:00:00") & (orders["order_purchase_timestamp"] <= "2018-08-31 23:59:59")
# Window count: 99,092 orders (99.649% of 99,441 total orders)
```

- **Steady-State Operational Window:** **2017-01-01 through 2018-08-31** (**99,092 orders**, **99.65%** of total volume).
- **Excluded Fringe Orders (349 total):**
  - 2016-09: 4 orders (initial pilot launch)
  - 2016-10: 324 orders (beta launch)
  - 2016-12: 1 order (anomalous transaction)
  - 2018-09: 16 orders (system phase-out)
  - 2018-10: 4 orders (trailing records)

---

## 8. Canonical Control Totals (Pandas Baseline for SQL & DAX)

```
========================================================================================
CANONICAL CONTROL TOTAL BENCHMARK (PANDAS BASELINE - v1.1.0)
========================================================================================
Total Orders Count:                              99,441
Total Order Items Count:                        112,650
Total Order Payments Count:                     103,886
Total Order Reviews Count (Raw):                 99,224
Deduplicated Order Reviews Count:                98,673
Total Distinct Customers (customer_id):          99,441
Total Distinct Entities (customer_unique_id):    96,096
Repeat Customers Count (>= 2 orders):             2,997
Repeat Customer Rate (%):                        3.1188%

Delivered Orders (Status = 'delivered'):         96,478
Delivered Orders with Delivery Date:             96,470
Delivered Order Items:                          110,189

DATE-LEVEL DELIVERY SLA BENCHMARKS:
On-Time Delivered Orders (Date-Level):           89,936
Late Delivered Orders (Date-Level):               6,534
On-Time Delivery Rate (Date-Level %):           93.2269%
Late Delivery Rate (Date-Level %):               6.7731%

FINANCIAL CONTROL TOTALS:
Gross Item Revenue (All Items):                 R$ 13,591,643.70
Total Freight Billed (All Items):               R$  2,251,909.54
Total Customer Spend on Items:                  R$ 15,843,553.24
Total Captured Payments:                        R$ 16,008,872.12
Financial Discrepancy (Payments - Spend):       +R$   165,318.88

DELIVERED FINANCIAL TOTALS:
Delivered Item Revenue:                         R$ 13,220,248.93
Delivered Freight Billed:                       R$  2,198,145.90
Delivered Customer Spend:                       R$ 15,418,394.83

REVIEW & SATISFACTION BENCHMARKS (DATE-LEVEL):
Average Review Score (Raw All Reviews):          4.0864
Average Review Score (Deduplicated Orders):      4.0864
Average Review Score (Delivered Orders):         4.1559

On-Time Delivered Reviewed Orders Count:         89,443
On-Time Delivered Average Review Score:          4.2904
On-Time Delivered 1-2 Star Share (%):             9.27%
On-Time Delivered 5 Star Share (%):              62.27%

Late Delivered Reviewed Orders Count:             6,381
Late Delivered Average Review Score:             2.2705
Late Delivered 1-2 Star Share (%):               62.42%
Late Delivered 5 Star Share (%):                 16.53%
========================================================================================
```
