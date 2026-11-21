-- ============================================================================
-- QUERY 04: Hypothesis 1 Deep-Dive — Review Timing Relative to Delivery
-- BUSINESS OBJECTIVE: Quantify the proportion of late-delivery reviews submitted before vs after delivery.
-- GRAIN: Delivery Timeliness Cohort x Review Submission Timing (Pre-Delivery vs Post-Delivery).
-- FILTERS APPLIED: Delivered orders with valid delivery dates and deduplicated reviews (N = 95,824).
-- LIMITATIONS: The dataset records timestamp sequence only; customer intent, survey dispatch logic,
--              or psychological motives are not observed in the data.
-- ============================================================================

SELECT 
    CASE WHEN d.is_late THEN 'Late Delivery' ELSE 'On-Time Delivery' END AS delivery_timeliness,
    CASE 
        WHEN d.review_created_before_delivery THEN 'Reviewed Before Delivery'
        ELSE 'Reviewed On/After Delivery'
    END AS review_timing_cohort,
    
    COUNT(DISTINCT d.order_id) AS reviewed_orders_n,
    
    ROUND(
        COUNT(DISTINCT d.order_id)::numeric / 
        SUM(COUNT(DISTINCT d.order_id)) OVER (PARTITION BY d.is_late)::numeric * 100, 
        2
    ) AS cohort_share_pct,
    
    ROUND(AVG(d.review_score)::numeric, 4) AS avg_review_score,
    ROUND(COUNT(CASE WHEN d.review_score IN (1, 2) THEN 1 END)::numeric / COUNT(*)::numeric * 100, 2) AS pct_1_2_star,
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
GROUP BY d.is_late, d.review_created_before_delivery
ORDER BY d.is_late DESC, d.review_created_before_delivery DESC;
