# Project Change Log
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Format:** [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [1.4.0] - 2026-11-16
### Added
- **Phase 5 Power BI Semantic Model Package Completed:**
  - `python/04_export_powerbi_csvs.py`: Re-runnable warehouse export script generating pre-cleaned, pre-typed CSV tables in `data/processed/powerbi_input/` for all 8 star schema tables.
  - `dim_date.csv` & `powerbi/power_query/dim_date.m`: Terminated explicitly at `2018-10-17` (the maximum date in the dataset, never `TODAY()`), eliminating dangling empty future calendar intervals.
  - Power Query M Scripts (`powerbi/power_query/`): Parameterized via `SourceFolder`, covering `dim_date`, `dim_geography`, `dim_customer`, `dim_seller`, `dim_product`, `fact_order_delivery`, `fact_order_items`, and `fact_order_payments`.
  - Star Schema Relationship Architecture: Single-direction $1:*$ relationships mapped from dimensional tables to `fact_order_delivery` and child facts (`fact_order_items`, `fact_order_payments`).
  - DAX Measure Library (`powerbi/dax/measures.dax`): 44 production DAX measures organized into 8 logical display folders (`01_Volume_and_Spend`, `02_Delivery_SLA`, `03_Review_Satisfaction`, `04_Fulfillment_Bottlenecks`, `05_Regional_and_Seller`, `06_Freight_Economics`, `07_Retention_and_Cohort`, `08_Sample_Size_Governance`).
  - DAX Verification & Reconciliation Test Table (`powerbi/dax/dax_test_table.md`): Pre-flight quality assurance table detailing all 44 measures with exact expected benchmarks and blank user-fill columns for Desktop QA verification.
  - Custom Accessible Theme (`powerbi/theme/olist_theme.json`): WCAG AA compliant palette (Charcoal `#111827`, Electric Blue `#0078D4`, Forest Green `#00A86B`, Coral Alert `#D83B01`, Steel Blue `#2C5364`, Warm Amber `#F39C12`).
  - 4-Page Dashboard Specifications (`powerbi/specifications/`):
    - Page 1: Executive Logistics & SLA Overview
    - Page 2: Delivery Performance & Fulfillment Bottlenecks (H3)
    - Page 3: Regional Logistics & Seller Operations (H2)
    - Page 4: Customer Satisfaction, Review Timing & Retention (H1 & H4)
  - End-to-End Build Guide (`powerbi/README_build_guide.md`): Step-by-step implementation guide detailing setup, model configuration, measure entry, and visual assembly.

### Fixed
- **Q12 Difference Confidence Intervals & Observational Note:** Computed and documented two-sample difference 95% confidence intervals: Full Cohort Delivered-Only gap = **-0.52 pp** [95% CI: **-0.92 pp to -0.12 pp**] ($p = 0.016$); Mature Cohort (< Oct 2017) gap = **-1.35 pp** [95% CI: **-2.61 pp to -0.09 pp**] ($p = 0.038$). Noted why separate CIs overlap while the difference CI excludes zero, and explicitly documented that customers receiving late deliveries are not randomly assigned (observational association only).
- **Hedged Analytical Conclusions Restored:** Regenerated [`documentation/business_queries_report.md`](business_queries_report.md) with short, hedged analytical commentary and sample sizes under all 12 business queries. Reported Q09 mixed-origin order share (240 orders / 0.25%).

## [1.3.1] - 2026-11-14
### Fixed
- **Q05 Sample Size Governance & Range Corrections:** Corrected narrative claim regarding product categories. Of the 63 categories with total orders $\ge 30$, late delivery sample size governance classifies 18 as interpretable ($N_{\text{late}} \ge 100$), 11 as exploratory ($30 \le N_{\text{late}} < 100$), and 34 as suppressed ($N_{\text{late}} < 30$). Across all 29 qualifying categories ($N_{\text{late}} \ge 30$), the satisfaction gap is strictly negative, ranging from -1.40 points (`office_furniture`, $N_{\text{late}} = 99$) to -2.51 points (`musical_instruments`, $N_{\text{late}} = 46$), correcting the prior approximation ("-1.7 to -2.3").
- **Q09 Order Double-Counting Elimination:** Fixed `SELECT DISTINCT` over item-level route flags that caused 240 multi-seller orders with mixed origins to be counted in both intrastate and interstate groups (totaling 95,322 vs 95,082 clean delivered orders). Re-architected query to aggregate route flags at order grain using `BOOL_OR(is_interstate)`: 61,022 Interstate Flow orders and 34,060 Intrastate Flow orders, summing exactly to 95,082 orders (zero double-counting). Noted 240 mixed-origin orders classified under interstate flow due to cross-state dependency.
- **Q06 & Q07 Order-Level Customer State Joins:** Replaced customer-level `dim_customer.primary_state` with order-level destination state from `raw_customers.customer_state` (joined on `d.customer_id = c.customer_id`), resolving 43 orders where customer delivery address differed from the latest account address. Corrected SP delivered order count to 40,494 (was 40,499) and MA on-time delivery rate to 82.57% ($N = 717$, was 82.59%).
- **Q07 Terminology & ETA Safety Buffer Dynamics:** Renamed performance gap column to `mix_adjusted_performance_gap_pp` and strictly labeled all percentage point differences as `pp` (never `%`). Added promised lead times and actual cycle days to illuminate why Amazonian states (AM: 97.24% on-time, RO: 97.12%) outperform southeastern hubs (RJ: 87.89%, SP: 95.51%): AM and RO receive generous promised lead times (45.9d and 39.4d vs actual cycle times of 26.4d and 19.4d, a ~19–20 day buffer), whereas RJ has tighter promised lead times (27.0d vs 15.3d actual cycle, a 11.7d buffer), rendering it vulnerable to carrier transit volatility.
- **Q12 Repeat Customer Rates, 95% Confidence Intervals & Maturity Cohort:** Re-structured Q12 to report binomial 95% confidence intervals, delivered-only repeat rates, and a mature customer cohort ($< \text{2017-10-01}$, providing $\ge 11$ months follow-up):
  - Full Dataset Delivered-Only Repeat: On-time 3.04% [95% CI: 2.92%, 3.15%] vs Late 2.52% [95% CI: 2.13%, 2.90%], gap = -0.52 pp [-0.94 pp, -0.10 pp] ($p = 0.016$).
  - Mature Cohort ($< \text{2017-10-01}$, All Orders): On-time 5.13% [95% CI: 4.85%, 5.40%] vs Late 3.78% [95% CI: 2.55%, 5.00%], gap = -1.35 pp [-2.63 pp, -0.07 pp] ($p = 0.038$).
  - Mature Cohort ($< \text{2017-10-01}$, Delivered-Only): On-time 4.89% [95% CI: 4.62%, 5.16%] vs Late 3.56% [95% CI: 2.37%, 4.75%], gap = -1.33 pp [-2.59 pp, -0.07 pp] ($p = 0.039$).
- **Q11 / H4 Freight Burden Controlled by Weight Tier:** Restructured H4 analysis into a $5 \times 3$ matrix (5 distance bands $\times$ 3 product weight tiers: Light $< 1\text{kg}$, Medium $1\text{--}5\text{kg}$, Heavy $5\text{kg+}$), reporting both mean and median freight per kg. Demonstrates that holding weight tier constant, median freight per kg increases monotonically by $2.43\times$ to $2.63\times$ from Local ($< 250\text{km}$) to Remote ($2,000\text{km+}$) across all tiers.
- **Q08 Seller Volume Tier Definitions & Tier 3 Transparency:** Documented explicit seller tier volume thresholds computed across all 3,095 sellers in the dataset: Tier 1 ($500+$ orders) = 26 sellers, Tier 2 ($100\text{--}499$ orders) = 184 sellers, Tier 3 ($30\text{--}99$ orders) = 424 sellers, Tier 4 ($< 30$ orders) = 2,461 sellers. Reported Tier 3 explicitly in tables and narrative (424 sellers, 22,448 delivered orders, 93.34% on-time, 2.91 handling days, 9.86% late dispatch, 4.11 avg review).

## [1.3.0] - 2026-11-14
### Added
- **Phase 4 Analytical Business SQL Queries Suite Completed:**
  - Designed, authored, and verified 12 production SQL queries in `sql/queries/`:
    - `q01_executive_summary.sql`: Macro volume, GMV, freight, date-level SLA, and review score.
    - `q02_monthly_trend_analysis.sql`: Monthly trends across steady-state reporting window (2017-01 to 2018-08), flagging boundary months.
    - `q03_h1_late_delivery_satisfaction.sql`: H1 test on on-time vs late review score gap (-2.02 points) and rating distributions.
    - `q04_h1_review_timing_split.sql`: H1 deep dive splitting late reviews by pre-delivery (1.84 avg, 74.5% share) vs post-delivery (3.53 avg, 25.5% share).
    - `q05_h1_category_controlled_satisfaction.sql`: H1 category mix control across 63 product categories with late sample-size tags.
    - `q06_h2_state_delivery_performance.sql`: H2 destination state on-time rates, delay severity, and lead times across all 27 Brazilian states.
    - `q07_h2_state_mix_adjusted_benchmarks.sql`: H2 mix-adjusted actual vs expected on-time rates per state based on distance mix.
    - `q08_h2_seller_fulfillment_cohorts.sql`: H2 merchant fulfillment performance across 4 seller volume tiers.
    - `q09_h3_bottleneck_decomposition.sql`: H3 lead time decomposition (handling vs transit) for intrastate vs interstate order flows.
    - `q10_h3_top_interstate_corridors.sql`: H3 route analysis across top 20 interstate logistics trade corridors.
    - `q11_h4_freight_burden_by_distance.sql`: H4 freight-to-price ratio across 5 distance bands and 3 item price tiers.
    - `q12_customer_retention_delivery_impact.sql`: Customer repeat buying rates comparing first order on-time vs late cohorts.
  - Built Python runner `python/03_run_business_queries.py` and executed verification via `python/test_queries_duckdb.py`.
  - Exported all 12 query result tables to `data/processed/query_results/` as CSVs.
  - Generated comprehensive documentation report: `documentation/business_queries_report.md`.

## [1.2.0] - 2026-11-14
### Added
- **Phase 2 PostgreSQL Star Schema & Transformation Pipeline Completed:**
  - `sql/01_create_raw_tables.sql`: DDL for all 9 raw staging tables with explicit types matching Kaggle CSV schemas.
  - `sql/02_load_raw_data.sql`: Re-runnable loading script using `\copy` commands with utf-8 encoding.
  - `sql/03_create_derived_tables.sql`: Idempotent transformation script building the production analytical star schema:
    - Dimensions: `dim_date` (1,096 days), `dim_geography` (19,015 deduplicated zip prefixes), `dim_customer` (96,096 unique entities), `dim_seller` (3,095 merchants), `dim_product` (32,951 products with English translation & category fallback).
    - Facts: `fact_order_delivery` (99,441 orders at order grain with date-level SLA, whole-day delays, duration lead times, non-destructive anomaly flags, and deduplicated review attributes), `fact_order_items` (112,650 items with Haversine route distances and freight-to-price ratios), `fact_order_payments` (103,886 payment transactions).
  - `documentation/transformation_log.md`: Comprehensive documentation of transformations T1 through T8.
  - `documentation/kpi_dictionary.md` (v1.2.0): Updated every KPI (M01 to M19) with an explicit grain and an explicit stated exclusion rule.
  - `python/02_validate_warehouse.py`: Automated Phase 3 validation script that reads `control_totals` from `data/processed/profiling_results.json`, executes 31 verification queries against PostgreSQL, and produces a structured PASS/FAIL table.
  - `python/test_sql_duckdb.py`: Verified 100% of the SQL transformations and KPI calculations against all 9 raw CSVs (16/16 checks PASS).

### Fixed
- **Unsupported Wording Corrected in Profiling Report:** Fixed line 138 in `documentation/profiling_report.md` and artifact to adhere strictly to non-causal language and zero invented facts: *"74% of reviews on late orders were created after the estimated date but before delivery (4,692 after the estimated date, 5 on the estimated date, and 54 before the estimated date), and score much lower than post-delivery reviews (1.84 vs 3.53). The data cannot tell us why."*
- **Clean Transit Statistics Discrepancy Resolved:** Re-verified clean transit duration excluding negative handling ($N = 1,350$) and negative transit ($N = 23$), confirming exact $N = 95,082$ rows, mean = 9.3641 days, and median = 7.1103 days.

## [1.1.1] - 2026-11-14
### Fixed
- **Date-Level Late Definition:** Switched delivery SLA evaluation from timestamp comparison to calendar DATE-level comparison (`DATE(delivered) > DATE(estimated)`). `order_estimated_delivery_date` has midnight timestamps (`00:00:00`), so comparing timestamps misclassified afternoon deliveries on the promised day as late. Canonical benchmark corrected to **6,534 late orders (6.77%)** and **89,936 on-time orders (93.23%)** among 96,470 delivered orders.
- **Review Star Shares Recomputed:** Recomputed exact star distributions from data. On-time reviewed orders ($N = 89,443$): **9.27% 1–2 stars**, **62.27% 5 stars**, avg score **4.2904**. Late reviewed orders ($N = 6,381$): **62.42% 1–2 stars**, **16.53% 5 stars**, avg score **2.2705**. Review score gap is **-2.0199 points**; negative review share surges **6.73-fold**. Fixed earlier text duplication error where multi-item share (9.94%) had been copied into the negative review field.
- **Reporting Window Order Count:** Corrected order count for 2017-01-01 to 2018-08-31 to **99,092 orders (99.65%)** (349 orders excluded across 2016-09, 2016-10, 2016-12, 2018-09, 2018-10).
- **Geolocation Gaps Disambiguated:** Corrected count reversal: **157 customer zip code prefixes** are missing in `olist_geolocation_dataset.csv`, affecting **278 customers** and **278 orders**; **7 seller zip code prefixes** are missing, affecting **7 sellers**.
- **Handling & Transit Times:** Documented fulfillment durations both with and without negative-duration rows. Excluding 1,350 negative handling rows, clean mean handling is **2.85 days** ($N = 95,105$). Excluding all chronological anomalies (handling $< 0$ and transit $< 0$), clean mean transit is **9.36 days** ($N = 95,084$).

### Added
- **Review Creation Timing Audit (`review_created_before_delivery`):** Added flag comparing `review_creation_date` against `order_delivered_customer_date`. Found that **74.46% of reviews on late orders ($N = 4,751$) were created BEFORE delivery**, averaging an extremely low **1.8396 stars** (75.23% 1–2 stars), whereas late orders reviewed on or after delivery ($N = 1,630$) average **3.5264 stars**. Incorporated into H1 analytical framework.

## [1.1.0] - 2026-11-14
### Added
- Phase 1 Data Profiling completed:
  - All 9 raw CSV files loaded and profiled in `python/01_data_profiling.py`.
  - Canonical Pandas control totals established.
  - Financial discrepancy reconciled (+R$ 165,318.88).

## [1.0.0] - 2026-11-14
### Added
- Phase 0 Requirements document and folder structure initialized.
