-- ============================================================================
-- QUERY 03: Hypothesis 1 — Late Delivery and Customer Satisfaction
-- BUSINESS OBJECTIVE: Test observational association between delivery timeliness and review ratings.
-- GRAIN: Delivery Timeliness Cohort (On-Time vs Late).
-- FILTERS APPLIED: Delivered orders with valid delivery dates and deduplicated reviews (N = 95,824).
-- LIMITATIONS: Observational data only; does not establish causality. Confounding variables 
--              (product defects, merchant communication) are partially controlled in Q05.
-- ============================================================================

SELECT 
    CASE WHEN d.is_late THEN 'Late Delivery' ELSE 'On-Time Delivery' END AS delivery_cohort,
    COUNT(DISTINCT d.order_id) AS reviewed_orders_n,
    
    ROUND(AVG(d.review_score)::numeric, 4) AS avg_review_score,
    
    -- Rating Distribution
    COUNT(CASE WHEN d.review_score IN (1, 2) THEN 1 END) AS count_1_2_star,
    ROUND(COUNT(CASE WHEN d.review_score IN (1, 2) THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) AS pct_1_2_star,
    
    COUNT(CASE WHEN d.review_score = 3 THEN 1 END) AS count_3_star,
    ROUND(COUNT(CASE WHEN d.review_score = 3 THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) AS pct_3_star,
    
    COUNT(CASE WHEN d.review_score = 4 THEN 1 END) AS count_4_star,
    ROUND(COUNT(CASE WHEN d.review_score = 4 THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) AS pct_4_star,
    
    COUNT(CASE WHEN d.review_score = 5 THEN 1 END) AS count_5_star,
    ROUND(COUNT(CASE WHEN d.review_score = 5 THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) AS pct_5_star,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(DISTINCT d.order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT d.order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM fact_order_delivery d
WHERE d.is_delivered = TRUE 
  AND d.is_valid_delivery_date = TRUE 
  AND d.has_review = TRUE
GROUP BY d.is_late
ORDER BY d.is_late DESC;
