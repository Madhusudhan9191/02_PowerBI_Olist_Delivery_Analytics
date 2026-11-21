# Dashboard Page 1: Executive Logistics & SLA Overview
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Audience:** Chief Operating Officer (COO), VP of Logistics, Head of Customer Experience.  
**Canvas Dimensions:** 16:9 Standard (1280 x 720 px).  
**Primary Color Palette:** Charcoal `#111827`, Electric Blue `#0078D4`, Forest Green `#00A86B`, Coral Alert `#D83B01`, Slate Grey `#9CA3AF`.

---

### Layout Grid & Visual Structure

```
+--------------------------------------------------------------------------------------------------+
| HEADER BAR: Project Title, Subtitle, Portfolio Disclaimer, and Date Range Filter Slicer          |
+--------------------------------------------------------------------------------------------------+
| KPI CARDS BANNER (Row 1: Y=80, Height=90):                                                       |
| [1. Gross Item Spend]  [2. Billed Orders]  [3. On-Time Rate %]  [4. Avg Delay]  [5. Avg Rating]   |
| R$ 15.84M              99,441 (96,470 val) 93.23% (Target 95%)  10.62 days      4.09 stars        |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 1 (Left 60%): Monthly Operational Trend  | VISUAL 2 (Right 40%): Delivery SLA Breakdown   |
| Combo Line & Clustered Column Chart:            | Donut Chart across All 99,441 Orders:          |
| - Columns: Total Delivered Orders               | - On-Time Delivered: 89,936 (90.44%)           |
| - Line 1: On-Time Delivery Rate %               | - Late Delivered: 6,534 (6.57%)                |
| - Line 2: 95.0% Operational Target Benchmark    | - Non-Delivered: 2,963 (2.98%)                 |
| Highlights Black Friday 2017 & March 2018 dips  | - Delivered (Missing Date): 8 (0.01%)          |
|                                                 | Total Sum = 99,441 (100.00%)                   |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 3 (Bottom Left 50%): Lead Time Milestones| VISUAL 4 (Bottom Right 50%): Executive Findings |
| Horizontal Lead Time Breakdown Bar:             | Analytical Callout Card / Matrix:              |
| - Merchant Handling: 2.85 days (23.3%)          | - Steady-State Orders: 99,092 (99.65%)         |
| - Carrier Transit: 9.37 days (76.7%)            | - Black Friday (Nov 2017): 87.6% SLA (vs Oct 95.8%)|
| - End-to-End Cycle: 12.61 days (12.22d clean)   | - 2018 Dip: Feb 85.9%, Mar 81.0% (cause not in data)|
|                                                 | - Trend: Apr 95.5%, May 93.4%, Jun 98.8%       |
+--------------------------------------------------------------------------------------------------+
```

---

### Visual Specifications

#### 1. KPI Cards Banner (Top Grid)
- **Card 1: Customer Spend**
  - Measure: `[Total Customer Spend]` (R\$ 15.84M)
  - Secondary Label: Billed Items: R\$ 13.59M | Freight: R\$ 2.25M
- **Card 2: Total Orders**
  - Measure: `[Total Orders]` (99,441)
  - Sub-measure: `[Valid Delivered Orders]` (96,470 delivered with delivery timestamp)
- **Card 3: On-Time Delivery SLA**
  - Measure: `[On-Time Delivery Rate %]` (93.23%)
  - Target Reference: 95.00% (-1.77 pp variance)
  - Color Alert: Coral `#D83B01` if $< 95\%$, Green `#00A86B` if $\ge 95\%$.
- **Card 4: Average Delay Severity**
  - Measure: `[Average Delay Days (Late Orders)]` (10.62 calendar days; median 7.0 days, P90 22.0 days)
  - Subtitle: Late Orders: 6,534 (6.77% of valid delivered)
- **Card 5: Customer Satisfaction**
  - Measure: `[Average Review Score]` (4.09 stars on reviewed orders)
  - Total Reviewed Orders: 98,673

#### 2. Visual 1: Monthly Operational Trends (Combo Chart)
- **Visual Type:** Line and Clustered Column Chart
- **X-Axis:** `dim_date[year_month]` (Filtered to steady-state window `2017-01` to `2018-08`)
- **Column Values:** `[Valid Delivered Orders]`
- **Line Values:** `[On-Time Delivery Rate %]`
- **Reference Line:** Constant at `0.95` (95.0% Service Level Agreement)
- **Data Callouts:** Annotations on `2017-11` (Black Friday: 87.60% SLA, down from 95.8% in Oct 2017) and `2018-03` (Delivery SLA fell to 81.04%; cause not in the data). April reached 95.5%, May 93.4%, and June 98.8%.

#### 3. Visual 2: Order Delivery Status Breakdown (Donut Chart)
- **Visual Type:** Donut Chart
- **Field / Legend:** `fact_order_delivery[order_delivery_status_category]` (or slice `fact_order_delivery` by categories)
  - **On-Time Delivered:** 89,936 orders (90.44% of all orders; 93.23% of valid delivered)
  - **Late Delivered:** 6,534 orders (6.57% of all orders; 6.77% of valid delivered)
  - **Non-Delivered:** 2,963 orders (2.98% of all orders: canceled 625, unavailable 609, shipped 1,107, invoiced 314, processing 301, created 5, approved 2)
  - **Delivered (Missing Date):** 8 orders (0.01% of all orders: marked delivered in status but null delivery timestamp)
  - **Total Sum:** $89,936 + 6,534 + 2,963 + 8 = 99,441$ orders (100.00% complete reconciliation)
- **Colors:** On-Time `#00A86B`, Late `#D83B01`, Non-Delivered `#9CA3AF`, Delivered (Missing Date) `#F59E0B`.

#### 4. Visual 3: Lead Time Decomposition
- **Visual Type:** Clustered Bar Chart / KPI Cards
- **Population:** Evaluated on clean fulfillment population ($N = 95,082$ orders: `handling_days >= 0 AND transit_days >= 0`)
- **Metrics Displayed:**
  - `[Average Handling Days]` (2.85 days / 23.32% fulfillment share)
  - `[Average Transit Days]` (9.37 days / 76.68% fulfillment share)
  - `[Average Fulfillment Cycle Days]` (12.61 days total cycle)
- **Data Label:** Highlights that carrier transit represents over three-quarters of total fulfillment lead time.
