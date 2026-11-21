# Dashboard Page 4: Customer Satisfaction, Review Timing & Retention
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Audience:** Chief Marketing Officer (CMO), Head of Customer Retention, Product Quality Managers.  
**Canvas Dimensions:** 16:9 Standard (1280 x 720 px).  
**Primary Objective:** Test Hypotheses 1 and 4 by isolating the satisfaction penalty of delayed delivery, analyzing review submission timing, verifying category invariance, examining freight economics, and measuring long-term customer repeat purchasing behavior.

---

### Layout Grid & Visual Structure

```
+--------------------------------------------------------------------------------------------------+
| HEADER: Customer Satisfaction & Retention Impact | Slicers: Product Category / Cohort Selection   |
+--------------------------------------------------------------------------------------------------+
| KPI CARDS BANNER (Row 1: Height=80):                                                             |
| [On-Time Score]    [Late Score]       [Satisfaction Gap]   [Pre-Delivery Share] [Repeat Gap pp]  |
| 4.29 stars (89.4k) 2.27 stars (6.38k) -2.02 points (-47%)  74.46% (1.84 stars)  -0.52 to -1.35 pp|
+-------------------------------------------------+------------------------------------------------+
| VISUAL 1 (Top Left 50%): Rating Distribution    | VISUAL 2 (Top Right 50%): Review Timing Split  |
| 100% Stacked Bar: On-Time vs Late Stars         | Clustered Column: Pre vs Post Delivery Late    |
| - On-Time: 9.3% Neg (1-2★) | 62.3% 5-Star (5★)  | - Pre-Delivery (N=4,751): 1.84★, 75.2% Neg     |
| - Late:    62.4% Neg (1-2★) | 16.5% 5-Star (5★)  | - Post-Delivery (N=1,630): 3.53★, 25.1% Neg    |
| Late delivery associates with 6.7x negative reviews | 74.5% of late reviews occur pre-delivery (1.84★)|
+-------------------------------------------------+------------------------------------------------+
| VISUAL 3 (Bottom Left 50%): Freight by Weight   | VISUAL 4 (Bottom Right 50%): Retention Cohorts |
| Line Chart: Median Freight per kg by Distance:  | Grouped Bar / Matrix with 95% Error Bars:      |
| Light:  R$ 30.10 -> R$ 78.60/kg (+161%)         | - Full Cohort: 3.04% vs 2.52% (Gap -0.52 pp)   |
| Medium: R$ 7.60  -> R$ 18.50/kg (+143%)         | - Mature Cohort (< Oct 2017): 5.13% vs 3.78%   |
| Heavy:  R$ 2.36  -> R$ 6.21/kg  (+163%)         |   (Gap -1.35 pp [95% CI: -2.61 to -0.09 pp])   |
| Freight/kg escalates >140% across weight tiers  | Observational note: Clustered by state/seller  |
+--------------------------------------------------------------------------------------------------+
```

---

### Visual Specifications

#### 1. KPI Cards Banner
- **Card 1: On-Time Customer Rating Baseline**
  - Measure: `[Average Review Score (On-Time)]` (4.29 stars across 89,443 reviewed orders)
- **Card 2: Late Delivery Customer Rating**
  - Measure: `[Average Review Score (Late)]` (2.27 stars across 6,381 reviewed orders)
- **Card 3: Net Satisfaction Penalty**
  - Measure: `[Review Score Gap (Late vs On-Time)]` (-2.02 points, a 47.1% rating contraction)
- **Card 4: Pre-Delivery Review Concentration**
  - Measure: `[Pre-Delivery Late Review Share %]` (74.46% of late reviews, $N = 4,751$; avg 1.84 stars)
- **Card 5: Repeat Purchase Retention Deficit**
  - Value: -0.52 pp (Full Cohort) to -1.35 pp (Mature Cohort, $p = 0.038$)

#### 2. Visual 1: Star Rating Distribution Shift (H1 Test)
- **Visual Type:** 100% Stacked Bar Chart (Horizontal)
- **Y-Axis:** Delivery Timeliness (`On-Time Delivery` vs `Late Delivery`)
- **X-Axis Values:**
  - 1-2 Stars (Negative): Red `#D83B01`
  - 3 Stars (Neutral): Amber `#F39C12`
  - 4 Stars (Satisfied): Steel Blue `#2C5364`
  - 5 Stars (Delighted): Forest Green `#00A86B`
- **Data Labels:**
  - On-Time ($N = 89,443$): 9.27% negative (1–2★), 8.07% neutral (3★), 20.39% good (4★), **62.27% top-tier (5★)**.
  - Late ($N = 6,381$): **62.42% negative (1–2★)**, 10.88% neutral (3★), 10.17% good (4★), 16.53% top-tier (5★).
- **Core Insight:** Late delivery drives a **6.73-fold expansion in negative feedback**, shifting the modal experience from 5 stars to 1 star.

#### 3. Visual 2: Review Timing Dissection (Pre-Delivery vs Post-Delivery)
- **Visual Type:** Clustered Column Chart
- **X-Axis:** Timing Cohort (`Reviewed Before Delivery` vs `Reviewed On/After Delivery`)
- **Series:** Delivery SLA (`Late Delivery` vs `On-Time Delivery`)
- **Y-Axis:** Average Review Score (1.0 to 5.0)
- **Data Callout:**
  - Late orders reviewed before delivery ($N = 4,751$, 74.5% share) average an abysmal **1.84 stars** (75.2% 1–2 star).
  - Late orders reviewed after package arrival ($N = 1,630$, 25.5% share) rebound to **3.53 stars** (37.1% 5-star).
  - For on-time orders, 99.75% of reviews occur after delivery, averaging 4.29 stars.

#### 4. Visual 3: Freight Burden per kg Across Distance & Weight Tiers (H4 Test)
- **Visual Type:** Line Chart
- **X-Axis:** `distance_band` (`1. Local`, `2. Regional`, `3. Medium`, `4. Long`, `5. Remote`)
- **Legend:** `weight_tier` (`1. Light (<1kg)`, `2. Medium (1-5kg)`, `3. Heavy (5kg+)`)
- **Y-Axis:** Median Freight per kg (BRL/kg)
- **Key Takeaway:** Holding weight constant, freight per kg escalates monotonically by **2.43x to 2.63x** from Local to Remote across all tiers:
  - Light: R\$ 30.10/kg $\rightarrow$ R\$ 78.60/kg (+161%)
  - Medium: R\$ 7.60/kg $\rightarrow$ R\$ 18.50/kg (+143%)
  - Heavy: R\$ 2.36/kg $\rightarrow$ R\$ 6.21/kg (+163%)
- Consistent with Hypothesis 4: geographic distance is associated with higher freight burden even after controlling for physical package weight.

#### 5. Visual 4: Customer Retention & Repeat Buying Cohorts (Q12)
- **Visual Type:** Clustered Column Chart with Error Bars (95% CI)
- **X-Axis:** Cohort Scope (`Full Dataset (Delivered-Only)` vs `Mature Cohort (< 2017-10-01, All Orders)` vs `Mature Cohort (< 2017-10-01, Delivered-Only)`)
- **Legend:** Initial Delivery Outcome (`First Order On-Time` vs `First Order Late`)
- **Y-Axis:** Repeat Customer Rate %
- **Values & Error Bars:**
  - **Full Dataset (Delivered-Only, $N = 93,350$):**
    - On-Time: 3.04% [95% CI: 2.92%, 3.15%]
    - Late: 2.52% [95% CI: 2.13%, 2.90%]
    - **Difference Gap:** **-0.52 pp** [95% CI of difference: **-0.92 pp to -0.12 pp**] ($p = 0.016$)
  - **Mature Cohort (< 2017-10-01, All Orders, $N = 25,668$, $\ge 11$ mo follow-up):**
    - On-Time: 5.13% [95% CI: 4.85%, 5.40%]
    - Late: 3.78% [95% CI: 2.55%, 5.00%]
    - **Difference Gap:** **-1.35 pp** [95% CI of difference: **-2.61 pp to -0.09 pp**] ($p = 0.038$)
  - **Mature Cohort (< 2017-10-01, Delivered-Only, $N = 25,668$):**
    - On-Time: 4.89% [95% CI: 4.62%, 5.16%]
    - Late: 3.56% [95% CI: 2.37%, 4.75%]
    - **Difference Gap:** **-1.33 pp** [95% CI of difference: **-2.55 pp to -0.11 pp**] ($p = 0.039$)
- **Methodological & Observational Caution Callout:**
  - *Confidence Intervals:* While separate confidence intervals overlap in the mature cohort due to sample size disparity ($N = 927$ vs $N = 24,741$), the confidence interval of the *difference in proportions* strictly excludes zero.
  - *Non-Random Assignment:* Because delivery delays cluster geographically (e.g., Rio de Janeiro, Alagoas) and by seller dispatch behavior, customers receiving late deliveries are not randomly assigned. These findings demonstrate a statistically significant **observational association**, not causal attribution.
  - *Cohort Slicer Independence Note:* Customer cohort retention measures evaluate at the customer entity grain on `dim_customer`. Because the dimensional relationship flows from `dim_customer` (1) to `fact_order_delivery` (*), slicers placed on fact attributes (such as purchase date ranges in `dim_date` or destination states in `fact_order_delivery`) do not filter `dim_customer`. This is architecturally intentional for cohort metrics: a customer's lifetime repeat classification is a persistent property of that customer's cohort, not a transactional slice. Slicing by customer-level geography (`dim_customer[primary_state]`) will filter both tables.
