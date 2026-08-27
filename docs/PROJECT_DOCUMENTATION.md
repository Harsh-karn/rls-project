# RLS Ops Intelligence Dashboard — Project Documentation

**Built for:** RemoteLegalStaff (RLS) — "AI-Powered Data Analyst" role application
**Author:** Harsh
**Status:** Portfolio / take-home-style project, built proactively ahead of the interview

---

## 1. Why this project exists

The job description asks for someone who can pull and structure data from
operational systems (ATS, CRM, Monday.com, Bloom Growth), turn it into
recurring metrics (close rate, retention, escalations), maintain clean
dashboards, and document everything so the reporting function doesn't depend
on one person's memory. Rather than describe that skill set in a resume
bullet, this project **is** that skill set, built end-to-end on realistic
synthetic data:

1. **Synthetic data generation** standing in for the four named systems
2. **A SQLite warehouse** consolidating them (`rls_ops.db`)
3. **20 SQL queries** across 4 files, each mapped to a specific line in the
   job description
4. **A Streamlit dashboard** ("Weekly Leadership Dashboard" analog) styled
   after RLS's public brand identity
5. **This documentation** — the "living knowledge base" the JD explicitly
   asks the hire to build

Every design decision below is written down for the same reason the JD wants
documentation: so someone else (or interview-you, three weeks from now) can
pick this up without re-deriving it.

---

## 2. Repository structure

```
rls-project/
├── data/
│   ├── generate_data.py            # synthetic data generator (seeded, reproducible)
│   ├── clients_crm.csv
│   ├── candidates_ats.csv
│   ├── placements_crm.csv
│   ├── escalations_bloomgrowth.csv
│   └── reporting_tasks_monday.csv
├── database/
│   ├── build_db.py                 # loads CSVs → rls_ops.db
│   └── rls_ops.db
├── sql/
│   ├── 01_funnel_and_close_rate.sql
│   ├── 02_retention.sql
│   ├── 03_escalations.sql
│   └── 04_weekly_leadership_dashboard.sql
├── dashboard/
│   ├── app.py                      # Streamlit app
│   └── .streamlit/config.toml      # brand theme
└── docs/
    └── PROJECT_DOCUMENTATION.md    # this file
```

### How to run it

```bash
cd data && python generate_data.py        # regenerate synthetic CSVs (optional — already generated)
cd ../database && python build_db.py      # rebuild rls_ops.db from the CSVs
cd ../dashboard && streamlit run app.py   # launch the dashboard at localhost:8501
```

---

## 3. Data dictionary

All data below is **entirely synthetic** — fictional names, firms, and
figures generated with fixed random seeds (`random.seed(42)`) so results are
reproducible. It is *shaped* like what RLS's real systems plausibly track
(based only on what the job description states), not derived from any real
RLS data.

### `clients` (stands in for CRM client accounts)
| Column | Description |
|---|---|
| `client_id` | Unique client identifier |
| `firm_name` | Fictional law firm name |
| `firm_size` | Solo / 2–10 / 11–25 / 26+ attorneys |
| `practice_area` | e.g. Personal Injury, Immigration, Family Law |
| `state` | U.S. state |
| `plan_tier` | Standard / Plus / Enterprise |
| `signed_date` | Date the firm signed with RLS |

### `candidates` (stands in for the ATS)
| Column | Description |
|---|---|
| `candidate_id` | Unique candidate identifier |
| `candidate_name` | Fictional name |
| `region` | Sourcing region (Colombia, Philippines, South Africa, Mexico, Argentina, Peru) |
| `role_applied` | Role applied for (10 roles named in the JD) |
| `source_channel` | LinkedIn, Referral, Job Board, Facebook Ads, Recruiter Outreach, University Partner |
| `recruiter` | Owning recruiter |
| `application_date` | Date applied |
| `current_stage` | Applied → Screened → Interviewed → Offered → Placed, or Rejected / Withdrawn |
| `stage_date` | Date the candidate entered `current_stage` |
| `years_experience` | Simulated years of relevant experience |

### `placements` (stands in for CRM engagements)
| Column | Description |
|---|---|
| `placement_id` | Unique placement identifier |
| `candidate_id` | FK → candidates |
| `client_id` | FK → clients |
| `role`, `region` | Carried over from the candidate |
| `hourly_rate` | Simulated billing rate |
| `start_date` | Placement start |
| `end_date` | Placement end (blank if still active) |
| `status` | Active / Ended |
| `end_reason` | Why an ended placement ended (client- vs. staff-side) |

### `escalations` (stands in for a Bloom Growth-style issue log)
| Column | Description |
|---|---|
| `escalation_id` | Unique identifier |
| `placement_id`, `client_id` | FKs |
| `category` | Performance, Attendance, Communication, Billing Dispute, Technical/Access |
| `severity` | Low / Medium / High |
| `date_raised` | When flagged |
| `resolved` | Boolean |
| `resolution_date` | When closed (blank if unresolved) |

### `reporting_tasks` (stands in for a Monday.com reporting board)
| Column | Description |
|---|---|
| `task_id` | Unique identifier |
| `report_name` | One of 6 recurring reports (incl. "Weekly Leadership Dashboard") |
| `owner` | Data Analyst or Ops Lead |
| `due_date`, `completed_date` | Cadence tracking |
| `status` | Completed / Overdue |
| `on_time` | Boolean |

### Known data quirks (documented deliberately — this is exactly what the JD asks for)
- `close_rate` is inferred from `current_stage`, not from a `reached_offer_stage`
  flag. In a real ATS you'd want an explicit stage-history table so a
  candidate later rejected *after* being offered is still counted as having
  reached the offer stage. This project's SQL notes that assumption inline.
- `placements.end_reason` is only populated for `status = 'Ended'` rows by
  design — a blank `end_reason` on an ended placement would be a real
  reporting bug and is one of the data-quality checks in
  `sql/04_weekly_leadership_dashboard.sql`.
- Regions/currencies are simplified (single `hourly_rate` field, no
  currency conversion) since the JD doesn't specify a finance system in
  scope for this role.

---

## 4. Metric definitions (the numbers leadership sees)

| Metric | Formula | Why this definition |
|---|---|---|
| **Close rate** | `Placed ÷ (Offered + Placed)` | Measures offer-stage conversion, which is what a staffing team can actually influence — an "Applied ÷ Placed" rate would conflate sourcing volume with closing skill. |
| **Retention rate** | `Active placements ÷ All placements ever made` | A point-in-time health check leadership can track week over week. |
| **Retention cohort %** | Of placements *started* in month X, % still active today | Shows whether retention is improving or worsening over time, not just a single snapshot. |
| **Escalation rate** | `Total escalations ÷ Total placements` | Normalizes issue volume against book-of-business size so growth doesn't look like a quality problem. |
| **% resolved / avg days to resolve** | Grouped by severity | The SLA-style number leadership asks for first; High severity resolving *slower* than Medium is a flagged process issue, not just a number. |
| **% reports on time** | `On-time completions ÷ total scheduled` per recurring report | Directly measures the JD's own success criterion: "dashboards run clean... at any weekly check." |

---

## 5. SQL files — what each one does and why

- **`01_funnel_and_close_rate.sql`** — stage-by-stage funnel, close rate
  overall / by role / by sourcing channel / by recruiter. Answers "where are
  we losing candidates, and which channels and recruiters are converting."
- **`02_retention.sql`** — headline retention rate, tenure-band breakdown of
  churned placements, end-reason breakdown (client- vs. staff-driven churn),
  monthly cohort retention curve, retention by role × region.
- **`03_escalations.sql`** — escalation rate, category × severity breakdown,
  resolution SLA by severity, a live "open escalations" worklist, and a
  "which clients escalate the most" diagnostic (client-health signal, not
  just a staff-performance one).
- **`04_weekly_leadership_dashboard.sql`** — the single-row KPI summary that
  would headline a Monday leadership update, a **data-quality check block**
  (blanks, orphaned end dates, duplicate IDs, resolved-but-undated
  escalations), reporting-cadence hygiene, and a 12-week trend query for the
  applicants-vs-placements line chart.

---

## 6. Dashboard walkthrough

The Streamlit app (`dashboard/app.py`) mirrors the "Weekly Leadership
Dashboard" the JD names directly.

- **KPI header row** — retention rate, close rate, open escalations, active
  clients, 30-day new applicants. This is the row a leader reads in 5 seconds.
- **Funnel & Close Rate tab** — funnel chart, close rate by role, sourcing
  channel performance (bubble chart flags high-volume/low-conversion
  channels worth a budget conversation).
- **Retention tab** — monthly cohort chart (bars = volume, line = % still
  active), churn-reason donut, retention heatmap by role × region.
- **Escalations tab** — category/severity stacked bars, resolution SLA
  table, live "needs attention" worklist joined to client names.
- **Reporting Hygiene tab** — this is the tab that most directly answers the
  role's actual mandate: a chart of on-time delivery by recurring report,
  plus an automated data-quality check table (the kind of thing you'd run
  *before* every refresh, not after someone notices a blank cell).

### Brand styling — an honest note
RLS's public site uses a minimalist black-and-white wordmark (a black logo
on light backgrounds, a white version on a dark footer), paired with warm,
gold-toned photography. I wasn't able to pull an official style guide or
exact hex codes through automated tools, so the dashboard uses a
closely-matched professional palette — near-black (`#111111`), a warm gold
accent (`#C9A54B`), and a soft off-white background (`#F5F3EE`) — built to
feel consistent with that identity rather than copied from a design system.
**If asked in the interview:** be upfront that this is an interpretation of
the public brand, not an official asset, and that you'd swap in exact hex
values in five minutes given brand guidelines — the CSS variables at the top
of `app.py` are isolated for exactly that.

---

## 7. Job description → project artifact map

Use this table directly in the interview — it's the fastest way to show
you read the JD closely.

| JD line | Where it's addressed |
|---|---|
| "Pull and structure data ... for recurring metrics: close rate, retention, escalations" | `sql/01`, `sql/02`, `sql/03` |
| "Maintain dashboards ... catching blanks, duplicates, and inconsistencies proactively" | `sql/04` data-quality block + dashboard "Reporting Hygiene" tab |
| "Document every recurring report and dashboard as you learn it" | This file, Section 4 (metric definitions) and Section 3 (data dictionary + known quirks) |
| "Use Claude to build lightweight automations for repetitive reporting tasks" | `generate_data.py` / `build_db.py` pipeline — a one-command refresh, and this whole project was built with Claude as the "do the heavy lifting" tool the JD describes, with me verifying every query's output |
| "Support the Weekly Leadership Dashboard" | The Streamlit dashboard itself |
| "Flag data gaps and quality issues directly rather than quietly working around them" | The known-quirks note in Section 3, and the data-quality query surfacing issues rather than silently fixing them |

---

## 8. Interview prep

### How to describe this project in 30 seconds
"I built an ops-intelligence project modeled directly on this JD — synthetic
ATS, CRM, Monday.com, and Bloom Growth data loaded into a small warehouse,
SQL queries for close rate, retention, and escalations, and a Streamlit
dashboard styled after RLS's brand. I used Claude to do the first-pass data
generation and SQL drafting, and I verified every number — which is exactly
the 'direct AI tools, verify the output' workflow the role describes."

### Likely questions and how to answer them

**"Walk me through how you calculated close rate."**
→ Explain the `Offered + Placed` denominator choice and *why* (isolates the
close, not the sourcing). Mention the known limitation: using
`current_stage` instead of a stage-history flag, and how you'd fix it with
real ATS access.

**"How would you catch a bad number before it reaches leadership?"**
→ Point to the `sql/04` data-quality block — walk through 2-3 of the checks
(orphaned end dates, resolved-but-undated escalations) and explain these run
*before* the dashboard refresh, not as an afterthought.

**"What would you do differently with real data?"**
→ Be candid: real ATS/CRM/Monday.com data would need actual API
integrations (this project used static CSVs as a stand-in), stage-history
tracking instead of a single current-stage field, and probably a proper
warehouse (BigQuery/Postgres) rather than a single SQLite file once volume
grows. Naming these limitations unprompted signals seniority.

**"How did you use Claude in this project?"**
→ Answer honestly: Claude drafted the synthetic data generator, SQL, and
dashboard code; you defined the metric logic, reviewed every query's output
against the JD's stated metrics, and made the judgment calls about
denominators and edge cases. That's the "direct AI tools ... verified
output" pattern the JD explicitly wants, not "let AI do it and hope."

**"What's a data gap you'd flag in your first 30 days on this role?"**
→ Use a real one from this project as a template: "close rate needs a
stage-history table, not just a current-stage snapshot" — then say you'd
raise that as a finding rather than quietly working around it, echoing the
JD's own language.

### What to have open during the interview
- The dashboard running locally (`streamlit run app.py`)
- `sql/04_weekly_leadership_dashboard.sql` open — it's the file most directly
  tied to the role's actual title
- This documentation, to answer "how did you approach this" without
  fumbling for details

---

## 9. Limitations & honest disclaimers (say these unprompted if asked "is this real RLS data")

- All data is synthetic and randomly generated; no real RLS records, client
  names, or figures were used or seen.
- The brand palette is an inferred approximation of RLS's public site, not
  an official style guide.
- This project was built as interview preparation, not as a claim of
  insider knowledge of RLS's actual systems or numbers.
