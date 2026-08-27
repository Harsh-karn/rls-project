# RLS Ops Intelligence Dashboard (Interview Portfolio Project)

A self-contained data analyst portfolio project built for the
**RemoteLegalStaff — AI-Powered Data Analyst** role. See
`docs/PROJECT_DOCUMENTATION.md` for full documentation, the data dictionary,
the JD-to-artifact mapping, and interview talking points.

## Quick start

```bash
pip install -r requirements.txt

# 1. (Optional — CSVs are already generated) rebuild synthetic data
cd data && python generate_data.py && cd ..

# 2. Build the SQLite warehouse
cd database && python build_db.py && cd ..

# 3. Run the dashboard
cd dashboard && streamlit run app.py
```

## What's inside

| Folder | Contents |
|---|---|
| `data/` | Synthetic data generator + generated CSVs (ATS, CRM, Bloom Growth, Monday.com stand-ins) |
| `database/` | SQLite loader + `rls_ops.db` |
| `sql/` | 20 SQL queries across 4 files: funnel/close rate, retention, escalations, weekly leadership dashboard |
| `dashboard/` | Streamlit app with RLS-inspired branding |
| `docs/` | Full documentation + interview prep guide |

All data is synthetic. See `docs/PROJECT_DOCUMENTATION.md` §9 for disclaimers.
