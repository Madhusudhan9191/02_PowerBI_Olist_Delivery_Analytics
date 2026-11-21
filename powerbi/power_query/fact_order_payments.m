// ============================================================================
// Table: fact_order_payments
// Grain: One record per payment sequence (103,886 payment transactions).
// Features: Payment method, installments, and captured monetary value.
// ============================================================================

let
    Source = Csv.Document(File.Contents(SourceFolder & "\fact_order_payments.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", type text},
        {"payment_sequential", Int64.Type},
        {"payment_type", type text},
        {"payment_installments", Int64.Type},
        {"payment_value", type number}
    })
in
    #"Changed Type"
