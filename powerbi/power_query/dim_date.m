// ============================================================================
// Table: dim_date
// Grain: One record per calendar day (2016-01-01 to 2018-10-17).
// Note: Explicitly terminates at the dataset's maximum date (2018-10-17), never TODAY().
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\dim_date.csv"), [Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"date_key", Int64.Type},
        {"full_date", type date},
        {"year_num", Int64.Type},
        {"quarter_num", Int64.Type},
        {"quarter_name", type text},
        {"month_num", Int64.Type},
        {"month_name", type text},
        {"year_month", type text},
        {"week_of_year", Int64.Type},
        {"day_of_month", Int64.Type},
        {"day_of_week", Int64.Type},
        {"day_name", type text},
        {"is_weekend", type logical}
    })
in
    #"Changed Type"
