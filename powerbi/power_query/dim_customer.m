// ============================================================================
// Table: dim_customer
// Grain: One record per persistent customer entity (customer_unique_id: 96,096 entities).
// Note: Holds customer-level lifetime metrics, cohort definitions, and repeat buyer flags.
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\dim_customer.csv"), [Delimiter=",", Columns=17, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"customer_unique_id", type text},
        {"primary_city", type text},
        {"primary_state", type text},
        {"primary_zip_code_prefix", Int64.Type},
        {"first_order_timestamp", type datetime},
        {"last_order_timestamp", type datetime},
        {"lifetime_orders", Int64.Type},
        {"is_repeat_customer", type logical},
        {"has_delivered_order", type logical},
        {"first_delivered_order_id", type text},
        {"first_delivered_order_date", type date},
        {"first_order_on_time", type logical},
        {"first_order_late", type logical},
        {"total_delivered_orders", Int64.Type},
        {"has_repeat_delivered_order", type logical},
        {"has_repeat_all_order", type logical},
        {"is_mature_cohort", type logical}
    })
in
    #"Changed Type"
