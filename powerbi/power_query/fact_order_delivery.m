// ============================================================================
// Table: fact_order_delivery
// Grain: One record per order (99,441 orders).
// Features: Order-level delivery milestones, canonical date-level SLA flags,
//           fractional lead times (handling, transit, cycle), QA anomaly flags,
//           order-grain route distance and distance bands, delivery status category,
//           and deduplicated review metrics (latest submission per order).
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\fact_order_delivery.csv"), [Delimiter=",", Columns=44, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", type text},
        {"customer_id", type text},
        {"customer_unique_id", type text},
        {"order_customer_state", type text},
        {"order_customer_city", type text},
        {"order_customer_zip_prefix", Int64.Type},
        {"order_status", type text},
        {"order_purchase_timestamp", type datetime},
        {"order_approved_at", type datetime},
        {"order_delivered_carrier_date", type datetime},
        {"order_delivered_customer_date", type datetime},
        {"order_estimated_delivery_date", type datetime},
        {"order_purchase_date", type date},
        {"order_delivered_customer_date_only", type date},
        {"order_estimated_delivery_date_only", type date},
        {"promised_lead_time_days", Int64.Type},
        {"is_delivered", type logical},
        {"is_valid_delivery_date", type logical},
        {"is_on_time", type logical},
        {"is_late", type logical},
        {"delay_days", Int64.Type},
        {"estimate_variance_days", Int64.Type},
        {"handling_days", type number},
        {"transit_days", type number},
        {"cycle_days", type number},
        {"carrier_before_purchase", type logical},
        {"carrier_before_approved", type logical},
        {"delivery_before_purchase", type logical},
        {"delivery_before_carrier", type logical},
        {"delivery_before_approved", type logical},
        {"has_negative_handling", type logical},
        {"has_negative_transit", type logical},
        {"is_anomalous_sequence", type logical},
        {"is_clean_fulfillment", type logical},
        {"is_steady_state_window", type logical},
        {"order_route_distance_km", type number},
        {"order_distance_band", type text},
        {"order_delivery_status_category", type text},
        {"review_id", type text},
        {"review_score", Int64.Type},
        {"review_creation_date", type date},
        {"review_answer_timestamp", type datetime},
        {"has_review", type logical},
        {"review_created_before_delivery", type logical}
    })
in
    #"Changed Type"
