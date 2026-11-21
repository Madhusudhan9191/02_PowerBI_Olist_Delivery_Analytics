-- ============================================================================
-- QUERY 05: Hypothesis 1 Mix Control — Category-Level Satisfaction Impact
-- BUSINESS OBJECTIVE: Test whether late delivery is associated with lower reviews within product categories.
-- GRAIN: Product Category (English).
-- FILTERS APPLIED: Delivered orders with valid delivery dates and reviews; categories with total N >= 30.
-- SAMPLE SIZE GOVERNANCE:
--   Total categories with N >= 30: 63 categories.
--   Governance applied to late reviewed cohort (late_orders_n):
--     - Interpretable (N_late >= 100): 18 categories
--     - Exploratory (30 <= N_late < 100): 11 categories
--     - Suppressed (N_late < 30): 34 categories
--   Key Finding: Across all 29 qualifying categories (N_late >= 30), the satisfaction gap
--   is strictly negative, ranging from -1.40 points (office_furniture) to -2.51 points (musical_instruments).
-- ============================================================================

WITH item_cats AS (
    SELECT DISTINCT 
        i.order_id,
        p.product_category_name_en
    FROM fact_order_items i
    JOIN dim_product p ON i.product_id = p.product_id
),
cat_metrics AS (
    SELECT 
        c.product_category_name_en,
        COUNT(DISTINCT d.order_id) AS total_reviewed_orders,
        
        -- On-Time Cohort
        COUNT(DISTINCT CASE WHEN d.is_on_time THEN d.order_id END) AS ontime_orders_n,
        ROUND(AVG(CASE WHEN d.is_on_time THEN d.review_score END)::numeric, 2) AS ontime_avg_score,
        
        -- Late Cohort
        COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END) AS late_orders_n,
        ROUND(AVG(CASE WHEN d.is_late THEN d.review_score END)::numeric, 2) AS late_avg_score,
        
        -- Score Gap (Late - On-Time)
        ROUND(
            (AVG(CASE WHEN d.is_late THEN d.review_score END) - 
             AVG(CASE WHEN d.is_on_time THEN d.review_score END))::numeric, 
            2
        ) AS score_delta_late_vs_ontime,
        
        -- Late Rate %
        ROUND(
            COUNT(DISTINCT CASE WHEN d.is_late THEN d.order_id END)::numeric / 
            NULLIF(COUNT(DISTINCT d.order_id), 0)::numeric * 100, 
            2
        ) AS category_late_rate_pct

    FROM fact_order_delivery d
    JOIN item_cats c ON d.order_id = c.order_id
    WHERE d.is_delivered = TRUE 
      AND d.is_valid_delivery_date = TRUE 
      AND d.has_review = TRUE
    GROUP BY c.product_category_name_en
)
SELECT 
    product_category_name_en,
    total_reviewed_orders,
    ontime_orders_n,
    ontime_avg_score,
    late_orders_n,
    late_avg_score,
    score_delta_late_vs_ontime,
    category_late_rate_pct,
    
    -- Sample Size Governance on Late Cohort
    CASE 
        WHEN late_orders_n < 30 THEN 'suppress'
        WHEN late_orders_n < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS late_sample_size_status

FROM cat_metrics
WHERE total_reviewed_orders >= 30
ORDER BY late_orders_n DESC, total_reviewed_orders DESC;
