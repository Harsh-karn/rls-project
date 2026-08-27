"""
build_db.py
------------
Loads the synthetic CSVs from /data into a single SQLite database
(rls_ops.db) so the SQL analysis scripts and the Streamlit dashboard
both read from one source of truth, the way a real Ops Intelligence
function would consolidate ATS + CRM + Monday.com + Bloom Growth data.

Run:  python build_db.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "database" / "rls_ops.db"

TABLES = {
    "clients": "clients_crm.csv",
    "candidates": "candidates_ats.csv",
    "placements": "placements_crm.csv",
    "escalations": "escalations_bloomgrowth.csv",
    "reporting_tasks": "reporting_tasks_monday.csv",
}


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    try:
        for table_name, csv_name in TABLES.items():
            df = pd.read_csv(DATA_DIR / csv_name)
            df.to_sql(table_name, conn, index=False, if_exists="replace")
            print(f"Loaded {csv_name:32s} -> table `{table_name}` ({len(df)} rows)")

        # Helpful indexes for the join-heavy queries in /sql
        conn.execute("CREATE INDEX idx_placements_client ON placements(client_id)")
        conn.execute("CREATE INDEX idx_placements_candidate ON placements(candidate_id)")
        conn.execute("CREATE INDEX idx_escalations_placement ON escalations(placement_id)")
        conn.commit()
        print(f"\nDatabase written to: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
