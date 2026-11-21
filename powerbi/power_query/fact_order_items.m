// ============================================================================
// Table: fact_order_items
// Grain: One record per order item (order_id, order_item_id: 112,650 items).
// Features: Merchandise price, freight charges, total customer spend,
//           freight per kg, late merchant dispatch flag, Haversine route distances (km),
//           item-level distance band, and interstate flow flags.
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\fact_order_items.csv"), [Delimiter=",", Columns=18, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", type text},
        {"order_item_id", Int64.Type},
        {"product_id", type text},
        {"seller_id", type text},
        {"customer_unique_id", type text},
        {"order_purchase_date", type date},
        {"shipping_limit_date", type datetime},
        {"price", type number},
        {"freight_value", type number},
        {"total_item_spend", type number},
        {"freight_to_price_ratio", type number},
        {"freight_per_kg", type number},
        {"is_late_dispatch", type logical},
        {"customer_zip_prefix", Int64.Type},
        {"seller_zip_prefix", Int64.Type},
        {"route_distance_km", type number},
        {"distance_band", type text},
        {"is_interstate", type logical}
    })
in
    #"Changed Type"
