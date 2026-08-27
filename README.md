# RLS Ops Intelligence Dashboard (Interview Portfolio Project)

🚀 **Live Dashboard:** [https://harsh-rls-portfolio.streamlit.app](https://harsh-rls-portfolio.streamlit.app)
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

## 🤖 How I Used Claude (AI) in this Project

The job description explicitly calls for a **"genuine Claude Master"** who directs AI to do the heavy lifting while verifying the output. Here is exactly how I used Claude to build this project:

- **Synthetic Data Generation:** I used Claude to write `generate_data.py` to create a realistic, interconnected mock dataset so I could build and test the SQL logic without needing access to real company data.
- **SQL Edge-Case Review:** I prompted Claude to act as a code reviewer to catch edge cases in my retention and close-rate SQL queries (e.g., handling blank end dates and division-by-zero errors).
- **Streamlit Formatting:** I used Claude to quickly generate the frontend Streamlit layout and apply the RLS brand colors, allowing me to focus entirely on data accuracy and metric logic.

## What's inside

| Folder | Contents |
|---|---|
| `data/` | Synthetic data generator + generated CSVs (ATS, CRM, Bloom Growth, Monday.com stand-ins) |
| `database/` | SQLite loader + `rls_ops.db` |
| `sql/` | 20 SQL queries across 4 files: funnel/close rate, retention, escalations, weekly leadership dashboard |
| `dashboard/` | Streamlit app with RLS-inspired branding |
| `docs/` | Full documentation + interview prep guide |

All data is synthetic. See `docs/PROJECT_DOCUMENTATION.md` §9 for disclaimers.
