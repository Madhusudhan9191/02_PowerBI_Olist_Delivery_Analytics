-- ============================================================================
-- QUERY 12: Customer Retention & Repeat Buying by Initial Delivery Outcome
-- BUSINESS OBJECTIVE: Test observational association between initial order delivery outcome and customer repeat purchasing.
-- GRAIN: Cohort Scope x Repeat Definition x Initial Delivery Outcome Comparison.
-- FILTERS APPLIED: Customers whose initial order was successfully delivered with valid delivery date (N = 93,350 unique customers).
-- METHODOLOGY & STATISTICAL METRICS:
--   - Repeat Customers: Evaluated under delivered-only orders as well as all subsequent orders.
--   - Mature Cohort: Customers whose first order was placed before 2017-10-01 (providing >= 11 months of follow-up
--     before the dataset cutoff on 2018-10-17).
--   - Individual 95% CIs: p +/- 1.96 * sqrt(p*(1-p)/n).
--   - Gap 95% CI (Difference in Proportions): (p_late - p_ontime) +/- 1.96 * sqrt(p1(1-p1)/n1 + p2(1-p2)/n2).
--   - METHODOLOGICAL & OBSERVATIONAL CAUTION:
--     While separate confidence intervals overlap in the mature cohort due to unequal sample sizes (N_late = 927 vs
--     N_ontime = 24,741), the two-proportion confidence interval of the difference strictly excludes zero.
--     Crucially, customers receiving late deliveries are NOT randomly assigned: late deliveries cluster heavily by
--     destination state (e.g., Rio de Janeiro, Alagoas) and by seller dispatch behavior.
--     Therefore, this metric demonstrates an observational association only, not causal attribution.
-- ============================================================================

WITH deliv_orders AS (
    SELECT 
        d.order_id,
        d.customer_unique_id,
        d.order_purchase_timestamp,
        d.is_on_time,
        d.is_late,
        ROW_NUMBER() OVER (
            PARTITION BY d.customer_unique_id 
            ORDER BY d.order_purchase_timestamp ASC, d.order_id ASC
        ) AS rn
    FROM fact_order_delivery d
    WHERE d.is_delivered = TRUE 
      AND d.is_valid_delivery_date = TRUE
),
customer_deliv_counts AS (
    SELECT 
        customer_unique_id,
        (COUNT(DISTINCT order_id) > 1) AS is_repeat_delivered
    FROM fact_order_delivery
    WHERE is_delivered = TRUE 
      AND is_valid_delivery_date = TRUE
    GROUP BY customer_unique_id
),
customer_all_counts AS (
    SELECT 
        customer_unique_id,
        is_repeat_customer AS is_repeat_all
    FROM dim_customer
),
first_orders AS (
    SELECT 
        d.customer_unique_id,
        d.order_id,
        d.order_purchase_timestamp,
        d.is_on_time,
        d.is_late,
        cdc.is_repeat_delivered,
        cac.is_repeat_all,
        (d.order_purchase_timestamp < '2017-10-01 00:00:00') AS is_mature_cohort
    FROM deliv_orders d
    JOIN customer_deliv_counts cdc ON d.customer_unique_id = cdc.customer_unique_id
    JOIN customer_all_counts cac ON d.customer_unique_id = cac.customer_unique_id
    WHERE d.rn = 1
),
scopes AS (
    -- 1. Full Dataset: Delivered-Only
    SELECT 
        '1. Full Dataset (All Initial Delivered)' AS analysis_scope,
        'Delivered Orders Only' AS repeat_definition,
        COUNT(CASE WHEN is_on_time THEN 1 END) AS n_ontime,
        SUM(CASE WHEN is_on_time AND is_repeat_delivered THEN 1 ELSE 0 END) AS r_ontime,
        COUNT(CASE WHEN is_late THEN 1 END) AS n_late,
        SUM(CASE WHEN is_late AND is_repeat_delivered THEN 1 ELSE 0 END) AS r_late
    FROM first_orders
    
    UNION ALL
    
    -- 2. Mature Cohort: All Orders
    SELECT 
        '2. Mature Cohort (< 2017-10-01, >= 11 mo Follow-up)' AS analysis_scope,
        'All Subsequent Orders' AS repeat_definition,
        COUNT(CASE WHEN is_on_time THEN 1 END) AS n_ontime,
        SUM(CASE WHEN is_on_time AND is_repeat_all THEN 1 ELSE 0 END) AS r_ontime,
        COUNT(CASE WHEN is_late THEN 1 END) AS n_late,
        SUM(CASE WHEN is_late AND is_repeat_all THEN 1 ELSE 0 END) AS r_late
    FROM first_orders
    WHERE is_mature_cohort = TRUE
    
    UNION ALL
    
    -- 3. Mature Cohort: Delivered-Only
    SELECT 
        '3. Mature Cohort (< 2017-10-01, >= 11 mo Follow-up)' AS analysis_scope,
        'Delivered Orders Only' AS repeat_definition,
        COUNT(CASE WHEN is_on_time THEN 1 END) AS n_ontime,
        SUM(CASE WHEN is_on_time AND is_repeat_delivered THEN 1 ELSE 0 END) AS r_ontime,
        COUNT(CASE WHEN is_late THEN 1 END) AS n_late,
        SUM(CASE WHEN is_late AND is_repeat_delivered THEN 1 ELSE 0 END) AS r_late
    FROM first_orders
    WHERE is_mature_cohort = TRUE
)
SELECT 
    analysis_scope,
    repeat_definition,
    n_ontime,
    r_ontime,
    ROUND(r_ontime::numeric / n_ontime::numeric * 100, 2) AS ontime_repeat_rate_pct,
    n_late,
    r_late,
    ROUND(r_late::numeric / n_late::numeric * 100, 2) AS late_repeat_rate_pct,
    ROUND((r_late::numeric / n_late::numeric - r_ontime::numeric / n_ontime::numeric) * 100, 2) AS repeat_rate_gap_pp,
    -- Two-sample difference 95% CI: (p2 - p1) +/- 1.96 * sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)
    ROUND((
        (r_late::numeric / n_late::numeric - r_ontime::numeric / n_ontime::numeric) -
        1.96 * SQRT(
            (r_ontime::numeric / n_ontime::numeric) * (1.0 - r_ontime::numeric / n_ontime::numeric) / n_ontime::numeric +
            (r_late::numeric / n_late::numeric) * (1.0 - r_late::numeric / n_late::numeric) / n_late::numeric
        )
    ) * 100, 2) AS gap_ci_lower_pp,
    ROUND((
        (r_late::numeric / n_late::numeric - r_ontime::numeric / n_ontime::numeric) +
        1.96 * SQRT(
            (r_ontime::numeric / n_ontime::numeric) * (1.0 - r_ontime::numeric / n_ontime::numeric) / n_ontime::numeric +
            (r_late::numeric / n_late::numeric) * (1.0 - r_late::numeric / n_late::numeric) / n_late::numeric
        )
    ) * 100, 2) AS gap_ci_upper_pp,
    CASE 
        WHEN n_late < 30 THEN 'suppress'
        WHEN n_late < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status
FROM scopes
ORDER BY analysis_scope, repeat_definition;
