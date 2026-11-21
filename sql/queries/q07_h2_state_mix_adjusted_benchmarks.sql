-- ============================================================================
-- QUERY 07: Hypothesis 2 Mix-Adjusted Benchmarks — Destination State Performance
-- BUSINESS OBJECTIVE: Calculate actual vs expected on-time delivery rates per state adjusted for distance mix.
-- GRAIN: Destination State (order-level customer_state from raw_customers).
-- FILTERS APPLIED: Delivered orders with valid delivery dates and computed route distances.
-- METHODOLOGY: Expected on-time rate = SUM( state_share_in_band * global_band_ontime_rate ).
--              Performance Gap (pp) = Actual On-Time Rate (%) - Expected On-Time Rate (%).
-- NOTE ON UNITS & ETA TARGETING:
--   - Performance gaps are strictly reported in percentage points (pp), not percent.
--   - Promised lead times (avg_promised_lead_time_days) and actual cycle times (avg_actual_cycle_days)
--     are reported to illuminate platform ETA dynamics:
--       * AM and RO maintain high on-time delivery rates (97.24% and 97.12%) despite long transit (26.4d and 19.4d)
--         because their promised lead times are generous (45.9d and 39.4d, a ~19-20 day safety buffer).
--       * RJ achieves faster delivery (15.3d actual cycle), but its tighter promised ETA (27.0d) yields
--         a lower on-time rate (87.89%, a negative gap of -5.34 pp vs national benchmark).
--       * SP has tight promised lead time (19.8d) and fast delivery (8.8d actual cycle), achieving 95.51% on-time.
-- ============================================================================

WITH order_distance_bands AS (
    SELECT 
        d.order_id,
        c.customer_state AS destination_state,
        d.is_on_time,
        (d.order_estimated_delivery_date_only - d.order_purchase_date) AS promised_lead_time_days,
        d.cycle_days AS actual_cycle_days,
        CASE 
            WHEN i.route_distance_km IS NULL THEN 'Unknown'
            WHEN i.route_distance_km < 250 THEN '1. Local (<250km)'
            WHEN i.route_distance_km < 500 THEN '2. Regional (250-500km)'
            WHEN i.route_distance_km < 1000 THEN '3. Medium (500-1000km)'
            WHEN i.route_distance_km < 2000 THEN '4. Long (1000-2000km)'
            ELSE '5. Remote (2000km+)'
        END AS distance_band
    FROM fact_order_delivery d
    JOIN raw_customers c ON d.customer_id = c.customer_id
    JOIN (
        SELECT order_id, MAX(route_distance_km) AS route_distance_km
        FROM fact_order_items
        GROUP BY order_id
    ) i ON d.order_id = i.order_id
    WHERE d.is_delivered = TRUE 
      AND d.is_valid_delivery_date = TRUE
),
global_band_benchmarks AS (
    SELECT 
        distance_band,
        COUNT(*) AS global_orders,
        ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END)::numeric, 4) AS global_ontime_rate
    FROM order_distance_bands
    GROUP BY distance_band
),
state_band_mix AS (
    SELECT 
        o.destination_state,
        o.distance_band,
        COUNT(*) AS state_band_orders,
        COUNT(*)::numeric / SUM(COUNT(*)) OVER (PARTITION BY o.destination_state)::numeric AS band_weight
    FROM order_distance_bands o
    GROUP BY o.destination_state, o.distance_band
),
state_expected AS (
    SELECT 
        m.destination_state,
        ROUND(SUM(m.band_weight * b.global_ontime_rate) * 100, 2) AS expected_ontime_rate_pct
    FROM state_band_mix m
    JOIN global_band_benchmarks b ON m.distance_band = b.distance_band
    GROUP BY m.destination_state
),
state_actual AS (
    SELECT 
        destination_state,
        COUNT(*) AS total_delivered_orders,
        ROUND(AVG(CASE WHEN is_on_time THEN 1.0 ELSE 0.0 END) * 100, 2) AS actual_ontime_rate_pct,
        ROUND(AVG(promised_lead_time_days)::numeric, 1) AS avg_promised_lead_time_days,
        ROUND(AVG(actual_cycle_days)::numeric, 1) AS avg_actual_cycle_days
    FROM order_distance_bands
    GROUP BY destination_state
)
SELECT 
    a.destination_state,
    a.total_delivered_orders,
    a.avg_promised_lead_time_days,
    a.avg_actual_cycle_days,
    a.actual_ontime_rate_pct,
    e.expected_ontime_rate_pct,
    ROUND((a.actual_ontime_rate_pct - e.expected_ontime_rate_pct)::numeric, 2) AS mix_adjusted_performance_gap_pp,
    
    -- Sample Size Governance
    CASE 
        WHEN a.total_delivered_orders < 30 THEN 'suppress'
        WHEN a.total_delivered_orders < 100 THEN 'exploratory'
        ELSE 'interpretable'
    END AS sample_size_status

FROM state_actual a
JOIN state_expected e ON a.destination_state = e.destination_state
ORDER BY a.total_delivered_orders DESC;
