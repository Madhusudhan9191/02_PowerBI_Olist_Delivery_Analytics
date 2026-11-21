// ============================================================================
// Table: dim_geography
// Grain: One record per 5-digit zip code prefix (19,015 prefixes).
// Coordinates: Median latitude and longitude with modal city/state.
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\dim_geography.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"zip_code_prefix", Int64.Type},
        {"median_lat", type number},
        {"median_lng", type number},
        {"primary_city", type text},
        {"primary_state", type text},
        {"coordinate_count", Int64.Type}
    })
in
    #"Changed Type"
