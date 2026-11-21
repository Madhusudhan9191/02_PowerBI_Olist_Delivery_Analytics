"""
Validation Script: PostgreSQL Data Warehouse vs. Independent Pandas Control Totals
Project: Olist E-commerce Delivery Performance & Customer Satisfaction
Version: 1.0.0
Author: Independent Portfolio Project

Reads canonical control totals from data/processed/profiling_results.json
and queries PostgreSQL to verify row counts, key integrity, and business KPIs.
Outputs a structured PASS/FAIL reconciliation table.

Usage:
    python python/02_validate_warehouse.py --dbname olist_db --user postgres --password secret --host localhost --port 5432
    (or set PG_DATABASE, PG_USER, PG_PASSWORD, PG_HOST, PG_PORT environment variables)
"""

import os
import sys
import json
import argparse
import subprocess

def load_control_totals():
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "profiling_results.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Cannot find profiling_results.json at: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def execute_query_psql(query, dbname, user, password, host, port):
    """Fallback query execution using psql CLI if no python driver is installed."""
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    
    cmd = [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "-A", "-t", "-c", query
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"psql error: {res.stderr.strip()}")
    return res.stdout.strip()

def get_db_connection(dbname, user, password, host, port):
    """Attempt connection via SQLAlchemy/asyncpg or fallback to psql CLI wrapper."""
    try:
        from sqlalchemy import create_engine, text
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        engine = create_engine(conn_str)
        conn = engine.connect()
        def runner(q):
            res = conn.execute(text(q)).fetchall()
            return res
        return runner, "sqlalchemy"
    except Exception:
        # Fallback to psql runner
        def runner(q):
            out = execute_query_psql(q, dbname, user, password, host, port)
            lines = [line.split("|") for line in out.splitlines() if line]
            return lines
        return runner, "psql_cli"

def run_validations(runner, control_data):
    ct = control_data["control_totals"]
    dur_clean = control_data["delivery_sla"]["duration_stats_clean"]
    h1 = control_data["h1_satisfaction_analysis"]
    
    checks = []
    
    def safe_float(val, default=0.0):
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    def safe_int(val, default=0):
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    def add_check(cid, name, expected, actual, tolerance=0.001):
        try:
            exp_val = float(expected)
            act_val = float(actual)
            diff = abs(exp_val - act_val)
            passed = diff <= tolerance
        except (ValueError, TypeError):
            passed = (str(expected).strip() == str(actual).strip())
            diff = 0 if passed else 1
        
        status = "PASS" if passed else "FAIL"
        checks.append({
            "id": cid,
            "metric": name,
            "expected": expected,
            "actual": actual,
            "diff": diff,
            "status": status
        })

    print("Running warehouse verification checks against PostgreSQL...")

    # 1. Total Orders
    res = runner("SELECT COUNT(*) FROM fact_order_delivery;")[0][0]
    add_check("C01", "Total Orders Count", ct["total_orders"], safe_int(res))

    # 2. Total Order Items
    res = runner("SELECT COUNT(*) FROM fact_order_items;")[0][0]
    add_check("C02", "Total Order Items Count", ct["total_order_items"], safe_int(res))

    # 3. Total Payments Count
    res = runner("SELECT COUNT(*) FROM fact_order_payments;")[0][0]
    add_check("C03", "Total Order Payments Count", 103886, safe_int(res))

    # 4. Total Customers (Unique Entities)
    res = runner("SELECT COUNT(*) FROM dim_customer;")[0][0]
    add_check("C04", "Unique Customers Count (dim_customer)", ct["total_customer_unique_id_count"], safe_int(res))

    # 5. Repeat Customers Count
    res = runner("SELECT COUNT(*) FROM dim_customer WHERE is_repeat_customer = TRUE;")[0][0]
    add_check("C05", "Repeat Customers Count", ct["repeat_customers_count"], safe_int(res))

    # 6. Repeat Customer Rate
    res = runner("SELECT ROUND((COUNT(CASE WHEN is_repeat_customer THEN 1 END)::numeric / NULLIF(COUNT(*), 0)::numeric) * 100, 4) FROM dim_customer;")[0][0]
    add_check("C06", "Repeat Customer Rate (%)", ct["repeat_customer_rate_pct"], safe_float(res))

    # 7. Gross Item Revenue (GMV)
    res = runner("SELECT ROUND(SUM(price), 2) FROM fact_order_items;")[0][0]
    add_check("C07", "Gross Item Revenue (BRL)", ct["total_item_revenue_brl"], safe_float(res))

    # 8. Total Freight Billed
    res = runner("SELECT ROUND(SUM(freight_value), 2) FROM fact_order_items;")[0][0]
    add_check("C08", "Total Freight Billed (BRL)", ct["total_freight_value_brl"], safe_float(res))

    # 9. Total Customer Spend (Items)
    res = runner("SELECT ROUND(SUM(total_item_spend), 2) FROM fact_order_items;")[0][0]
    add_check("C09", "Total Customer Item Spend (BRL)", ct["total_customer_spend_brl"], safe_float(res))

    # 10. Total Captured Payments
    res = runner("SELECT ROUND(SUM(payment_value), 2) FROM fact_order_payments;")[0][0]
    add_check("C10", "Total Captured Payments (BRL)", ct["total_payment_value_brl"], safe_float(res))

    # 11. Delivered Orders (Valid Date)
    res = runner("SELECT COUNT(*) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE;")[0][0]
    add_check("C11", "Delivered Orders (with Delivery Date)", ct["delivered_orders_with_date"], safe_int(res))

    # 12. Delivered Order Items
    res = runner("""
        SELECT COUNT(*) 
        FROM fact_order_items i
        JOIN fact_order_delivery d ON i.order_id = d.order_id
        WHERE d.is_delivered = TRUE AND d.is_valid_delivery_date = TRUE;
    """)[0][0]
    add_check("C12", "Delivered Order Items", ct["delivered_order_items"], safe_int(res))

    # 13. Delivered Gross Revenue
    res = runner("""
        SELECT ROUND(SUM(i.price), 2)
        FROM fact_order_items i
        JOIN fact_order_delivery d ON i.order_id = d.order_id
        WHERE d.is_delivered = TRUE AND d.is_valid_delivery_date = TRUE;
    """)[0][0]
    add_check("C13", "Delivered Item Revenue (BRL)", ct["delivered_item_revenue_brl"], safe_float(res))

    # 14. Delivered Freight
    res = runner("""
        SELECT ROUND(SUM(i.freight_value), 2)
        FROM fact_order_items i
        JOIN fact_order_delivery d ON i.order_id = d.order_id
        WHERE d.is_delivered = TRUE AND d.is_valid_delivery_date = TRUE;
    """)[0][0]
    add_check("C14", "Delivered Freight Value (BRL)", ct["delivered_freight_value_brl"], safe_float(res))

    # 15. Date-Level On-Time Delivered Orders
    res = runner("SELECT COUNT(*) FROM fact_order_delivery WHERE is_on_time = TRUE;")[0][0]
    add_check("C15", "On-Time Delivered Orders (Date-Level)", ct["date_level_ontime_delivered_orders"], safe_int(res))

    # 16. Date-Level Late Delivered Orders
    res = runner("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late = TRUE;")[0][0]
    add_check("C16", "Late Delivered Orders (Date-Level)", ct["date_level_late_delivered_orders"], safe_int(res))

    # 17. Date-Level On-Time Rate (%)
    res = runner("""
        SELECT ROUND((COUNT(CASE WHEN is_on_time THEN 1 END)::numeric / 
                      NULLIF(COUNT(CASE WHEN is_delivered AND is_valid_delivery_date THEN 1 END), 0)::numeric) * 100, 4)
        FROM fact_order_delivery;
    """)[0][0]
    add_check("C17", "On-Time Delivery Rate (%)", ct["date_level_ontime_delivery_rate_pct"], safe_float(res))

    # 18. Date-Level Late Rate (%)
    res = runner("""
        SELECT ROUND((COUNT(CASE WHEN is_late THEN 1 END)::numeric / 
                      NULLIF(COUNT(CASE WHEN is_delivered AND is_valid_delivery_date THEN 1 END), 0)::numeric) * 100, 4)
        FROM fact_order_delivery;
    """)[0][0]
    add_check("C18", "Late Delivery Rate (%)", ct["date_level_late_delivery_rate_pct"], safe_float(res))

    # 19. Deduplicated Reviewed Orders Count
    res = runner("SELECT COUNT(*) FROM fact_order_delivery WHERE has_review = TRUE;")[0][0]
    add_check("C19", "Deduplicated Reviewed Orders Count", ct["deduplicated_order_reviews_count"], safe_int(res))

    # 20. Overall Deduplicated Avg Review Score
    res = runner("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE has_review = TRUE;")[0][0]
    add_check("C20", "Avg Review Score (Deduplicated)", ct["avg_dedup_review_score"], safe_float(res))

    # 21. On-Time Delivered Avg Review Score
    res = runner("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_on_time = TRUE AND has_review = TRUE;")[0][0]
    add_check("C21", "On-Time Delivered Avg Review Score", ct["date_level_ontime_avg_review_score"], safe_float(res))

    # 22. Late Delivered Avg Review Score
    res = runner("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE;")[0][0]
    add_check("C22", "Late Delivered Avg Review Score", ct["date_level_late_avg_review_score"], safe_float(res))

    # 23. Review Created Before Delivery Count (Late Orders)
    res = runner("SELECT COUNT(*) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE AND review_created_before_delivery = TRUE;")[0][0]
    add_check("C23", "Late Orders Reviewed Before Delivery", h1["late_review_timing_split"]["reviewed_before_delivery"]["N"], safe_int(res))

    # 24. Review Created Before Delivery Score (Late Orders)
    res = runner("SELECT ROUND(AVG(review_score), 4) FROM fact_order_delivery WHERE is_late = TRUE AND has_review = TRUE AND review_created_before_delivery = TRUE;")[0][0]
    add_check("C24", "Late Pre-Delivery Avg Review Score", h1["late_review_timing_split"]["reviewed_before_delivery"]["avg_score"], safe_float(res))

    # 25. Clean Handling Time Mean (Days)
    res = runner("SELECT ROUND(AVG(handling_days), 4) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE AND handling_days >= 0;")[0][0]
    add_check("C25", "Clean Handling Time Mean (Days)", dur_clean["avg_handling_clean_days"], safe_float(res))

    # 26. Clean Transit Time Mean (Days, excluding both anomalies)
    res = runner("SELECT ROUND(AVG(transit_days), 4) FROM fact_order_delivery WHERE is_delivered = TRUE AND is_valid_delivery_date = TRUE AND transit_days >= 0 AND handling_days >= 0;")[0][0]
    add_check("C26", "Clean Transit Time Mean (Days)", dur_clean["transit_excluding_all_anomalies_days"], safe_float(res))

    # 27. Primary Key Uniqueness Checks
    res = runner("SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM fact_order_delivery;")[0][0]
    add_check("C27", "PK Uniqueness (fact_order_delivery)", 0, safe_int(res))

    res = runner("SELECT COUNT(*) - COUNT(DISTINCT (order_id, order_item_id)) FROM fact_order_items;")[0][0]
    add_check("C28", "PK Uniqueness (fact_order_items)", 0, safe_int(res))

    res = runner("SELECT COUNT(*) - COUNT(DISTINCT customer_unique_id) FROM dim_customer;")[0][0]
    add_check("C29", "PK Uniqueness (dim_customer)", 0, safe_int(res))

    # 28. Referential Integrity (Child to Parent Orphans)
    res = runner("""
        SELECT COUNT(*) 
        FROM fact_order_items i 
        LEFT JOIN fact_order_delivery d ON i.order_id = d.order_id 
        WHERE d.order_id IS NULL;
    """)[0][0]
    add_check("C30", "Orphan Items -> Delivery Fact", 0, safe_int(res))

    res = runner("""
        SELECT COUNT(*) 
        FROM fact_order_delivery d 
        LEFT JOIN dim_customer c ON d.customer_unique_id = c.customer_unique_id 
        WHERE c.customer_unique_id IS NULL;
    """)[0][0]
    add_check("C31", "Orphan Orders -> Customer Dim", 0, safe_int(res))

    # Display Results
    print("\n" + "=" * 105)
    print(f"{'ID':4} | {'Metric / Verification Check':40} | {'Expected (Pandas)':20} | {'Actual (SQL)':20} | {'Status':6}")
    print("=" * 105)
    
    passed_all = True
    for c in checks:
        print(f"{c['id']:4} | {c['metric']:40} | {str(c['expected']):20} | {str(c['actual']):20} | {c['status']:6}")
        if c["status"] == "FAIL":
            passed_all = False

    print("=" * 105)
    total_checks = len(checks)
    passed_count = sum(1 for c in checks if c["status"] == "PASS")
    failed_count = total_checks - passed_count
    print(f"Summary: {passed_count}/{total_checks} PASSED | {failed_count} FAILED")
    print("=" * 105 + "\n")

    return passed_all

def main():
    parser = argparse.ArgumentParser(description="Validate PostgreSQL Warehouse against Control Totals")
    parser.add_argument("--dbname", default=os.getenv("PG_DATABASE", "olist_db"))
    parser.add_argument("--user", default=os.getenv("PG_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("PG_PASSWORD", ""))
    parser.add_argument("--host", default=os.getenv("PG_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PG_PORT", "5432")))
    args = parser.parse_args()

    control_data = load_control_totals()
    print("Loaded canonical control totals successfully.")
    
    try:
        runner, mode = get_db_connection(args.dbname, args.user, args.password, args.host, args.port)
        print(f"Connected to database '{args.dbname}' using {mode}.")
    except Exception as e:
        print(f"ERROR: Could not establish connection to PostgreSQL: {e}")
        sys.exit(1)

    all_passed = run_validations(runner, control_data)
    if not all_passed:
        print("VALIDATION FAILED: One or more checks did not match control totals.")
        sys.exit(1)
    else:
        print("ALL VERIFICATION CHECKS PASSED PERFECTLY.")
        sys.exit(0)

if __name__ == "__main__":
    main()
