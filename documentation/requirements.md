# Requirements Document
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Type:** Independent Portfolio Project  
**Author:** Software Engineer transitioning to Data Analyst / Junior Data Scientist  
**Data Source:** Olist Brazilian E-Commerce Public Dataset (Kaggle: `olistbr/brazilian-ecommerce`)  
**License:** CC BY-NC-SA 4.0  
**Version:** 1.1.0  
**Date:** 2026-11-14  

---

> [!NOTE]
> **Portfolio Project Disclosure:**  
> This project is an independent educational and analytical portfolio project using public, anonymized e-commerce data from Olist. It is **not** commissioned, sponsored, or endorsed by Olist, nor does it represent internal operational results of any enterprise. All simulated roles, scenarios, and business framing are created solely to demonstrate real-world analytical, data modeling, and business communication competency.

---

## 1. Business Problem & Project Objective

Olist operates a marketplace platform connecting small and medium merchants across Brazil to national retail marketplaces. In a marketplace model, logistics fulfillment and delivery reliability are critical determinants of customer retention, ratings, and marketplace brand equity. 

The objective of this project is to build an end-to-end analytical data product across **Python**, **PostgreSQL**, and **Power BI** that:
1. Evaluates delivery fulfillment performance (handling time, transit duration, on-time delivery rates, and estimate accuracy).
2. Quantifies the empirical association between fulfillment delays and customer review scores, controlling for product category mix and review submission timing (whether reviewed before or after actual delivery).
3. Identifies geographic and seller-level operational bottlenecks across Brazilian states.
4. Analyzes the freight cost burden relative to item price across regional trade lanes.
5. Implements rigorous data engineering, dimensional modeling (star schema), and automated three-way reconciliation (Python pandas vs. PostgreSQL vs. Power BI DAX) with zero tolerance for unverified numbers.

---

## 2. Simulated Stakeholder Personas & Analytical Needs

To establish realistic business requirements, three simulated stakeholder personas define the analytical scope and reporting perspectives:

### 2.1 VP of Customer Experience & Marketplace Trust *(Simulated Role)*
- **Primary Concerns:** Customer satisfaction trends, review score drivers, impact of service failure (late deliveries) on negative reviews (1–2 stars), category-level vulnerabilities, and customer survey timing dynamics (reviews triggered while orders remain overdue).
- **Key Decision Supported:** Proactive communication policies for delayed orders, survey trigger throttling for orders in-flight, and seller quality enforcement thresholds.

### 2.2 Head of Logistics & Carrier Management *(Simulated Role)*
- **Primary Concerns:** End-to-end delivery cycle time, carrier transit times vs. seller fulfillment lead times, geographic delivery variance across states/regions, carrier estimation accuracy, and handling/transit anomaly isolation.
- **Key Decision Supported:** Carrier contract evaluations, regional fulfillment center strategy, and delivery SLA tuning by destination state.

### 2.3 Director of Merchant Performance *(Simulated Role)*
- **Primary Concerns:** Merchant dispatch speed (order approval to carrier handoff), seller late-dispatch rates, seller volume distribution, and freight cost fairness across distance bands.
- **Key Decision Supported:** Merchant SLA policies, seller tiering, and seller onboarding in under-indexed geographic regions.

---

## 3. Core Hypotheses & Analytical Approach

All hypotheses are tested using observational data. Findings are reported strictly using associational and non-causal language (e.g., "associated with", "correlated with", rather than "causes", "proves", or "optimizes").

### Hypothesis 1 (H1): Delivery Delay, Review Timing, and Customer Satisfaction
- **Hypothesis:** Orders delivered after the estimated delivery date are associated with lower customer review scores compared to orders delivered on or before the estimated date, both overall and when controlling for product category mix. Furthermore, this negative rating gap is substantially driven by reviews created while customers are still awaiting delivery past the promise date (`review_created_before_delivery = TRUE`).
- **Metrics:** Average Review Score (1–5 scale), Late Delivery Rate (%), Negative Review Rate (% 1–2 stars), Positive Review Rate (% 5 stars).
- **Controls & Segmentation:** Product category grouping; review timing relative to delivery (`review_creation_date < delivered_date` vs. `review_creation_date >= delivered_date`).

### Hypothesis 2 (H2): Regional and Seller Fulfillment Heterogeneity
- **Hypothesis:** On-time delivery rates vary significantly across Brazilian destination states and across individual seller cohorts, reflecting regional logistics infrastructure disparities and merchant fulfillment discipline.
- **Metrics:** On-time Delivery Rate (%), Carrier Transit Duration (Days), Seller Handling Time (Days).
- **Sample Size Controls:** Seller cohorts stratified by volume; groups with < 30 orders suppressed, 30–99 flagged as exploratory, 100+ interpretable. Mix-adjusted benchmark comparisons implemented for regional rates.

### Hypothesis 3 (H3): Fulfillment Bottleneck Decomposition (Handling vs. Transit)
- **Hypothesis:** Total delivery cycle duration decomposes into seller dispatch handling time and carrier transit duration, with carrier transit duration accounting for the primary share of total variance and late delivery incidence on interstate routes.
- **Metrics:** Seller Handling Time (Days), Carrier Transit Time (Days), Total Order Cycle Time (Days), Route Distance (km).
- **Quality Rule:** Rows with chronological sequence violations ($t_{\text{carrier}} < t_{\text{approved}}$: 1,350 rows; $t_{\text{delivered}} < t_{\text{carrier}}$: 23 rows) are flagged and excluded from clean route-level duration models.
- **Segmentation:** Intrastate vs. Interstate order flows.

### Hypothesis 4 (H4): Freight Burden Across Geographic Distance
- **Hypothesis:** Freight value as a percentage of item price increases with geographic distance between seller and customer, creating higher friction for low-value goods and remote destination states.
- **Metrics:** Freight-to-Price Ratio (`freight_value / price`), Distance Band (km), Item Price Band (BRL).

---

## 4. Key Architectural & Data Modeling Decisions

| Decision Area | Chosen Approach | Rationale & Trade-offs |
| :--- | :--- | :--- |
| **Primary Grain for Financials** | `order_items` (`order_id` + `order_item_id`) | Items represent the fundamental revenue and product grain. Joining `order_payments` or `order_reviews` directly to items creates fan-out double counting. Payment and review metrics are aggregated to order grain first or modeled separately. |
| **Delivery Metrics Grain** | Order Grain (`order_id`) | Logistics milestones occur at the order level. Evaluating delivery performance at the item level would artificially overweight multi-item orders. Delivery KPIs are computed on order-grain derived facts. |
| **Customer Identity** | `customer_id` (transaction-level) mapped to `customer_unique_id` (entity-level) | In Olist, each row in `olist_customers_dataset` has a distinct `customer_id` generated per order. To analyze repeat buying, customer retention, or lifetime purchasing behavior, the persistent `customer_unique_id` must be used as the dimensional key. |
| **Review Deduplication** | 1 review per order; select latest by `review_answer_timestamp` (tie-breaker: `review_creation_date`, max `review_id`) | 547 orders contain multiple review submissions. Deduplicating to the latest review guarantees that each reviewed order contributes exactly once to order-level review aggregates. Missing reviews (768 orders) are tracked and excluded from rating averages without dropping orders. |
| **Delivery KPI Scope & Inclusions** | Delivered orders only (`order_status = 'delivered'` AND `order_delivered_customer_date IS NOT NULL`) | Evaluated on 96,470 orders with valid delivery dates (8 delivered orders with null delivery dates excluded). Non-delivered orders categorized under Lifecycle Funnel metrics. |
| **Definition of "Late Delivery"** | Calendar DATE comparison: $\text{DATE}(t_{\text{delivered}}) > \text{DATE}(t_{\text{estimated}})$ | `order_estimated_delivery_date` contains only calendar dates (midnight timestamps `00:00:00`). Comparing raw timestamps would misclassify orders delivered during the afternoon on the promised day as late. Date-level comparison correctly yields 6,534 late orders (6.77%) and 89,936 on-time orders (93.23%). |
| **Revenue Definition** | Item Price (`SUM(price)`) separated from Customer Spend (`SUM(price + freight_value)`) and Payment Value (`SUM(payment_value)`) | `price` reflects pure merchant merchandise value (R$ 13,591,643.70). `freight_value` reflects logistics charges (R$ 2,251,909.54). `payment_value` reflects actual captured money (R$ 16,008,872.12). Discrepancy (+R$ 165,318.88) is fully reconciled: 775 orders without items in `order_items` account for R$ 162,591.95; 380 orders have rounding/voucher diffs (R$ 2,870.39); 1 order has items without payment (R$ 143.46). |
| **Reporting Time Window** | **2017-01-01 to 2018-08-31** (99,092 orders, 99.65% of dataset) | Boundary months (2016-09, 2016-10, 2016-12, 2018-09, 2018-10) represent beta ramp-up and platform cutoff with thin or discontinuous volumes (349 total orders). Core operational reporting focuses on steady-state continuous operations. |
| **Geolocation & Geodesic Distance** | Deduplicate `geolocation_zip_code_prefix` by taking the median latitude and longitude per 5-digit prefix | Multiple rows exist per zip prefix. Aggregating to median coordinates eliminates cartesian joins while providing reliable centroids. 157 customer zip prefixes (affecting 278 orders) and 7 seller zip prefixes (affecting 7 sellers) missing from geolocation table will use city/state fallback centroids. |

---

## 5. Statistical & Sample Size Governance

| Sample Size ($N$) | Classification | Reporting Rule |
| :--- | :--- | :--- |
| **$N < 30$** | **Suppress** | Metrics are masked or explicitly flagged as insufficient sample size to draw conclusions. |
| **$30 \le N < 100$** | **Exploratory** | Metrics displayed with an informational caveat; suitable for directional insight only. |
| **$N \ge 100$** | **Interpretable** | Fully reportable for standard operational comparisons. |

For regional and seller comparisons, **mix-adjusted benchmarks** will be computed:
$$\text{Expected Rate} = \sum_{c} \left( w_c \times \bar{R}_c \right)$$
where $w_c$ is the share of orders in category/corridor $c$ for that entity, and $\bar{R}_c$ is the global rate for category/corridor $c$.

---

## 6. Document Change Log

| Version | Date | Section Affected | Change Description | Author / Role |
| :--- | :--- | :--- | :--- | :--- |
| **1.0.0** | 2026-11-14 | All | Initial baseline requirements document created for Phase 0 sign-off. | Lead Analyst |
| **1.1.0** | 2026-11-14 | 3, 4, 5 | Updated late delivery definition to DATE-level (`DATE(delivered) > DATE(estimated)`). Incorporated `review_created_before_delivery` timing flag into H1. Corrected reporting window order count to 99,092. Clarified handling/transit anomaly exclusion rules for H3. Corrected geolocation gap figures (157 customer prefixes / 278 orders; 7 seller prefixes / 7 sellers). | Lead Analyst |
