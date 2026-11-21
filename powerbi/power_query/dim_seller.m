// ============================================================================
// Table: dim_seller
// Grain: One record per distinct merchant (seller_id: 3,095 sellers).
// Note: Includes seller lifetime orders and volume tiers (Tiers 1 to 4).
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\dim_seller.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"seller_id", type text},
        {"seller_zip_code_prefix", Int64.Type},
        {"seller_city", type text},
        {"seller_state", type text},
        {"seller_lifetime_orders", Int64.Type},
        {"seller_tier", type text}
    })
in
    #"Changed Type"
