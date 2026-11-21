-- ============================================================================
-- QUERY 01: Executive KPI Summary
-- BUSINESS OBJECTIVE: Macro baseline of order volume, revenue, delivery SLA, and satisfaction.
-- GRAIN: Single row (Dataset wide with delivered cohort breakdowns).
-- FILTERS APPLIED: None for macro volume; delivered cohort scoped to valid delivery timestamps.
-- LIMITATIONS: Covers entire historical period (2016-09 to 2018-10); multi-year totals should not be annualized.
-- ============================================================================

SELECT 
    COUNT(DISTINCT d.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN d.is_delivered AND d.is_valid_delivery_date THEN d.order_id END) AS delivered_orders_with_date,
    
    -- Date-Level Delivery SLA
    COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END) AS on_time_delivered_orders,
    COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END) AS late_delivered_orders,
    ROUND(
        COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN d.is_delivered AND d.is_valid_delivery_date THEN d.order_id END), 0)::numeric * 100, 
        2
    ) AS on_time_delivery_rate_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN d.is_delivered AND d.is_valid_delivery_date THEN d.order_id END), 0)::numeric * 100, 
        2
    ) AS late_delivery_rate_pct,
    ROUND(AVG(CASE WHEN d.is_late THEN d.delay_days END)::numeric, 2) AS avg_delay_days_late_orders,
    
    -- Financial Totals
    ROUND(SUM(i.price)::numeric, 2) AS gross_item_revenue_brl,
    ROUND(SUM(i.freight_value)::numeric, 2) AS total_freight_billed_brl,
    ROUND(SUM(i.total_item_spend)::numeric, 2) AS total_customer_item_spend_brl,
    ROUND(AVG(d.review_score)::numeric, 4) AS overall_avg_review_score,
    
    -- Sample Size Governance
    COUNT(DISTINCT d.order_id) AS sample_size_n,
    'interpretable' AS sample_size_status

FROM fact_order_delivery d
LEFT JOIN fact_order_items i ON d.order_id = i.order_id;
