# Interview Defense Notes — Olist Delivery Analytics

Prepared responses for portfolio review, technical interviews, and analytical
challenge questions. All numbers are traceable to SQL, Pandas, or DAX outputs
verified in `documentation/three_way_reconciliation_report.md`.

---

## Table of Contents
1. [Project Framing](#1-project-framing)
2. [Data & Methodology Questions](#2-data--methodology-questions)
3. [Hypothesis Defense (H1–H4)](#3-hypothesis-defense-h1h4)
4. [Technical Architecture Questions](#4-technical-architecture-questions)
5. [Power BI & DAX Questions](#5-power-bi--dax-questions)
6. [Limitations & What I Would Do Differently](#6-limitations--what-i-would-do-differently)
7. [Business Impact Questions](#7-business-impact-questions)

---

## 1. Project Framing

**Q: Summarise this project in 60 seconds.**

> "I took the Kaggle Olist Brazilian e-commerce dataset — 99,441 orders across two
> years — and built an end-to-end analytical product: PostgreSQL warehouse,
> Python validation, and a four-page Power BI dashboard with 71 DAX measures.
> The core question was whether late delivery hurts Olist's business across four
> dimensions: review scores, regional performance, ETA buffering strategy, and
> freight economics. The headline finding is a 2.02-point review score gap between
> late and on-time deliveries, with 74.5% of late-order reviews written before the
> package even arrives. I also built a three-way numerical reconciliation across
> SQL, Pandas, and DAX to confirm that every dashboard number is traceable to
> the raw data (all 63 measures verified directly against Power BI Desktop DAX query
> export, matching independent PostgreSQL warehouse controls within documented tolerances)."

---

**Q: Why Olist? Why this dataset?**

> "It is a real-world multi-sided marketplace with realistic messiness: multi-seller
> orders, sparse early months, missing carrier pickup timestamps, and state-level
> geographic variation. It is also publicly available under CC BY-NC-SA, so I can
> share it in a portfolio without data-sharing concerns. The delivery-performance
> angle lets me demonstrate time-series analysis, geographic aggregation,
> customer-lifetime cohorts, and freight economics in a single dataset."

---

## 2. Data & Methodology Questions

**Q: How did you define 'on-time'?**

> "An order is on-time if `order_delivered_customer_date ≤
> order_estimated_delivery_date`. Both timestamps are in the raw dataset.
> I did not adjust for weekends or holidays — the promised date is whatever
> Olist showed the customer at checkout, so that is the right comparator."

---

**Q: Why 96,470 orders and not 99,441?**

> "99,441 is the total order count in the dataset. The valid delivered cohort
> (96,470) restricts to `order_status = 'delivered'` with non-null actual and
> estimated delivery timestamps. The remaining ~3,000 include cancelled orders,
> orders with unavailable or in-transit status, and a small number with null
> timestamps that make the on-time calculation impossible. This is documented
> in the transformation log."

---

**Q: What is the 'steady-state window' and why does Page 1 use it?**

> "September–December 2016 had only 4 orders in the dataset — a ramp-up period
> that distorts the monthly SLA trend chart (0% on-time in a month with one order
> is not a meaningful rate). I created an `is_steady_state_window` boolean flag
> that is TRUE from January 2017 onward and applied it as a page-level filter on
> Page 1. The KPI cards on Page 1 therefore reflect a slightly different total
> (15.79M, 93.21%) than the global figures on other pages (15.84M, 93.23%). This
> is intentional and documented."

---

**Q: How did you compute the mix-adjusted performance gap?**

> "For each destination state, I computed its `Expected On-Time Rate %` by weighting
> the national benchmark on-time delivery rate across the 6 distance bands
> (Local, Regional, Medium, Long, Remote, Unknown) by that state's specific order
> distribution across those bands. In DAX, this is evaluated dynamically as:
> `Expected On-Time Rate % = SUMX(VALUES(fact_order_delivery[order_distance_band]), BandWeight * GlobalBandRate)`.
> The mix-adjusted performance gap is then `Actual state on-time rate % − Expected on-time rate %`.
> For example, Alagoas (AL) achieves an actual on-time rate of 78.59%, while its
> distance-mix expected rate is 90.27%, yielding an exact mix-adjusted gap of
> −11.68 pp. This demonstrates that even after controlling for its higher share
> of long-distance shipments, AL underperforms expected fulfillment standards by
> over 11 percentage points."

---

**Q: Why is Average Actual Cycle Days 12.56 days, but Average Fulfillment Cycle Days is 12.61 days and Handling + Transit is 12.22 days?**

> "This reflects two distinct cohort grains and operational milestones:
> 1. **Average Actual Cycle Days (12.56 days):** Evaluated across the full valid
>    delivered cohort (N = 96,470), measuring total elapsed duration from customer
>    order purchase to confirmed delivery (`order_delivered_customer_date − order_purchase_timestamp`).
>    Combined with `Average Promised Lead Time Days` (24.37 days), this yields the
>    platform's `ETA Safety Buffer Days` of 11.81 days (24.37 − 12.56).
> 2. **Average Fulfillment Cycle Days (12.61 days):** Evaluated on the clean
>    fulfillment population (N = 95,082) where carrier pickup timestamps are present
>    and non-negative.
> 3. **Handling vs. Transit Decomposition:** Within that clean population, `Average
>    Handling Days` is 2.85 days (approval to carrier pickup) and `Average Transit Days`
>    is 9.37 days (carrier pickup to customer delivery), summing to 12.22 days.
>    The remaining 0.39 days (~9.4 hours) between 12.22 days and the 12.61-day total
>    cycle accounts for payment approval latency (`order_approved_at − order_purchase_timestamp`)."

---

**Q: Why is the repeat-buying cohort restricted to October 2017?**

> "The dataset ends in October 2018. A customer who places their first order in,
> say, September 2018 has only one month of observable follow-up — not enough to
> conclude they did not return. The mature cohort (first order before October 2017)
> gives everyone at least 11 months of observation window within the dataset,
> making the repeat-buying comparison meaningful. The full-cohort result
> (−0.52 pp, p = 0.016) is still reported for completeness."

---

**Q: Did you test statistical significance?**

> "Yes, for the repeat-buying gap only — that is the one finding where a p-value
> is meaningful because I am comparing two proportions. I used a two-sample
> proportion z-test: mature cohort gap −1.35 pp (p = 0.038); full cohort −0.52 pp
> (p = 0.016). I did not apply significance tests to the review score gap or
> regional gaps because the population is the entire dataset, not a sample —
> there is no sampling uncertainty to test."

---

## 3. Hypothesis Defense (H1–H4)

**H1 — Q: The 2.02-point gap could just be because difficult routes are both
late AND have unhappy customers. How do you rule that out?**

> "I cannot rule it out with this dataset — that is a correct challenge.
> The review timing analysis adds some texture: 74.5% of late-order reviews
> were written *before delivery*, averaging 1.84 stars. Reviews submitted after
> delivery average 3.53 stars. This pattern is consistent with frustrated
> waiting driving the low scores, but I cannot confirm it. I say 'associated with'
> not 'caused by' throughout."

---

**H2 — Q: You say Alagoas is the worst performer. Is that just because it's far?**

> "Partly, yes. AL's average route distance is about 1,345 km, which puts most
> orders in the Long band. But the mix-adjusted gap (−11.68 pp) accounts for
> the national average at that distance. AL underperforms even after adjusting
> for the fact that long routes are harder. Whether the residual gap is due to
> carrier routing, infrastructure, or something else is not in the data."

---

**H3 — Q: You say Amazonas has a ~19.5-day buffer. Is Olist padding deliberately?**

> "The data shows a large gap between promised and actual lead times in AM — I
> cannot infer intent. It is consistent with Olist setting conservative ETAs
> for remote states to protect its SLA rate, which is a common e-commerce practice.
> AM achieves 97.24% on-time, which is consistent with the buffer working as
> intended. I describe this as an association, not a deliberate strategy."

---

**H4 — Q: Freight per kg rising with distance — isn't that obvious?**

> "Yes, the direction is expected. The value of quantifying it is showing the
> magnitude (143–163% increase from Local to Remote across all weight tiers) and
> that the relationship is consistent across weight tiers, not just for heavy items.
> For a business question like 'should we subsidise freight to remote customers?'
> this gives a concrete cost input."

---

## 4. Technical Architecture Questions

**Q: Why PostgreSQL? Why not just use Pandas the whole way?**

> "Three reasons: (1) the star schema DDL is a portfolio demonstration of SQL
> data warehousing skills; (2) PostgreSQL's window functions and CTEs make the
> derived-table logic cleaner and auditable; (3) the three-way reconciliation
> — the same metric computed in SQL, Pandas, and DAX — only has value if all
> three are independent implementations. If I computed everything in Pandas and
> then just imported it into Power BI, I would have a two-layer pipeline, not
> a three-layer cross-check."

---

**Q: Why Power BI and not Tableau or Looker?**

> "Power BI with DAX measures gives me the most control over the semantic layer.
> The 71-measure model means every KPI card, tooltip, and table cell is a named,
> documented measure — not an ad-hoc calculation in a view. That makes the
> reconciliation tractable. It is also the tool most commonly used in analyst
> roles in the markets I am targeting."

---

**Q: What does the bidirectional relationship between facts do, and what does
it cost you?**

> "The `fact_order_delivery ↔ fact_order_items` bidirectional relationship allows
> seller-tier slicers (which live on the items fact) to filter delivery metrics
> (which live on the delivery fact). Without it, selecting 'Tier 1 sellers' would
> filter item-level revenue but not delivery SLA. The cost is that 825 multi-seller
> orders (0.83%) can be double-counted when aggregating order counts by seller tier,
> because the same order appears in two tiers' items. Revenue and freight are
> unaffected since they aggregate at item grain. I document this caveat in
> the data dictionary."

---

## 5. Power BI & DAX Questions

**Q: What is the difference between CALCULATE and FILTER in DAX?**

> "CALCULATE modifies the filter context — it is the standard way to override
> or add filters. FILTER returns a table, often used inside CALCULATE to pass
> a row-by-row condition. For example:
> `CALCULATE([On-Time Delivery Rate %], fact_order_delivery[is_on_time] = TRUE)`
> uses CALCULATE with a simple boolean filter. For more complex row-level logic
> I use `CALCULATE([measure], FILTER(table, condition))`. The key distinction is
> that CALCULATE respects and modifies the existing filter context, while FILTER
> iterates the table."

---

**Q: How did you handle the date table? Why not use auto date/time?**

> "I disabled auto date/time and created a proper `dim_date` table in Power Query
> using `List.Dates` from the dataset's minimum to maximum date (2016-09-04 to
> 2018-10-17). This gives me control over every column (year, month, year_month
> label, quarter), avoids the hidden auto-hierarchy tables that bloat the model,
> and means the date table is bounded at the data maximum — no future dates,
> no `TODAY()` creep."

---

**Q: How would you add a rolling 3-month SLA average to the trend chart?**

> "I would add a measure using `DATESINPERIOD` and `CALCULATE`:
> ```dax
> Rolling 3M On-Time Rate % =
> CALCULATE(
>     [On-Time Delivery Rate %],
>     DATESINPERIOD(
>         dim_date[full_date],
>         LASTDATE(dim_date[full_date]),
>         -3,
>         MONTH
>     )
> )
> ```
> Then add it as a second line on the trend combo chart."

---

**Q: What is SUMMARIZECOLUMNS and when did you use it?**

> "SUMMARIZECOLUMNS is the preferred DAX function for grouped aggregations in
> DAX Query View — it is the equivalent of SQL `SELECT ... GROUP BY`. I used it
> in `powerbi/dax/evaluate_all_63_measures.dax` to export state-level and
> seller-tier-level aggregations for the Phase 6 reconciliation:
> ```dax
> EVALUATE
> SUMMARIZECOLUMNS(
>     fact_order_delivery[order_customer_state],
>     \"On-Time Rate\", [On-Time Delivery Rate %],
>     \"Mix-Adjusted Gap pp\", [Mix-Adjusted Performance Gap pp]
> )
> ```"

---

**Q: Did you encounter any DAX engine bugs during reconciliation, and how did you resolve them?**

> "Yes — a classic DAX null-semantics bug during Phase 6 reconciliation. 
> PostgreSQL reported 95,082 clean fulfillment orders, but Power BI Desktop evaluated 95,097 orders (+15 orders).
> 
> Investigating the data, 15 delivered orders lacked a carrier pickup date (`order_delivered_carrier_date IS NULL`), leaving `handling_days` as `BLANK()`. In DAX, `BLANK() >= 0` evaluates to `TRUE`, so filtering with `fact_order_delivery[handling_days] >= 0` inadvertently let those 15 orders pass. This shifted Tier 4 late dispatch from 11.07% to 11.10%.
> 
> Rather than masking the variance by widening test tolerances or writing complex composite DAX filters, I fixed the issue at the architectural level: I added an explicit boolean column `is_clean_fulfillment` in the data transformation pipeline (`04_export_powerbi_csvs.py`) and refactored the DAX measures to filter strictly on `fact_order_delivery[is_clean_fulfillment] = TRUE()`.
> 
> Upon re-evaluating in DAX Query View, the count matched PostgreSQL at exactly 95,082 (zero variance), Tier 4 late dispatch matched PostgreSQL at 11.07%, and count tolerance was restored to exact 0."

---

## 6. Limitations & What I Would Do Differently

**Q: What is the biggest limitation of this analysis?**

> "The absence of causal identification. I cannot separate the effect of late
> delivery on review scores from the effect of route difficulty, product category,
> or seller quality — all of which are correlated. A proper causal design would
> need either a randomised experiment or a natural experiment (e.g., a carrier
> strike affecting some regions but not others). With observational data I can
> describe patterns precisely, but I am careful not to claim causes."

---

**Q: What would you do with more time / data?**

> "Five things:
> 1. **Carrier-level data** — the dataset has no carrier identity, so I cannot
>    attribute transit delays to specific carriers or routes.
> 2. **A/B experiment design** — an experiment varying promised lead time by
>    region to test whether buffer size actually changes the review score, holding
>    actual delivery time constant.
> 3. **Product-category mix adjustment** — the current mix-adjusted gap uses
>    only distance band; controlling for category (electronics vs. furniture)
>    would sharpen the state comparisons.
> 4. **Customer-level panel** — Olist's `customer_unique_id` allows limited
>    panel analysis, but the dataset window (2 years) is short. Longer follow-up
>    would make the repeat-buying cohort analysis much more powerful.
> 5. **Incremental refresh in Power BI** — with live production data the model
>    should use incremental refresh rather than full CSV reload."

---

**Q: Your Page 1 KPIs (15.79M, 93.21%) differ slightly from other pages
(15.84M, 93.23%). Is that a bug?**

> "No — it is intentional and documented. Page 1 applies the
> `is_steady_state_window` page-level filter, which excludes the September–December
> 2016 ramp-up orders (4 orders, 0% on-time). The other pages show the full
> valid delivered cohort. The difference is small (R\$50K revenue, 0.02 pp SLA)
> because the excluded period is tiny. I add a note to the Page 1 subtitle to
> make this transparent to report viewers."

---

## 7. Business Impact Questions

**Q: If you were presenting to Olist's VP of Operations, what would you recommend?**

> "Three things, framed as observations and hypotheses — not prescriptions:
>
> 1. **Focus carrier quality improvement on AL, MA, and RJ.** These states show
>    the largest negative mix-adjusted gaps (−11.68 pp, −6.24 pp, −5.41 pp).
>    Handling time is stable across states, so the gap is consistent with
>    carrier transit being the variable factor. Investigating carrier routing
>    and SLA contracts in those states seems like the highest-leverage action.
>
> 2. **Review the RJ promised ETA.** RJ gets only an 11.7-day buffer against a
>    15.3-day actual cycle — the smallest buffer of any significant-volume state.
>    Extending the promised window could improve the on-time rate without
>    changing any logistics operation. The trade-off is that a longer promised
>    date may reduce conversion.
>
> 3. **Investigate pre-delivery review prompting.** 74.5% of late-order reviews
>    arrive before delivery, averaging 1.84 stars. If the platform is sending
>    review prompts on a fixed schedule regardless of delivery status, switching
>    to delivery-triggered prompts could improve the average score for late orders
>    without changing any logistics. I cannot confirm this from the data alone."

---

**Q: Is a −0.52 pp repeat-buying gap economically meaningful?**

> "At the scale of Olist's order volume, a 0.52 pp difference in repeat rate
> across tens of thousands of customers compounds over time. The more important
> number is the mature cohort gap: −1.35 pp (p = 0.038), observed among customers
> with enough follow-up time to have had a realistic chance to return. Whether
> that gap is worth the cost of logistics improvement depends on customer lifetime
> value estimates that are outside this dataset."

---

*Document prepared: November 2026*  
*All figures verified across PostgreSQL, Pandas, and Power BI DAX (documented in `documentation/three_way_reconciliation_report.md`)*
