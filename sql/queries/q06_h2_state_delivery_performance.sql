-- ============================================================================
-- QUERY 06: Hypothesis 2 — Regional Delivery Performance by Destination State
-- BUSINESS OBJECTIVE: Quantify geographic disparity in on-time delivery rates and transit times across Brazil.
-- GRAIN: Destination State (order-level customer_state from raw_customers).
-- FILTERS APPLIED: Delivered orders with valid delivery dates (N = 96,470).
-- NOTE ON GRAIN: Joins on d.customer_id = c.customer_id to evaluate destination state at the specific order level,
--                avoiding customer-level primary_state aggregation differences (43 orders differ).
--                For example, SP has 40,494 delivered orders (vs 40,499 under customer primary_state),
--                and MA on-time rate is 82.57% (N = 717).
-- ============================================================================

SELECT 
    c.customer_state AS destination_state,
    COUNT(DISTINCT d.order_id) AS delivered_orders_n,
    
    COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END) AS on_time_orders,
    COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END) AS late_orders,
    
    ROUND(
        COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END)::numeric / 
        NULLIF(COUNT(DISTINCT d.order_id), 0)::numeric * 100, 
        2
    ) AS on_time_rate_pct,
    
    ROUND(
        COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END)::numeric / 
        NULLIF(COUNT(DISTINCT d.order_id), 0)::numeric * 100, 
        2
    ) AS late_rate_pct,
    
    ROUND(AVG(CASE WHEN d.is_late THEN d.delay_days END)::numeric, 2) AS avg_delay_days,
    ROUND(AVG(CASE WHEN d.handling_days >= 0 THEN d.handling_days END)::numeric, 2) AS avg_handling_days,
    ROUND(AVG(CASE WHEN d.transit_days >= 0 AND d.handling_days >= 0 THEN d.transit_days END)::numeric, 2) AS avg_transit_days,
    ROUND(AVG(d.cycle_days)::numeric, 2) AS avg_total_cycle_days,
    ROUND(AVG(d.review_score)::numeric, 2) AS avg_review_score,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(DISTINCT d.order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT d.order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM fact_order_delivery d
JOIN raw_customers c ON d.customer_id = c.customer_id
WHERE d.is_delivered = TRUE 
  AND d.is_valid_delivery_date = TRUE
GROUP BY c.customer_state
ORDER BY delivered_orders_n DESC;
