import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

dax_script = """// ============================================================================
// DAX QUERY VIEW SCRIPT: All 63 Reconciliation Measures in ONE Table
// Instructions:
// 1. In Power BI Desktop, click "DAX Query View" (the icon with table + calculator on left bar).
// 2. Click "New query" or paste this entire script into Query 1.
// 3. Click "Run" (F5).
// 4. In the Results pane below, click anywhere in the table, press Ctrl+A, then right-click -> "Copy table"
//    (or click the "Export data" / "Save results" button).
// 5. Save/paste to: data/processed/powerbi_input/dax_all_63_export.csv
// ============================================================================

EVALUATE
UNION(
    // 01 Volume and Spend (Rows 01-09)
    ROW("Index", "01", "Measure_Name", "Total Orders", "Value", FORMAT([Total Orders], "#,0")),
    ROW("Index", "02", "Measure_Name", "Delivered Orders", "Value", FORMAT([Delivered Orders], "#,0")),
    ROW("Index", "03", "Measure_Name", "Valid Delivered Orders", "Value", FORMAT([Valid Delivered Orders], "#,0")),
    ROW("Index", "04", "Measure_Name", "Gross Item Revenue", "Value", FORMAT([Gross Item Revenue], "R$ #,##0.00")),
    ROW("Index", "05", "Measure_Name", "Total Freight Billed", "Value", FORMAT([Total Freight Billed], "R$ #,##0.00")),
    ROW("Index", "06", "Measure_Name", "Total Customer Spend", "Value", FORMAT([Total Customer Spend], "R$ #,##0.00")),
    ROW("Index", "07", "Measure_Name", "Captured Payment Value", "Value", FORMAT([Captured Payment Value], "R$ #,##0.00")),
    ROW("Index", "08", "Measure_Name", "Total Unique Customers", "Value", FORMAT([Total Unique Customers], "#,0")),
    ROW("Index", "09", "Measure_Name", "Total Active Sellers", "Value", FORMAT([Total Active Sellers], "#,0")),

    // 02 Delivery SLA (Rows 10-17)
    ROW("Index", "10", "Measure_Name", "On-Time Orders", "Value", FORMAT([On-Time Orders], "#,0")),
    ROW("Index", "11", "Measure_Name", "Late Orders", "Value", FORMAT([Late Orders], "#,0")),
    ROW("Index", "12", "Measure_Name", "On-Time Delivery Rate %", "Value", FORMAT([On-Time Delivery Rate %], "0.00%")),
    ROW("Index", "13", "Measure_Name", "Late Delivery Rate %", "Value", FORMAT([Late Delivery Rate %], "0.00%")),
    ROW("Index", "14", "Measure_Name", "Average Delay Days (Late Orders)", "Value", FORMAT([Average Delay Days (Late Orders)], "0.00 days")),
    ROW("Index", "15", "Measure_Name", "Average Promised Lead Time Days", "Value", FORMAT([Average Promised Lead Time Days], "0.00 days")),
    ROW("Index", "16", "Measure_Name", "Average Actual Cycle Days", "Value", FORMAT([Average Actual Cycle Days], "0.00 days")),
    ROW("Index", "17", "Measure_Name", "ETA Safety Buffer Days", "Value", FORMAT([ETA Safety Buffer Days], "0.00 days")),

    // 03 Review Satisfaction (Rows 18-35)
    ROW("Index", "18", "Measure_Name", "Total Reviewed Orders", "Value", FORMAT([Total Reviewed Orders], "#,0")),
    ROW("Index", "19", "Measure_Name", "Delivered Reviewed Orders", "Value", FORMAT([Delivered Reviewed Orders], "#,0")),
    ROW("Index", "20", "Measure_Name", "Average Review Score", "Value", FORMAT([Average Review Score], "0.0000")),
    ROW("Index", "21", "Measure_Name", "Average Review Score (Delivered)", "Value", FORMAT([Average Review Score (Delivered)], "0.0000")),
    ROW("Index", "22", "Measure_Name", "Average Review Score (On-Time)", "Value", FORMAT([Average Review Score (On-Time)], "0.0000")),
    ROW("Index", "23", "Measure_Name", "Average Review Score (Late)", "Value", FORMAT([Average Review Score (Late)], "0.0000")),
    ROW("Index", "24", "Measure_Name", "Review Score Gap (Late vs On-Time)", "Value", FORMAT([Review Score Gap (Late vs On-Time)], "0.00 points")),
    ROW("Index", "25", "Measure_Name", "Negative Reviews Count (1-2 Star)", "Value", FORMAT([Negative Reviews Count (1-2 Star)], "#,0")),
    ROW("Index", "26", "Measure_Name", "Negative Review Share %", "Value", FORMAT([Negative Review Share %], "0.00%")),
    ROW("Index", "27", "Measure_Name", "Negative Review Share % (Late)", "Value", FORMAT([Negative Review Share % (Late)], "0.00%")),
    ROW("Index", "28", "Measure_Name", "Negative Review Share % (On-Time)", "Value", FORMAT([Negative Review Share % (On-Time)], "0.00%")),
    ROW("Index", "29", "Measure_Name", "5-Star Reviews Count", "Value", FORMAT([5-Star Reviews Count], "#,0")),
    ROW("Index", "30", "Measure_Name", "5-Star Review Share % (Late)", "Value", FORMAT([5-Star Review Share % (Late)], "0.00%")),
    ROW("Index", "31", "Measure_Name", "5-Star Review Share % (On-Time)", "Value", FORMAT([5-Star Review Share % (On-Time)], "0.00%")),
    ROW("Index", "32", "Measure_Name", "Pre-Delivery Late Reviews Count", "Value", FORMAT([Pre-Delivery Late Reviews Count], "#,0")),
    ROW("Index", "33", "Measure_Name", "Pre-Delivery Late Review Share %", "Value", FORMAT([Pre-Delivery Late Review Share %], "0.00%")),
    ROW("Index", "34", "Measure_Name", "Avg Review Score (Pre-Delivery Late)", "Value", FORMAT([Avg Review Score (Pre-Delivery Late)], "0.0000")),
    ROW("Index", "35", "Measure_Name", "Avg Review Score (Post-Delivery Late)", "Value", FORMAT([Avg Review Score (Post-Delivery Late)], "0.0000")),

    // 04 Fulfillment Bottlenecks (Rows 36-45)
    ROW("Index", "36", "Measure_Name", "Clean Fulfillment Orders", "Value", FORMAT([Clean Fulfillment Orders], "#,0")),
    ROW("Index", "37", "Measure_Name", "Average Handling Days", "Value", FORMAT([Average Handling Days], "0.00 days")),
    ROW("Index", "38", "Measure_Name", "Average Transit Days", "Value", FORMAT([Average Transit Days], "0.00 days")),
    ROW("Index", "39", "Measure_Name", "Average Fulfillment Cycle Days", "Value", FORMAT([Average Fulfillment Cycle Days], "0.00 days")),
    ROW("Index", "40", "Measure_Name", "Handling Share of Fulfillment %", "Value", FORMAT([Handling Share of Fulfillment %], "0.00%")),
    ROW("Index", "41", "Measure_Name", "Transit Share of Fulfillment %", "Value", FORMAT([Transit Share of Fulfillment %], "0.00%")),
    ROW("Index", "42", "Measure_Name", "Interstate Orders Count", "Value", FORMAT([Interstate Orders Count], "#,0")),
    ROW("Index", "43", "Measure_Name", "Intrastate Orders Count", "Value", FORMAT([Intrastate Orders Count], "#,0")),
    ROW("Index", "44", "Measure_Name", "Interstate On-Time Rate %", "Value", FORMAT([Interstate On-Time Rate %], "0.00%")),
    ROW("Index", "45", "Measure_Name", "Intrastate On-Time Rate %", "Value", FORMAT([Intrastate On-Time Rate %], "0.00%")),

    // 05 Regional Mix-Adjusted Gaps (Rows 46-48)
    ROW("Index", "46", "Measure_Name", "Mix-Adjusted Performance Gap pp (RJ)", "Value", FORMAT(CALCULATE([Mix-Adjusted Performance Gap pp], fact_order_delivery[order_customer_state] = "RJ"), "0.00 pp")),
    ROW("Index", "47", "Measure_Name", "Mix-Adjusted Performance Gap pp (SP)", "Value", FORMAT(CALCULATE([Mix-Adjusted Performance Gap pp], fact_order_delivery[order_customer_state] = "SP"), "+0.00 pp;-0.00 pp;0.00 pp")),
    ROW("Index", "48", "Measure_Name", "Mix-Adjusted Performance Gap pp (AL)", "Value", FORMAT(CALCULATE([Mix-Adjusted Performance Gap pp], fact_order_delivery[order_customer_state] = "AL"), "0.00 pp")),

    // 05 Seller Tiers Late Dispatch Rates (Rows 49-52)
    ROW("Index", "49", "Measure_Name", "Late Dispatch Rate % (Tier 1)", "Value", FORMAT(CALCULATE([Late Dispatch Rate %], dim_seller[seller_tier] = "Tier 1: High Volume (500+ orders)"), "0.00%")),
    ROW("Index", "50", "Measure_Name", "Late Dispatch Rate % (Tier 2)", "Value", FORMAT(CALCULATE([Late Dispatch Rate %], dim_seller[seller_tier] = "Tier 2: Mid Volume (100-499 orders)"), "0.00%")),
    ROW("Index", "51", "Measure_Name", "Late Dispatch Rate % (Tier 3)", "Value", FORMAT(CALCULATE([Late Dispatch Rate %], dim_seller[seller_tier] = "Tier 3: Low Volume (30-99 orders)"), "0.00%")),
    ROW("Index", "52", "Measure_Name", "Late Dispatch Rate % (Tier 4)", "Value", FORMAT(CALCULATE([Late Dispatch Rate %], dim_seller[seller_tier] = "Tier 4: Micro Volume (<30 orders)"), "0.00%")),

    // 07 Retention and Cohorts (Rows 53-63)
    ROW("Index", "53", "Measure_Name", "Total Repeat Customers", "Value", FORMAT([Total Repeat Customers], "#,0")),
    ROW("Index", "54", "Measure_Name", "Repeat Customer Rate %", "Value", FORMAT([Repeat Customer Rate %], "0.00%")),
    ROW("Index", "55", "Measure_Name", "Delivered Repeat Rate % (On-Time)", "Value", FORMAT([Delivered Repeat Rate % (On-Time First Order)], "0.00%")),
    ROW("Index", "56", "Measure_Name", "Delivered Repeat Rate % (Late)", "Value", FORMAT([Delivered Repeat Rate % (Late First Order)], "0.00%")),
    ROW("Index", "57", "Measure_Name", "Delivered Repeat Rate Gap pp", "Value", FORMAT([Delivered Repeat Rate Gap pp], "0.00 pp")),
    ROW("Index", "58", "Measure_Name", "Mature Repeat Rate % (On-Time)", "Value", FORMAT([Mature Repeat Rate % (On-Time First Order)], "0.00%")),
    ROW("Index", "59", "Measure_Name", "Mature Repeat Rate % (Late)", "Value", FORMAT([Mature Repeat Rate % (Late First Order)], "0.00%")),
    ROW("Index", "60", "Measure_Name", "Mature Repeat Rate Gap pp", "Value", FORMAT([Mature Repeat Rate Gap pp], "0.00 pp")),
    ROW("Index", "61", "Measure_Name", "Mature Delivered Repeat Rate % (On-Time)", "Value", FORMAT([Mature Delivered Repeat Rate % (On-Time First Order)], "0.00%")),
    ROW("Index", "62", "Measure_Name", "Mature Delivered Repeat Rate % (Late)", "Value", FORMAT([Mature Delivered Repeat Rate % (Late First Order)], "0.00%")),
    ROW("Index", "63", "Measure_Name", "Mature Delivered Repeat Rate Gap pp", "Value", FORMAT([Mature Delivered Repeat Rate Gap pp], "0.00 pp"))
)
"""

out_path = os.path.join(base_dir, "powerbi", "dax", "evaluate_all_63_measures.dax")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(dax_script)
print(f"Generated {out_path}")
