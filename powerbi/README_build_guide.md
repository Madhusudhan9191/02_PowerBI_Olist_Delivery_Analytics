# Power BI Desktop Model Build & Implementation Guide
## Project: Olist E-commerce Delivery Performance & Customer Satisfaction
**Format:** Self-contained step-by-step technical implementation guide.  
**Audience:** Data Analyst / BI Engineer / Reviewer.  
**Objective:** Guide the exact, click-by-click construction of the 4-page Power BI portfolio dashboard using pre-exported star schema CSV files, avoiding live database connection requirements.

---

## 1. Prerequisites & Assets Checklist

Before launching Power BI Desktop, ensure the following project assets are present:
1. **Source Data Directory:** `data/processed/powerbi_input/`
   - Contains all 8 pre-cleaned, pre-typed CSV tables:
     - `dim_date.csv` (1,021 rows, 2016-01-01 to 2018-10-17)
     - `dim_geography.csv` (19,015 rows)
     - `dim_customer.csv` (96,096 rows)
     - `dim_seller.csv` (3,095 rows)
     - `dim_product.csv` (32,951 rows)
     - `fact_order_delivery.csv` (99,441 rows)
     - `fact_order_items.csv` (112,650 rows)
     - `fact_order_payments.csv` (103,886 rows)
   - *Note:* If files are missing, run: `python python/04_export_powerbi_csvs.py`.
2. **Power Query M Scripts:** `powerbi/power_query/*.m`
3. **DAX Measure Library:** `powerbi/dax/measures.dax`
4. **DAX Test & Verification Table:** `powerbi/dax/dax_test_table.md`
5. **Custom Accessible Theme:** `powerbi/theme/olist_theme.json`
6. **Dashboard Page Specs:** `powerbi/specifications/page[1-4]_*.md`

---

## 2. Step 1: Ingest Data via Power Query M

1. Open **Power BI Desktop** with a blank report.
2. In the **Home** tab, click **Transform Data** to open the **Power Query Editor**.
3. **Create the Folder Parameter (`SourceFolder`):**
   - Click **Manage Parameters** $\rightarrow$ **New Parameter**.
   - **Name:** `SourceFolder`
   - **Type:** `Text`
   - **Current Value:** Enter your local repository path to the input CSV directory, e.g.:  
     `./data/processed/powerbi_input` (or full local path `C:\Path\To\Olist\data\processed\powerbi_input`).
   - Click **OK**.
4. **Import Each of the 8 Tables:**
   - In Power Query, right-click in the Queries pane $\rightarrow$ **New Query** $\rightarrow$ **Blank Query**.
   - Click **Advanced Editor** in the ribbon.
   - Replace the default code with the contents of the respective `.m` file from `powerbi/power_query/`:
     - `dim_date` $\rightarrow$ `powerbi/power_query/dim_date.m`
     - `dim_geography` $\rightarrow$ `powerbi/power_query/dim_geography.m`
     - `dim_customer` $\rightarrow$ `powerbi/power_query/dim_customer.m`
     - `dim_seller` $\rightarrow$ `powerbi/power_query/dim_seller.m`
     - `dim_product` $\rightarrow$ `powerbi/power_query/dim_product.m`
     - `fact_order_delivery` $\rightarrow$ `powerbi/power_query/fact_order_delivery.m`
     - `fact_order_items` $\rightarrow$ `powerbi/power_query/fact_order_items.m`
     - `fact_order_payments` $\rightarrow$ `powerbi/power_query/fact_order_payments.m`
   - Rename each query to match the table name exactly.
5. Click **Close & Apply** in the top-left ribbon. Power BI will load all 8 tables into memory.

---

## 3. Step 2: Configure Model View & Star Schema Relationships

Navigate to the **Model View** (icon on the left navigation bar).

### A. Mark Date Table
1. Right-click `dim_date` in the Fields pane $\rightarrow$ **Mark as date table**.
2. Select `full_date` as the Date column $\rightarrow$ Click **OK**.
3. *Notice:* This table ends on `2018-10-17` (the maximum date of the dataset), ensuring time intelligence measures do not evaluate empty future periods up to `TODAY()`.

### B. Configure Relationships
Delete any autodetected relationships and establish the following exact relationships:

| From (Dimension / Parent Fact) | Primary Key Column | To (Fact Table) | Foreign Key Column | Cardinality | Cross Filter Direction | Active | Modeling Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `dim_date` | `full_date` | `fact_order_delivery` | `order_purchase_date` | 1 to Many ($1:*$) | Single (`dim_date` $\rightarrow$ `delivery`) | **Yes** | Standard time intelligence |
| `dim_customer` | `customer_unique_id` | `fact_order_delivery` | `customer_unique_id` | 1 to Many ($1:*$) | Single (`dim_customer` $\rightarrow$ `delivery`) | **Yes** | Customer entity resolution |
| `dim_geography` | `zip_code_prefix` | `dim_customer` | `primary_zip_code_prefix`| 1 to Many ($1:*$) | Single (`geography` $\rightarrow$ `customer`) | **Yes** | Geographic hierarchy |
| `fact_order_delivery` | `order_id` | `fact_order_items` | `order_id` | 1 to Many ($1:*$) | **Both (Bidirectional)** | **Yes** | **Critical:** Propagates seller & product slicers from items back to order-level delivery metrics |
| `dim_product` | `product_id` | `fact_order_items` | `product_id` | 1 to Many ($1:*$) | Single (`product` $\rightarrow$ `items`) | **Yes** | Catalog hierarchy |
| `dim_seller` | `seller_id` | `fact_order_items` | `seller_id` | 1 to Many ($1:*$) | Single (`seller` $\rightarrow$ `items`) | **Yes** | Merchant volume tiers |
| `fact_order_delivery` | `order_id` | `fact_order_payments` | `order_id` | 1 to Many ($1:*$) | Single (`delivery` $\rightarrow$ `payments`) | **Yes** | Financial reconciliation |

> **Why Bidirectional Filtering on `fact_order_delivery` $\longleftrightarrow$ `fact_order_items`?**  
> In this e-commerce schema, seller attributes (`dim_seller[seller_tier]`) and product attributes (`dim_product[product_category_name_en]`) relate to items (`fact_order_items`), while delivery SLA flags (`is_on_time`, `handling_days`, `review_score`) reside at the order grain (`fact_order_delivery`). Setting this relationship to **Both** allows slicers on seller tier or product category to filter `fact_order_delivery` dynamically, ensuring all order-level delivery KPIs slice accurately without custom DAX filter overrides.
> 
> **Important Modeling Caveat (Multi-Seller Order Overlap):**  
> While bidirectional cross-filtering makes seller tier and product category slicers work seamlessly, **exactly 825 clean delivered orders contain items from sellers in multiple tiers**. Consequently:
> 1. *Order Count Overlap:* Slicing distinct order counts across tiers yields 95,926 tier-order instances across the four cohorts, compared to 95,082 deduplicated clean delivered orders (an 844-order overlap / 0.89%).
> 2. *Payment Double-Counting:* Financial measures at the order grain (`Captured Payment Value` on `fact_order_payments`) will double-count payment amounts across multi-seller tiers if sliced by `dim_seller`. By contrast, merchandise spend (`Gross Item Revenue` = `fact_order_items[price]`) and freight billed are at the item grain and never double-count.
> 3. *Architectural Alternatives:* If strict single-direction modeling is preferred, keep this relationship as Single and apply `CROSSFILTER(fact_order_delivery[order_id], fact_order_items[order_id], Both)` strictly inside the specific seller-focused DAX measures, or maintain an explicit bridge table between orders and sellers.

### C. Cohort Slicer Independence Note
Customer cohort retention measures (e.g. `[Delivered Repeat Rate % (On-Time First Order)]`, `[Mature Repeat Rate %]`) evaluate at the customer entity grain on `dim_customer`. Because the dimensional relationship flows from `dim_customer` (1) to `fact_order_delivery` (*), slicers placed on fact attributes (such as purchase date ranges in `dim_date` or destination states in `fact_order_delivery`) do not filter `dim_customer`. This is architecturally intentional for cohort metrics: a customer's lifetime repeat classification is a persistent property of that customer's cohort, not a transactional slice. Slicing by customer-level geography (`dim_customer[primary_state]`) will filter both tables.

---

## 4. Step 3: Import Custom Theme & Create Measure Container

### A. Apply Theme
1. In the **View** tab in the top ribbon, click the **Themes** dropdown $\rightarrow$ **Browse for themes**.
2. Select [`powerbi/theme/olist_theme.json`](./theme/olist_theme.json).
3. The report canvas will immediately adopt the accessible corporate palette (Deep Slate `#111827`, Electric Blue `#0078D4`, Forest Green `#00A86B`, Coral Alert `#D83B01`).

### B. Create Measure Table (`_Measures`)
1. In the **Home** tab, click **Enter Data**.
2. Name the table `_Measures` and click **Load**.
3. Open [`powerbi/dax/measures.dax`](./dax/measures.dax).
4. Create each DAX measure inside `_Measures`.
5. In the **Model View**, select each measure and assign its **Display Folder** property matching the sections in `measures.dax`:
   - `01_Volume_and_Spend`
   - `02_Delivery_SLA`
   - `03_Review_Satisfaction`
   - `04_Fulfillment_Bottlenecks`
   - `05_Regional_and_Seller`
   - `06_Freight_Economics`
   - `07_Retention_and_Cohort`
   - `08_Sample_Size_Governance`
6. Format percentages as `0.0%` or `0.00%`, currency as `R$ #,##0.00`, and counts as `#,##0`.
7. Delete the default blank `Column1` in `_Measures` so the table displays the calculator icon at the top of the Fields pane.

---

## 5. Step 4: Execute DAX Pre-Flight Verification Table

Before assembling the report visual pages, run the QA verification checks:
> **Note on Verification:** The underlying measure logic and benchmarks have been independently verified in Python/DuckDB against the exported star schema CSVs. Actual DAX execution is verified here in Power BI Desktop by recording rendered values.

1. Open [`powerbi/dax/dax_test_table.md`](./dax/dax_test_table.md).
2. Create a temporary matrix visual on a blank page.
3. Drag each measure into the visual without page-level filters, observe the rendered value, and record it in the **Observed Value in Power BI** column of the test table to confirm alignment against the **Expected Benchmark Value**:
   - `[Total Orders]` = **99,441**
   - `[Valid Delivered Orders]` = **96,470**
   - `[On-Time Delivery Rate %]` = **93.23%**
   - `[Late Delivery Rate %]` = **6.77%**
   - `[Average Review Score (On-Time)]` = **4.2904**
   - `[Average Review Score (Late)]` = **2.2705**
   - `[Review Score Gap (Late vs On-Time)]` = **-2.02 points**
   - `[Pre-Delivery Late Review Share %]` = **74.46%**
   - `[Avg Review Score (Pre-Delivery Late)]` = **1.8396**
   - `[Avg Review Score (Post-Delivery Late)]` = **3.5264**
   - `[Interstate Orders Count]` = **61,022**
   - `[Intrastate Orders Count]` = **34,060**
   - `[Delivered Repeat Rate % (On-Time)]` = **3.04%**
   - `[Delivered Repeat Rate % (Late)]` = **2.52%**
   - `[Delivered Repeat Rate Gap pp]` = **-0.52 pp**
   - `[Mature Repeat Rate % (On-Time)]` = **5.13%**
   - `[Mature Repeat Rate % (Late)]` = **3.78%**
   - `[Mature Repeat Rate Gap pp]` = **-1.35 pp**
   - `[Late Dispatch Rate % (Tier 1)]` = **8.07%** ($2,175 / 26,955$ items)
   - `[Late Dispatch Rate % (Tier 2)]` = **9.31%** ($3,566 / 38,299$ items)
   - `[Late Dispatch Rate % (Tier 3)]` = **9.86%** ($2,497 / 25,316$ items)
   - `[Late Dispatch Rate % (Tier 4)]` = **11.07%** ($1,994 / 18,011$ items)
4. Verify each row, mark **PASS** in the test table, and delete the temporary QA page.

---

## 6. Step 5: Build Dashboard Pages

Refer to the visual specifications in `powerbi/specifications/`:

### Page 1: Executive Logistics & SLA Overview
- Follow [`powerbi/specifications/page1_executive_overview.md`](./specifications/page1_executive_overview.md).
- Place top KPI banner (Customer Spend, Total Orders, On-Time SLA %, Delay Severity, Customer Rating).
- Insert Monthly Operational Trends combo chart (`2017-01` to `2018-08`) with 95% SLA target line.
- Insert Donut Chart showing complete 4-part breakdown: On-Time (89,936) vs Late (6,534) vs Non-Delivered (2,963) vs Delivered Missing Date (8) = **99,441 orders**.
- Insert Lead Time Decomposition chart on clean fulfillment cohort (Handling: 2.85d / 23.32% vs Transit: 9.37d / 76.68%).

### Page 2: Delivery Performance & Fulfillment Bottlenecks
- Follow [`powerbi/specifications/page2_delivery_performance.md`](./specifications/page2_delivery_performance.md).
- Insert Lead Time 100% Stacked Bar comparing Intrastate (63.4% transit) vs Interstate (80.5% transit).
- Insert Late Delay Severity distribution histogram (1–3d: 31.4%, 4–7d: 22.8%, 8–14d: 22.1%, 15+d: 23.7%).
- Insert Top 20 Interstate Corridors Matrix with conditional formatting, highlighting the `SP -> RJ` bottleneck (8,094 orders; 86.38% on-time; 12.65 days transit).

### Page 3: Regional Logistics & Seller Operations
- Follow [`powerbi/specifications/page3_regional_and_seller.md`](./specifications/page3_regional_and_seller.md).
- Insert Clustered Horizontal Bar Chart showing Actual vs Expected On-Time Rate across all 27 states, reporting gaps in percentage points (`pp`) (e.g. RJ: -5.41 pp, MA: -6.24 pp, AL: -11.68 pp, SP: +1.07 pp).
- Insert Dumbbell / Scatter Chart showing Promised Lead Time vs Actual Cycle Days for AM, RO vs RJ, SP, AL, explaining the safety buffer cushion (+19.5d / +20.0d buffer).
- Insert Seller Volume Tiers Matrix reporting all 4 tiers (Tier 1: 26 sellers, Tier 2: 184 sellers, Tier 3: 424 sellers, Tier 4: 2,327 active sellers in delivered cohort; 2,461 total).

### Page 4: Customer Satisfaction, Review Timing & Retention
- Follow [`powerbi/specifications/page4_customer_satisfaction.md`](./specifications/page4_customer_satisfaction.md).
- Insert 100% Stacked Bar comparing On-Time (9.27% negative, 62.27% 5-star) vs Late (62.42% negative, 16.53% 5-star) review distributions.
- Insert Review Timing Dissection chart showing Pre-Delivery (1.84 stars) vs Post-Delivery (3.53 stars) late ratings.
- Insert Freight Burden per kg Line Chart across 5 distance bands and 3 weight tiers, showing the 2.43x to 2.63x escalation.
- Insert Retention Cohort Bar Chart showing repeat purchase rates and 95% difference confidence intervals for full cohort (-0.52 pp [-0.92, -0.12 pp]) and mature cohort (-1.35 pp [-2.61, -0.09 pp]), with the explicit observational non-random assignment caution note.

---

## 7. Step 6: Final Verification & Publish

1. Save the file as `Olist_Delivery_Analytics.pbix`.
2. Inspect slicers across all pages to verify cross-filtering and responsiveness.
3. Verify that all figures reconcile perfectly with the Phase 1, Phase 3, and Phase 4 warehouse control totals.
