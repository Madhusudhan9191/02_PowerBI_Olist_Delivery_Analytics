// ============================================================================
// Table: dim_product
// Grain: One record per catalog item (product_id: 32,951 products).
// Categories: Portuguese and English translations with explicit category fallback.
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\dim_product.csv"), [Delimiter=",", Columns=10, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"product_id", type text},
        {"product_category_name_pt", type text},
        {"product_category_name_en", type text},
        {"product_name_lenght", Int64.Type},
        {"product_description_lenght", Int64.Type},
        {"product_photos_qty", Int64.Type},
        {"product_weight_g", type number},
        {"product_length_cm", type number},
        {"product_height_cm", type number},
        {"product_width_cm", type number}
    }),
    #"Added Weight kg" = Table.AddColumn(#"Changed Type", "product_weight_kg", each if [product_weight_g] <> null then [product_weight_g] / 1000.0 else null, type number),
    #"Added Weight Tier" = Table.AddColumn(#"Added Weight kg", "weight_tier", each 
        if [product_weight_g] = null then "Unknown"
        else if [product_weight_g] < 1000 then "1. Light (<1kg)"
        else if [product_weight_g] < 5000 then "2. Medium (1-5kg)"
        else "3. Heavy (5kg+)", type text)
in
    #"Added Weight Tier"
