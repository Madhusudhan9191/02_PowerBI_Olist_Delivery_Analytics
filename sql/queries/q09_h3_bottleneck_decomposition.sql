-- ============================================================================
-- QUERY 09: Hypothesis 3 — Fulfillment Bottleneck Decomposition (Handling vs Transit)
-- BUSINESS OBJECTIVE: Decompose end-to-end delivery cycle into merchant handling and carrier transit lead times.
-- GRAIN: Route Flow Type (Intrastate vs Interstate at Order Level).
-- FILTERS APPLIED: Delivered orders with clean non-negative handling and transit times (N = 95,082).
-- ORDER-LEVEL ROUTE CLASSIFICATION:
--   To avoid double-counting multi-item orders (240 orders feature mixed seller origins):
--     - Interstate Flow: Any order where at least one item ships across state boundaries (N = 61,022).
--     - Intrastate Flow: Orders where all items ship within the customer's state (N = 34,060).
--   Sum = 61,022 + 34,060 = 95,082 orders (100% of clean delivered cohort, zero double-counting).
-- ============================================================================

WITH order_routes AS (
    SELECT 
        order_id,
        BOOL_OR(is_interstate) AS has_interstate_item,
        BOOL_OR(NOT is_interstate) AS has_intrastate_item
    FROM fact_order_items
    GROUP BY order_id
),
order_flow AS (
    SELECT 
        d.order_id,
        d.is_on_time,
        d.handling_days,
        d.transit_days,
        d.cycle_days,
        CASE 
            WHEN r.has_interstate_item THEN 'Interstate Flow (Cross-State)'
            ELSE 'Intrastate Flow (Within-State)'
        END AS route_flow_type,
        (r.has_interstate_item AND r.has_intrastate_item) AS is_mixed_origin
    FROM fact_order_delivery d
    JOIN order_routes r ON d.order_id = r.order_id
    WHERE d.is_delivered = TRUE 
      AND d.is_valid_delivery_date = TRUE
      AND d.handling_days >= 0 
      AND d.transit_days >= 0
)
SELECT 
    route_flow_type,
    COUNT(DISTINCT order_id) AS clean_delivered_orders_n,
    
    ROUND(AVG(handling_days)::numeric, 2) AS avg_handling_days,
    ROUND(AVG(transit_days)::numeric, 2) AS avg_transit_days,
    ROUND(AVG(cycle_days)::numeric, 2) AS avg_total_cycle_days,
    
    -- Lead Time Contribution Shares (%)
    ROUND(
        AVG(handling_days)::numeric / 
        NULLIF(AVG(handling_days) + AVG(transit_days), 0)::numeric * 100, 
        2
    ) AS handling_share_of_fulfillment_pct,
    
    ROUND(
        AVG(transit_days)::numeric / 
        NULLIF(AVG(handling_days) + AVG(transit_days), 0)::numeric * 100, 
        2
    ) AS transit_share_of_fulfillment_pct,
    
    ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) * 100, 2) AS on_time_delivery_rate_pct,
    
    -- Sample Size Governance
    CASE 
        WHEN COUNT(DISTINCT order_id) < 30 THEN 'suppress'
        WHEN COUNT(DISTINCT order_id) < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM order_flow
GROUP BY route_flow_type
ORDER BY route_flow_type;
