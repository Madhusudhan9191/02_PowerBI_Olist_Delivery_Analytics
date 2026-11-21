-- ============================================================================
-- QUERY 10: Hypothesis 3 — Key Logistics Trade Lanes & Interstate Corridors
-- BUSINESS OBJECTIVE: Identify carrier transit bottlenecks across top regional trade corridors.
-- GRAIN: Origin State to Destination State (seller_state -> customer_state).
-- FILTERS APPLIED: Delivered orders with clean non-negative lead times and total orders N >= 100.
-- LIMITATIONS: Freight carrier identity is not recorded in the public dataset.
-- ============================================================================

WITH corridor_orders AS (
    SELECT 
        d.order_id,
        s.seller_state AS origin_state,
        c.customer_state AS destination_state,
        d.is_on_time,
        d.handling_days,
        d.transit_days,
        d.cycle_days,
        i.route_distance_km
    FROM fact_order_delivery d
    JOIN fact_order_items i ON d.order_id = i.order_id
    JOIN raw_sellers s ON i.seller_id = s.seller_id
    JOIN raw_customers c ON d.customer_id = c.customer_id
    WHERE d.is_delivered = TRUE 
      AND d.is_valid_delivery_date = TRUE
      AND d.handling_days >= 0 
      AND d.transit_days >= 0
)
SELECT 
    origin_state || ' -> ' || destination_state AS trade_corridor,
    origin_state,
    destination_state,
    COUNT(DISTINCT order_id) AS delivered_orders_n,
    
    ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) * 100, 2) AS on_time_delivery_rate_pct,
    ROUND(AVG(transit_days)::numeric, 2) AS avg_carrier_transit_days,
    ROUND(AVG(handling_days)::numeric, 2) AS avg_merchant_handling_days,
    ROUND(AVG(route_distance_km)::numeric, 0) AS avg_distance_km,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(DISTINCT order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM corridor_orders
GROUP BY origin_state, destination_state
HAVING COUNT(DISTINCT order_id) >= 100
ORDER BY delivered_orders_n DESC
LIMIT 20;
