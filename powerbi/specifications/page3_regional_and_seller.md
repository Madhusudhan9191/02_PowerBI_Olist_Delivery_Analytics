# Dashboard Page 3: Regional Logistics & Seller Operations
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Audience:** VP of Marketplace, Regional Operations Directors, Merchant Success Leads.  
**Canvas Dimensions:** 16:9 Standard (1280 x 720 px).  
**Primary Objective:** Test Hypothesis 2 by evaluating state-level delivery performance against distance mix-adjusted benchmarks, explaining ETA buffer dynamics, and auditing merchant fulfillment across seller volume tiers.

---

### Layout Grid & Visual Structure

```
+--------------------------------------------------------------------------------------------------+
| HEADER: Regional Disparities & Merchant Fulfillment | Slicers: Destination State / Seller Tier   |
+--------------------------------------------------------------------------------------------------+
| KPI CARDS BANNER (Row 1: Height=80):                                                             |
| [National On-Time %] [SP On-Time %]     [RJ Gap (pp)]       [Remote Buffer (AM/RO)] [Active Sellers]|
| 93.23% (96,470 val)  95.51% (40,494 ord)-5.41 pp (12,350)   +19.5d / +20.0d buffer  2,961 delivered |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 1 (Left 55%): Mix-Adjusted State Gaps    | VISUAL 2 (Right 45%): Promised ETA vs Actual   |
| Clustered Bar Chart: Actual vs Expected SLA %   | Scatter / Dumbbell Chart: Lead Time Buffer     |
| Shows Gap in Percentage Points (pp):            | - AM: Promised 45.9d | Actual 26.4d (Buffer +19.5d)|
| - Underperforming: AL (-11.68 pp), MA (-6.24 pp)| - RO: Promised 39.4d | Actual 19.4d (Buffer +20.0d)|
|   RJ (-5.41 pp), SE (-5.55 pp), ES (-3.33 pp)   | - RJ: Promised 27.0d | Actual 15.3d (Buffer +11.7d)|
| - Outperforming: AM (+9.22 pp), RO (+8.57 pp),  | - SP: Promised 19.8d | Actual 8.8d  (Buffer +11.0d)|
|   MT (+3.34 pp), PR (+2.60 pp), MG (+2.11 pp)   | Shows AM/RO have ~46d promised vs 26d actual   |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 3 (Bottom 100%): Merchant Fulfillment by Volume Tiers (Q08 Focus)                         |
| Table / Matrix Visual:                                                                           |
| Columns: Seller Tier | Active Sellers (N) | Delivered Orders (N) | On-Time % | Handling | Late Dispatch %|
| Tier 1: 500+ orders  | 26 sellers         | 23,759 orders        | 93.09%    | 3.05d    | 8.07%          |
| Tier 2: 100-499 ord  | 184 sellers        | 34,156 orders        | 93.48%    | 2.71d    | 9.31%          |
| Tier 3: 30-99 orders | 424 sellers        | 22,448 orders        | 93.34%    | 2.91d    | 9.86%          |
| Tier 4: <30 orders   | 2,325 sellers      | 15,563 orders        | 93.38%    | 3.04d    | 11.07%         |
+--------------------------------------------------------------------------------------------------+
```

---

### Modeling Architecture & Cross-Filtering Decision

> **Critical Data Modeling Requirement: Bidirectional Filtering**
> - The relationship between `fact_order_delivery` (1) and `fact_order_items` (*) is configured with **Both** (Bidirectional) cross-filter direction in the semantic model.
> - **Why Bidirectional?**
>   - In this star schema, seller attributes (`dim_seller[seller_tier]`, `dim_seller[seller_state]`) and product attributes (`dim_product[product_category_name_en]`) connect at the item grain (`fact_order_items`).
>   - Order-level delivery outcomes (`is_on_time`, `handling_days`, `delay_days`, `review_score`) reside at the order grain (`fact_order_delivery`).
>   - Bidirectional filtering enables slicers on `dim_seller` and `dim_product` to filter `fact_order_delivery` dynamically, ensuring that all delivery metrics, SLA rates, and review scores accurately slice across seller tiers and product categories.
>
> **Important Modeling Caveat (Multi-Seller Order Overlap):**
> - While bidirectional filtering enables slicers on `dim_seller` to filter `fact_order_delivery`, **exactly 825 clean delivered orders contain items from sellers in multiple volume tiers**.
> - Slicing order counts by `dim_seller[seller_tier]` in a visual yields 95,926 tier-order instances across the four cohorts, compared to 95,082 deduplicated clean delivered orders (an 844-order overlap / 0.89%).
> - Slicing order-grain payments (`Captured Payment Value`) by seller tier will double-count payments on multi-seller orders, whereas item-grain merchandise spend (`Gross Item Revenue` = `fact_order_items[price]`) never double-counts.
> - *Architectural Alternative:* If single-direction modeling is preferred, keep this relationship Single and embed `CROSSFILTER(fact_order_delivery[order_id], fact_order_items[order_id], Both)` strictly inside the specific seller-focused DAX measures.

---

### Visual Specifications

#### 1. KPI Cards Banner
- **Card 1: National On-Time Baseline**
  - Measure: `[On-Time Delivery Rate %]` (93.23% across 96,470 valid delivered orders)
- **Card 2: Top Market Performance (São Paulo)**
  - Value: 95.51% on-time delivery across 40,494 delivered orders (+1.07 pp mix gap)
- **Card 3: Critical Regional Deficit (Rio de Janeiro)**
  - Value: 87.89% on-time delivery across 12,350 delivered orders (-5.41 pp mix gap)
- **Card 4: Remote Buffer Cushion (Amazonas & Rondônia)**
  - Value: +19.5d / +20.0d safety buffer (AM: 97.24% SLA; RO: 97.12% SLA)
- **Card 5: Active Marketplace Merchants**
  - Value: 2,959 active sellers with clean delivered orders (out of 3,095 total sellers in dataset)

#### 2. Visual 1: State Mix-Adjusted Performance Gaps (pp) (Q07)
- **Visual Type:** Clustered Bar Chart (Horizontal)
- **Y-Axis:** `fact_order_delivery[order_customer_state]` (All 27 Brazilian States)
- **X-Axis Values:**
  - Bar 1: `[On-Time Delivery Rate %]` (Actual, Blue `#0078D4`)
  - Bar 2: `[Expected On-Time Rate %]` (Distance Mix Benchmark, Gray `#9CA3AF`)
- **Tooltip / Secondary Measure:** `[Mix-Adjusted Performance Gap pp]`
- **Conditional Formatting:**
  - Green for positive gap ($\ge +1.0\text{ pp}$): AM (+9.22 pp), RO (+8.57 pp), MT (+3.34 pp), PR (+2.60 pp), MG (+2.11 pp), DF (+1.81 pp), RS (+1.49 pp), PE (+1.36 pp), SP (+1.07 pp).
  - Red for negative gap ($\le -2.0\text{ pp}$): AL (-11.68 pp), MA (-6.24 pp), SE (-5.55 pp), RJ (-5.41 pp), ES (-3.33 pp), PI (-3.07 pp), BA (-2.90 pp), CE (-2.33 pp), MS (-2.21 pp).

#### 3. Visual 2: Promised Lead Time vs Actual Cycle Days (Dumbbell / Scatter)
- **Visual Type:** Scatter Chart / Line-connected Markers
- **X-Axis:** Lead Time in Days (0 to 50 days)
- **Y-Axis:** Selected Benchmark States (`AM`, `RO`, `PA`, `AL`, `MA`, `RJ`, `MG`, `SP`)
- **Markers:**
  - Marker 1: `[Average Promised Lead Time Days]` (Circle, Coral `#D83B01`)
  - Marker 2: `[Average Actual Cycle Days]` (Square, Electric Blue `#0078D4`)
- **Key Insight Annotation:**
  - AM: 45.9d promised vs 26.4d actual $\rightarrow$ **19.5-day safety buffer** (associated with 97.24% on-time delivery).
  - RO: 39.4d promised vs 19.4d actual $\rightarrow$ **20.0-day safety buffer** (associated with 97.12% on-time delivery).
  - RJ: 27.0d promised vs 15.3d actual $\rightarrow$ **11.7-day safety buffer** (associated with 87.89% on-time delivery).
  - SP: 19.8d promised vs 8.8d actual $\rightarrow$ **11.0-day safety buffer** (associated with 95.51% on-time delivery).
  - AL: 33.2d promised vs 24.5d actual $\rightarrow$ **8.7-day safety buffer** (associated with 78.59% on-time delivery).

#### 4. Visual 3: Merchant Fulfillment by Seller Volume Tiers (Q08)
- **Visual Type:** Matrix / Table Visual
- **Rows:** `dim_seller[seller_tier]`
- **Columns:**
  1. `[Total Active Sellers]` ($N_{\text{active}} = 2,959$; Note: All 3,095 sellers categorized into T1: 26, T2: 184, T3: 424, T4: 2,461)
  2. `[Valid Delivered Orders]` (T1: 23,759, T2: 34,156, T3: 22,448, T4: 15,563)
  3. `[On-Time Delivery Rate %]` (T1: 93.09%, T2: 93.48%, T3: 93.34%, T4: 93.38%)
  4. `[Average Handling Days]` (T1: 3.05d, T2: 2.71d, T3: 2.91d, T4: 3.04d)
  5. `[Late Dispatch Rate %]` (T1: 8.07% [$2,175 / 26,955$ items], T2: 9.31% [$3,566 / 38,299$ items], T3: 9.86% [$2,497 / 25,316$ items], T4: 11.07% [$1,994 / 18,011$ items])
  6. `[Average Review Score]` (T1: 4.02, T2: 4.08, T3: 4.11, T4: 4.13)
  7. `[Sample Size Status]` (All tiers: `interpretable` with $N \ge 15,563$)
- **Key Operational Finding:** Mid-volume merchants in **Tier 3 (30–99 orders)** manage 22,448 orders with 93.34% on-time delivery and 2.91 handling days. Merchant late dispatch increases among long-tail micro-sellers in Tier 4 (11.07%), but overall customer delivery compliance remains insulated by carrier buffers.
