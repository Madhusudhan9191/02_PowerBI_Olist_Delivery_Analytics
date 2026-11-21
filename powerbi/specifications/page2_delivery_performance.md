# Dashboard Page 2: Delivery Performance & Fulfillment Bottlenecks
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Audience:** Director of Supply Chain, Logistics Operations Managers, Carrier Contract Leads.  
**Canvas Dimensions:** 16:9 Standard (1280 x 720 px).  
**Primary Objective:** Test Hypothesis 3 by decomposing end-to-end cycle times into merchant handling vs carrier transit, comparing intrastate vs interstate order flows, and surfacing top trade corridor bottlenecks.

---

### Layout Grid & Visual Structure

```
+--------------------------------------------------------------------------------------------------+
| HEADER: Delivery Bottlenecks & Trade Lanes | Slicers: Trade Flow (All/Interstate/Intrastate)     |
+--------------------------------------------------------------------------------------------------+
| KPI CARDS BANNER (Row 1: Height=80):                                                             |
| [Clean Orders N]   [Intrastate SLA %]  [Interstate SLA %]  [Avg Handling Days] [Avg Transit Days]|
| 95,082 orders      95.43% (34,060 ord) 91.89% (61,022 ord) 2.85 days (clean)   9.37 days (clean) |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 1 (Left 50%): Bottleneck Decomposition   | VISUAL 2 (Right 50%): Delay Severity Profile   |
| 100% Stacked Bar Chart:                         | Histogram / Column Chart of Late Delay Days:   |
| Intrastate vs Interstate Fulfillment Split:     | - 1 to 3 days late: 2,051 orders (31.4%)       |
| - Intrastate: Handling 36.6% | Transit 63.4%    | - 4 to 7 days late: 1,489 orders (22.8%)       |
| - Interstate: Handling 19.5% | Transit 80.5%    | - 8 to 14 days late: 1,444 orders (22.1%)      |
| Shows Transit represents >80% of cross-state lead time | - 15+ days late: 1,550 orders (23.7%)          |
+-------------------------------------------------+------------------------------------------------+
| VISUAL 3 (Bottom 100%): Top 20 Interstate Trade Corridors Matrix (Q10 Focus)                     |
| Matrix / Table with Data Bars:                                                                   |
| Columns: Corridor | Origin | Dest | Orders (N) | On-Time % | Carrier Transit (d) | Distance (km)  |
| Highlights SP -> RJ: 8,094 orders, 86.38% on-time, 12.65 days transit (vs 442 km avg distance) |
+--------------------------------------------------------------------------------------------------+
```

---

### Visual Specifications

#### 1. KPI Cards Banner
- **Card 1: Clean Fulfillment Cohort**
  - Measure: `[Clean Fulfillment Orders]` (95,082 orders)
  - Subtitle: Excludes 1,350 handling $<0$ and 23 transit $<0$ anomalies.
- **Card 2: Intrastate Delivery Compliance**
  - Measure: `[Intrastate On-Time Rate %]` (95.43%)
  - Subtitle: Orders: 34,060 (35.8% of clean volume) | Avg Transit: 4.82 days
- **Card 3: Interstate Delivery Compliance**
  - Measure: `[Interstate On-Time Rate %]` (91.89%)
  - Subtitle: Orders: 61,022 (64.2% of clean volume) | Avg Transit: 11.90 days
- **Card 4: Merchant Handling Time**
  - Measure: `[Average Handling Days]` (2.85 days on clean fulfillment cohort)
  - Subtitle: Intrastate: 2.79d | Interstate: 2.89d
- **Card 5: Carrier Transit Time**
  - Measure: `[Average Transit Days]` (9.37 days on clean fulfillment cohort)
  - Subtitle: Intrastate: 4.82d | Interstate: 11.90d (2.47x higher)

#### 2. Visual 1: Lead Time Contribution Decomposition (H3 Test)
- **Visual Type:** 100% Stacked Bar Chart
- **Y-Axis:** Route Flow Type (`Intrastate Flow (Within-State)` vs `Interstate Flow (Cross-State)`)
- **X-Axis Values:**
  - `[Average Handling Days]` (Blue `#0078D4`)
  - `[Average Transit Days]` (Teal-Navy `#203A43`)
- **Data Labels:**
  - Intrastate: Handling = 36.64%, Transit = 63.35% (Total = 7.99 days).
  - Interstate: Handling = 19.53%, Transit = 80.47% (Total = 15.20 days).
- **Core Insight Callout:** Carrier transit accounts for over **80% of total fulfillment time** on interstate shipments, showing that transit variations associate with cross-state lead times while merchant handling remains stable. Alagoas (AL) recorded Brazil's lowest on-time delivery rate at 78.59%, with Maranhão (MA) second lowest at 82.57%.

#### 3. Visual 2: Late Order Delay Days Severity Profile
- **Visual Type:** Clustered Column Chart
- **X-Axis:** Delay Bins (`1-3 days`, `4-7 days`, `8-14 days`, `15-30 days`, `31+ days`)
- **Y-Axis:** Count of Late Orders ($N = 6,534$)
- **Data Callout:** Median delay is 7.0 days; 76.3% of late orders arrive within 14 days of the promised date. Max delay reaches 188 days.

#### 4. Visual 3: Top Interstate Logistics Corridors Matrix (Q10)
- **Visual Type:** Table / Matrix Visual
- **Data Columns:**
  1. `trade_corridor` (e.g., `SP -> RJ`, `SP -> MG`, `SP -> RS`, `SP -> PR`, `PR -> SP`)
  2. `origin_state` & `destination_state`
  3. `[Valid Delivered Orders]` (with blue gradient data bar)
  4. `[On-Time Delivery Rate %]` (conditional formatting: Red $< 90\%$, Green $\ge 95\%$)
  5. `[Average Transit Days]`
  6. `[Average Merchant Handling Days]`
  7. `[Average Route Distance km]`
  8. `[Sample Size Status]` (All top 20 corridors are `interpretable` with $N \ge 946$)
- **Rio de Janeiro Pattern (RJ):** Statewide deliveries into RJ average 486.86 km route distance and 12.05 days carrier transit with an 87.89% on-time delivery rate (-5.41 pp below distance-mix expectation). The primary SP → RJ interstate corridor (8,094 orders) exhibits 12.65 days transit and 86.38% on-time delivery despite a 442 km route distance.
- **Key Bottleneck Alert:** Highlight `SP -> RJ` (8,094 orders; 86.38% on-time; 12.65 transit days; 442 km) vs `SP -> PR` (3,073 orders; 95.60% on-time; 9.42 transit days).
