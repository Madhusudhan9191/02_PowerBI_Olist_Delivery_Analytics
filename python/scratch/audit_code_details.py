import os
import re

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

print("=== CHECKING PYTHON FILES FOR PATHS AND CONFIG ===")
for pf in ["01_data_profiling.py", "02_validate_warehouse.py", "03_run_business_queries.py", "04_export_powerbi_csvs.py"]:
    fpath = os.path.join(base_dir, "python", pf)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"\n--- {pf} ---")
        # Check connection strings
        conn_matches = re.findall(r'(?:postgresql|psycopg2|create_engine|host|port|dbname|user|password).*', content, re.IGNORECASE)
        for cm in conn_matches[:5]:
            print(f"  Conn: {cm.strip()}")
        # Check file paths
        path_matches = re.findall(r'(?:os\.path|read_csv|to_csv|open).*', content)
        for pm in path_matches[:5]:
            print(f"  Path: {pm.strip()}")

print("\n=== CHECKING run_all_sql.ps1 ===")
with open(os.path.join(base_dir, "run_all_sql.ps1"), "r", encoding="utf-8") as f:
    ps1 = f.read()
    print(ps1[:500])

print("\n=== CHECKING SQL QUERY SCHEMAS ===")
for qf in os.listdir(os.path.join(base_dir, "sql", "queries")):
    if qf.endswith(".sql"):
        qp = os.path.join(base_dir, "sql", "queries", qf)
        with open(qp, "r", encoding="utf-8") as f:
            qtext = f.read()
            # check what tables are queried
            from_matches = re.findall(r'\bFROM\s+([a-zA-Z0-9_\.]+)', qtext, re.IGNORECASE)
            join_matches = re.findall(r'\bJOIN\s+([a-zA-Z0-9_\.]+)', qtext, re.IGNORECASE)
            tables = set(from_matches + join_matches)
            # print if raw or derived
            # print(f"{qf}: {tables}")
