-- ============================================================================
-- QUERY 11: Hypothesis 4 — Freight Burden Across Geographic Distance & Weight Tiers
-- BUSINESS OBJECTIVE: Quantify freight cost per kg and burden ratio across distance bands holding product weight constant.
-- GRAIN: Distance Band x Product Weight Tier.
-- FILTERS APPLIED: Order items with valid route distance and non-null positive product weight (N = 105,431 items).
-- METHODOLOGY:
--   - Weight Tiers: Light (< 1kg), Medium (1-5kg), Heavy (5kg+).
--   - Freight per kg (BRL/kg) = freight_value / (product_weight_g / 1000.0).
--   - Reports both Mean and Median freight per kg to account for skewness.
-- ============================================================================

WITH item_segments AS (
    SELECT 
        i.order_id,
        i.order_item_id,
        i.price,
        i.freight_value,
        p.product_weight_g,
        (p.product_weight_g / 1000.0) AS weight_kg,
        (i.freight_value / NULLIF(p.product_weight_g / 1000.0, 0)) AS freight_per_kg,
        CASE 
            WHEN i.route_distance_km < 250 THEN '1. Local (<250km)'
            WHEN i.route_distance_km < 500 THEN '2. Regional (250-500km)'
            WHEN i.route_distance_km < 1000 THEN '3. Medium (500-1000km)'
            WHEN i.route_distance_km < 2000 THEN '4. Long (1000-2000km)'
            ELSE '5. Remote (2000km+)'
        END AS distance_band,
        CASE 
            WHEN p.product_weight_g < 1000 THEN '1. Light (<1kg)'
            WHEN p.product_weight_g < 5000 THEN '2. Medium (1-5kg)'
            ELSE '3. Heavy (5kg+)'
        END AS weight_tier
    FROM fact_order_items i
    JOIN dim_product p ON i.product_id = p.product_id
    WHERE i.route_distance_km IS NOT NULL
      AND p.product_weight_g IS NOT NULL
      AND p.product_weight_g > 0
)
SELECT 
    distance_band,
    weight_tier,
    COUNT(*) AS order_items_n,
    
    ROUND(AVG(price)::numeric, 2) AS avg_item_price_brl,
    ROUND(AVG(freight_value)::numeric, 2) AS avg_freight_value_brl,
    ROUND(AVG(freight_per_kg)::numeric, 2) AS avg_freight_per_kg_brl,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY freight_per_kg)::numeric, 2) AS median_freight_per_kg_brl,
    
    -- Freight to Price Ratio (%)
    ROUND(
        (SUM(freight_value) / NULLIF(SUM(price), 0))::numeric * 100, 
        2
    ) AS freight_to_price_ratio_pct,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(*) < 30 THEN 'suppress'
        WHEN COUNT(*) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM item_segments
GROUP BY distance_band, weight_tier
ORDER BY distance_band, weight_tier;
