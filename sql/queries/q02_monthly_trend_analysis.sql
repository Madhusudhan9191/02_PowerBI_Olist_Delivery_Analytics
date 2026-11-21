-- ============================================================================
-- QUERY 02: Monthly Trend Analysis & Reporting Window Audit
-- BUSINESS OBJECTIVE: Track operational growth, delivery SLA consistency, and satisfaction by purchase month.
-- GRAIN: Calendar Year-Month (purchase timestamp).
-- FILTERS APPLIED: None. Boundary months flagged as thin (< 100 orders).
-- LIMITATIONS: Seasonality in late 2016 and late 2018 is distorted by platform launch and dataset cutoff.
-- ============================================================================

SELECT 
    dt.year_month,
    COUNT(DISTINCT d.order_id) AS total_orders,
    COUNT(DISTINCT CASE WHEN d.is_delivered AND d.is_valid_delivery_date THEN d.order_id END) AS delivered_orders,
    
    -- Date-Level On-Time Performance
    COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END) AS on_time_orders,
    COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END) AS late_orders,
    ROUND(
        COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END)::numeric / 
        NULLIF(COUNT(DISTINCT CASE WHEN d.is_delivered AND d.is_valid_delivery_date THEN d.order_id END), 0)::numeric * 100, 
        2
    ) AS on_time_rate_pct,
    
    -- Delay & Lead Times (Clean)
    ROUND(AVG(CASE WHEN d.is_late THEN d.delay_days END)::numeric, 2) AS avg_delay_days,
    ROUND(AVG(CASE WHEN d.handling_days >= 0 THEN d.handling_days END)::numeric, 2) AS avg_handling_days,
    ROUND(AVG(CASE WHEN d.transit_days >= 0 AND d.handling_days >= 0 THEN d.transit_days END)::numeric, 2) AS avg_transit_days,
    
    -- Financials & Ratings
    ROUND(SUM(i.price)::numeric, 2) AS gross_item_revenue_brl,
    ROUND(AVG(d.review_score)::numeric, 2) AS avg_review_score,
    
    -- Sample Size Governance & Thin Month Flag
    CASE 
        WHEN COUNT(DISTINCT d.order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT d.order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status,
    
    CASE 
        WHEN dt.year_month IN ('2016-09', '2016-10', '2016-12', '2018-09', '2018-10') THEN TRUE 
        ELSE FALSE 
    END AS is_thin_boundary_month

FROM fact_order_delivery d
JOIN dim_date dt ON d.order_purchase_date = dt.full_date
LEFT JOIN fact_order_items i ON d.order_id = i.order_id
GROUP BY dt.year_month
ORDER BY dt.year_month;
