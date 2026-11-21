"""
Execution Runner for Business SQL Queries Suite (Q01 - Q12)
Project: Olist E-commerce Delivery Performance & Customer Satisfaction
Author: Independent Portfolio Project

Executes all 12 analytical SQL queries from sql/queries/, exports tabular results
to data/processed/query_results/, and generates documentation/business_queries_report.md.
"""

import os
import sys
import argparse
import subprocess
import pandas as pd

QUERIES_DIR = os.path.join(os.path.dirname(__file__), "..", "sql", "queries")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "query_results")
DOCS_FILE = os.path.join(os.path.dirname(__file__), "..", "documentation", "business_queries_report.md")

os.makedirs(OUT_DIR, exist_ok=True)

query_files = [
    ("Q01", "Executive KPI Summary", "q01_executive_summary.sql"),
    ("Q02", "Monthly Trend Analysis", "q02_monthly_trend_analysis.sql"),
    ("Q03", "H1: Late Delivery and Satisfaction", "q03_h1_late_delivery_satisfaction.sql"),
    ("Q04", "H1: Review Timing Split", "q04_h1_review_timing_split.sql"),
    ("Q05", "H1: Category Mix Control", "q05_h1_category_controlled_satisfaction.sql"),
    ("Q06", "H2: Regional Delivery Performance", "q06_h2_state_delivery_performance.sql"),
    ("Q07", "H2: State Mix-Adjusted Benchmarks", "q07_h2_state_mix_adjusted_benchmarks.sql"),
    ("Q08", "H2: Seller Fulfillment Cohorts", "q08_h2_seller_fulfillment_cohorts.sql"),
    ("Q09", "H3: Bottleneck Decomposition", "q09_h3_bottleneck_decomposition.sql"),
    ("Q10", "H3: Top Interstate Corridors", "q10_h3_top_interstate_corridors.sql"),
    ("Q11", "H4: Freight Burden Across Distance", "q11_h4_freight_burden_by_distance.sql"),
    ("Q12", "Customer Retention by Delivery Outcome", "q12_customer_retention_delivery_impact.sql")
]

def get_engine_or_runner(dbname, user, password, host, port):
    try:
        from sqlalchemy import create_engine
        conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        engine = create_engine(conn_str)
        # Test connection
        with engine.connect() as conn:
            conn.execute(pd.io.sql.text("SELECT 1;"))
        return engine, "sqlalchemy"
    except Exception as e:
        print(f"SQLAlchemy direct connection not available ({e}). Using psql runner...")
        return None, "psql_cli"

def run_query_psql(query_path, dbname, user, password, host, port):
    env = os.environ.copy()
    if password:
        env["PGPASSWORD"] = password
    cmd = [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", user,
        "-d", dbname,
        "--csv",
        "-f", query_path
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"psql execution error for {query_path}: {res.stderr.strip()}")
    
    import io
    df = pd.read_csv(io.StringIO(res.stdout))
    return df

def main():
    parser = argparse.ArgumentParser(description="Run Business SQL Queries Suite")
    parser.add_argument("--dbname", default=os.getenv("PG_DATABASE", "olist_db"))
    parser.add_argument("--user", default=os.getenv("PG_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("PG_PASSWORD", ""))
    parser.add_argument("--host", default=os.getenv("PG_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PG_PORT", "5432")))
    args = parser.parse_args()

    engine, mode = get_engine_or_runner(args.dbname, args.user, args.password, args.host, args.port)
    print(f"Connected to database '{args.dbname}' using {mode}.\n")

    report_sections = [
        "# Analytical Business SQL Queries Report",
        "## Project: Olist E-commerce Delivery Performance & Customer Satisfaction",
        "**Execution Mode:** PostgreSQL 16 Data Warehouse  ",
        "**Status:** Phase 4 Complete — All 12 Business Queries Verified  \n",
        "> **Methodological Disclosure:** All queries include explicit sample size counts ($N$) and governance tags (`<30` suppress, `30–99` exploratory, `100+` interpretable). In accordance with non-negotiable rules, all findings are phrased using associational language; no causal claims are made.\n",
        "---"
    ]

    for qid, qtitle, qfile in query_files:
        fpath = os.path.join(QUERIES_DIR, qfile)
        print(f"Executing [{qid}] {qtitle} ({qfile})...")
        
        if mode == "sqlalchemy":
            with open(fpath, "r", encoding="utf-8") as f:
                qsql = f.read()
            df = pd.read_sql_query(qsql, engine)
        else:
            df = run_query_psql(fpath, args.dbname, args.user, args.password, args.host, args.port)
        
        # Save CSV
        out_csv = os.path.join(OUT_DIR, f"{qid.lower()}_{qfile.replace('.sql', '.csv')}")
        df.to_csv(out_csv, index=False)
        print(f"  -> Returned {len(df)} rows. Saved to: {out_csv}")

        # Add to Markdown Report
        report_sections.append(f"\n### {qid}: {qtitle}")
        report_sections.append(f"**Source Query:** [`sql/queries/{qfile}`](../sql/queries/{qfile})  ")
        report_sections.append(f"**Rows Returned:** {len(df)}  \n")
        
        # Format preview table (up to 25 rows)
        preview_df = df.head(25)
        markdown_table = preview_df.to_markdown(index=False)
        report_sections.append(markdown_table)
        if len(df) > 25:
            report_sections.append(f"\n*Showing top 25 of {len(df)} rows. Full dataset saved in query results.*")
        report_sections.append("\n---")

    # Write compiled report
    with open(DOCS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_sections))

    print(f"\nSuccessfully generated full business queries report at:\n{DOCS_FILE}\n")

if __name__ == "__main__":
    main()
