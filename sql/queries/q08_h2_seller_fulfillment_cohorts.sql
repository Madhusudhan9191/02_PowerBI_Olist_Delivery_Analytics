-- ============================================================================
-- QUERY 08: Hypothesis 2 — Merchant Fulfillment Performance by Seller Volume Tiers
-- BUSINESS OBJECTIVE: Evaluate merchant handling lead times and late-dispatch rates across seller cohorts.
-- GRAIN: Seller Volume Cohort.
-- SELLER TIER DEFINITIONS (Computed across all orders in dataset for all 3,095 sellers):
--   - Tier 1: High Volume (500+ orders) -> 26 sellers
--   - Tier 2: Mid Volume (100-499 orders) -> 184 sellers
--   - Tier 3: Low Volume (30-99 orders) -> 424 sellers
--   - Tier 4: Micro Volume (<30 orders) -> 2,461 sellers
--   Total Sellers = 3,095 sellers.
-- FILTERS APPLIED: Delivered orders with clean fulfillment (is_clean_fulfillment = TRUE).
--   Active sellers in clean delivered cohort = 2,959 (Tier 1: 26, Tier 2: 184, Tier 3: 424, Tier 4: 2,325).
--   The remaining 136 sellers in Tier 4 had orders that were canceled/unavailable or had anomalous fulfillment.
-- ============================================================================

WITH seller_order_counts AS (
    SELECT 
        seller_id,
        COUNT(DISTINCT order_id) AS seller_lifetime_orders
    FROM fact_order_items
    GROUP BY seller_id
),
seller_order_facts AS (
    SELECT 
        i.order_id,
        i.seller_id,
        soc.seller_lifetime_orders,
        CASE 
            WHEN soc.seller_lifetime_orders >= 500 THEN 'Tier 1: High Volume (500+ orders)'
            WHEN soc.seller_lifetime_orders >= 100 THEN 'Tier 2: Mid Volume (100-499 orders)'
            WHEN soc.seller_lifetime_orders >= 30  THEN 'Tier 3: Low Volume (30-99 orders)'
            ELSE 'Tier 4: Micro Volume (<30 orders)'
        END AS seller_tier,
        d.is_on_time,
        d.handling_days,
        d.review_score,
        -- Merchant dispatch deadline compliance
        (d.order_delivered_carrier_date > i.shipping_limit_date) AS is_late_dispatch
    FROM fact_order_items i
    JOIN seller_order_counts soc ON i.seller_id = soc.seller_id
    JOIN fact_order_delivery d ON i.order_id = d.order_id
    WHERE d.is_clean_fulfillment = TRUE
)
SELECT 
    seller_tier,
    COUNT(DISTINCT seller_id) AS distinct_sellers_count,
    COUNT(DISTINCT order_id) AS delivered_orders_n,
    
    ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) * 100, 2) AS on_time_delivery_rate_pct,
    ROUND(AVG(handling_days)::numeric, 2) AS avg_seller_handling_days,
    ROUND(AVG(CASE WHEN is_late_dispatch THEN 1.0 ELSE 0.0 END) * 100, 2) AS late_dispatch_rate_pct,
    ROUND(AVG(review_score)::numeric, 2) AS avg_review_score,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(DISTINCT order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM seller_order_facts
GROUP BY seller_tier
ORDER BY seller_tier;
