"""
generate_data.py
-----------------
Builds a synthetic operational dataset that mirrors the four systems named in
the RemoteLegalStaff (RLS) Data Analyst job description:

    - ATS            -> candidate pipeline (sourcing through placement)
    - CRM            -> client accounts + active placements
    - Monday.com     -> recurring reporting / task tracking board
    - Bloom Growth    -> escalations & performance log (the EOS-style ops tool
                         many small companies use to track issues/rocks)

All data is fictional. Names, firms, and figures are generated with fixed
random seeds so the dataset is reproducible.

Run:  python generate_data.py
Output: five CSVs written next to this script.
"""

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

random.seed(42)
np.random.seed(42)
fake = Faker()
Faker.seed(42)

TODAY = date(2026, 8, 28)
WINDOW_START = TODAY - timedelta(days=545)  # ~18 months of history

REGIONS = ["Colombia", "Philippines", "South Africa", "Mexico", "Argentina", "Peru"]
REGION_WEIGHTS = [0.28, 0.30, 0.16, 0.12, 0.08, 0.06]

ROLES = [
    "Legal Assistant", "Paralegal", "Case Manager", "Intake Specialist",
    "Lawyer", "Executive Assistant", "Receptionist", "Marketing Assistant",
    "Bookkeeper", "Operations Manager",
]
ROLE_WEIGHTS = [0.24, 0.18, 0.14, 0.12, 0.05, 0.09, 0.06, 0.05, 0.04, 0.03]

SOURCE_CHANNELS = ["LinkedIn", "Referral", "Job Board", "Facebook Ads", "Recruiter Outreach", "University Partner"]

PRACTICE_AREAS = ["Personal Injury", "Immigration", "Family Law", "Estate Planning",
                   "Criminal Defense", "Bankruptcy", "Real Estate", "General Practice"]

FIRM_SIZE = ["Solo Practitioner", "2-10 Attorneys", "11-25 Attorneys", "26+ Attorneys"]
FIRM_SIZE_WEIGHTS = [0.30, 0.42, 0.20, 0.08]

US_STATES = ["California", "Texas", "Florida", "New York", "Illinois", "Georgia",
             "Arizona", "North Carolina", "Ohio", "Pennsylvania", "Washington", "Colorado"]

PLAN_TIERS = ["Standard", "Plus", "Enterprise"]

RECRUITERS = ["Camila R.", "Josh T.", "Priya N.", "Diego M.", "Grace L."]

STAGE_ORDER = ["Applied", "Screened", "Interviewed", "Offered", "Placed", "Rejected", "Withdrawn"]

ESCALATION_CATEGORIES = ["Performance", "Attendance", "Communication", "Billing Dispute", "Technical / Access"]
ESCALATION_SEVERITY = ["Low", "Medium", "High"]

END_REASONS = ["Client Budget Cut", "Client Ended Engagement", "Staff Resigned",
               "Performance - Replaced", "Role No Longer Needed", "Staff Promoted Internally"]

REPORT_NAMES = [
    "Weekly Leadership Dashboard", "Close Rate Tracker", "Retention Cohort Report",
    "Escalation Log Review", "Recruiter Funnel Snapshot", "Monthly Client Health Report",
]


def business_days_between(start: date, end: date) -> int:
    days = np.busday_count(start.isoformat(), end.isoformat())
    return int(days)


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    if delta <= 0:
        return start
    return start + timedelta(days=random.randint(0, delta))


# ---------------------------------------------------------------------------
# 1. CLIENTS  (CRM — the U.S. law firms RLS staffs)
# ---------------------------------------------------------------------------
def generate_clients(n=85):
    rows = []
    for i in range(1, n + 1):
        signed = random_date(WINDOW_START, TODAY - timedelta(days=14))
        rows.append({
            "client_id": f"CL-{i:04d}",
            "firm_name": f"{fake.last_name()} {random.choice(['Law Group','& Associates','Legal','Law Firm','Partners'])}",
            "firm_size": np.random.choice(FIRM_SIZE, p=FIRM_SIZE_WEIGHTS),
            "practice_area": random.choice(PRACTICE_AREAS),
            "state": random.choice(US_STATES),
            "plan_tier": np.random.choice(PLAN_TIERS, p=[0.55, 0.32, 0.13]),
            "signed_date": signed.isoformat(),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. CANDIDATES  (ATS — sourcing-to-placement funnel)
# ---------------------------------------------------------------------------
def generate_candidates(n=1450):
    rows = []
    for i in range(1, n + 1):
        applied = random_date(WINDOW_START, TODAY - timedelta(days=1))
        region = np.random.choice(REGIONS, p=REGION_WEIGHTS)
        role = np.random.choice(ROLES, p=ROLE_WEIGHTS)

        # Funnel drop-off probabilities (realistic staffing-agency shape)
        r = random.random()
        if r < 0.22:
            stage, stage_offset = "Applied", 0
        elif r < 0.42:
            stage, stage_offset = "Rejected", random.randint(1, 4)
        elif r < 0.55:
            stage, stage_offset = "Screened", random.randint(2, 5)
        elif r < 0.63:
            stage, stage_offset = "Rejected", random.randint(4, 9)
        elif r < 0.74:
            stage, stage_offset = "Interviewed", random.randint(5, 10)
        elif r < 0.80:
            stage, stage_offset = "Withdrawn", random.randint(6, 14)
        elif r < 0.88:
            stage, stage_offset = "Offered", random.randint(9, 15)
        elif r < 0.93:
            stage, stage_offset = "Rejected", random.randint(10, 16)
        else:
            stage, stage_offset = "Placed", random.randint(12, 22)

        stage_date = min(applied + timedelta(days=stage_offset), TODAY)

        rows.append({
            "candidate_id": f"CND-{i:05d}",
            "candidate_name": fake.name(),
            "region": region,
            "role_applied": role,
            "source_channel": np.random.choice(
                SOURCE_CHANNELS, p=[0.30, 0.18, 0.22, 0.14, 0.11, 0.05]
            ),
            "recruiter": random.choice(RECRUITERS),
            "application_date": applied.isoformat(),
            "current_stage": stage,
            "stage_date": stage_date.isoformat(),
            "years_experience": max(0, int(np.random.normal(4, 2.2))),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. PLACEMENTS  (CRM — candidate x client engagement)
# ---------------------------------------------------------------------------
def generate_placements(candidates: pd.DataFrame, clients: pd.DataFrame):
    placed = candidates[candidates["current_stage"] == "Placed"].copy()
    rows = []
    client_ids = clients["client_id"].tolist()
    client_signed = dict(zip(clients["client_id"], pd.to_datetime(clients["signed_date"])))

    for idx, cand in enumerate(placed.itertuples(), start=1):
        client_id = random.choice(client_ids)
        start_date = pd.to_datetime(cand.stage_date)
        # Placement can't start before the client actually signed
        min_start = client_signed[client_id]
        if start_date < min_start:
            start_date = min_start + timedelta(days=random.randint(1, 10))
        if start_date.date() > TODAY:
            continue

        hourly_rate = round(random.uniform(11.5, 22.0), 2)

        # Attrition model: ~35% of placements have already ended
        ended = random.random() < 0.35
        end_date = None
        end_reason = None
        status = "Active"
        tenure_cap_days = (TODAY - start_date.date()).days
        if ended and tenure_cap_days > 30:
            tenure = random.randint(30, tenure_cap_days)
            end_date = start_date.date() + timedelta(days=tenure)
            end_reason = random.choices(
                END_REASONS,
                weights=[0.22, 0.18, 0.27, 0.15, 0.10, 0.08],
            )[0]
            status = "Ended"

        rows.append({
            "placement_id": f"PL-{idx:05d}",
            "candidate_id": cand.candidate_id,
            "client_id": client_id,
            "role": cand.role_applied,
            "region": cand.region,
            "hourly_rate": hourly_rate,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.isoformat() if end_date else "",
            "status": status,
            "end_reason": end_reason if end_reason else "",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. ESCALATIONS  (Bloom Growth style issue log tied to a placement)
# ---------------------------------------------------------------------------
def generate_escalations(placements: pd.DataFrame, rate=0.30):
    rows = []
    esc_id = 1
    for p in placements.itertuples():
        start = pd.to_datetime(p.start_date).date()
        end = pd.to_datetime(p.end_date).date() if p.end_date else TODAY
        span = (end - start).days
        if span < 10:
            continue
        # Roughly one escalation raised per ~130 days a placement is active,
        # so longer / rockier engagements naturally accumulate more.
        lam = max(span, 0) / 130.0
        n_escalations = np.random.poisson(lam)
        for _ in range(n_escalations):
            raised = random_date(start + timedelta(days=7), end)
            severity = np.random.choice(ESCALATION_SEVERITY, p=[0.5, 0.35, 0.15])
            resolve_days = {"Low": (1, 5), "Medium": (3, 10), "High": (5, 21)}[severity]
            resolved = random.random() < 0.86
            resolution_date = ""
            if resolved:
                rd = raised + timedelta(days=random.randint(*resolve_days))
                if rd <= TODAY:
                    resolution_date = rd.isoformat()
                else:
                    resolved = False
            rows.append({
                "escalation_id": f"ESC-{esc_id:05d}",
                "placement_id": p.placement_id,
                "client_id": p.client_id,
                "category": np.random.choice(
                    ESCALATION_CATEGORIES, p=[0.32, 0.22, 0.24, 0.14, 0.08]
                ),
                "severity": severity,
                "date_raised": raised.isoformat(),
                "resolved": resolved,
                "resolution_date": resolution_date,
            })
            esc_id += 1
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. MONDAY.COM REPORTING BOARD  (recurring reporting cadence / doc hygiene)
# ---------------------------------------------------------------------------
def generate_reporting_tasks(weeks=52):
    rows = []
    task_id = 1
    for w in range(weeks, 0, -1):
        due = TODAY - timedelta(weeks=w)
        for report in REPORT_NAMES:
            on_time = random.random() < 0.82
            completed_offset = random.randint(-1, 1) if on_time else random.randint(2, 6)
            completed = due + timedelta(days=completed_offset)
            status = "Completed" if completed <= TODAY else "Overdue"
            rows.append({
                "task_id": f"TSK-{task_id:05d}",
                "report_name": report,
                "owner": "Data Analyst" if report != "Monthly Client Health Report" else "Ops Lead",
                "due_date": due.isoformat(),
                "completed_date": completed.isoformat() if status == "Completed" else "",
                "status": status,
                "on_time": on_time and status == "Completed",
            })
            task_id += 1
    return pd.DataFrame(rows)


def main():
    clients = generate_clients()
    candidates = generate_candidates()
    placements = generate_placements(candidates, clients)
    escalations = generate_escalations(placements)
    reporting_tasks = generate_reporting_tasks()

    clients.to_csv("clients_crm.csv", index=False)
    candidates.to_csv("candidates_ats.csv", index=False)
    placements.to_csv("placements_crm.csv", index=False)
    escalations.to_csv("escalations_bloomgrowth.csv", index=False)
    reporting_tasks.to_csv("reporting_tasks_monday.csv", index=False)

    print("Generated synthetic dataset:")
    print(f"  clients_crm.csv               -> {len(clients)} rows")
    print(f"  candidates_ats.csv            -> {len(candidates)} rows")
    print(f"  placements_crm.csv            -> {len(placements)} rows")
    print(f"  escalations_bloomgrowth.csv   -> {len(escalations)} rows")
    print(f"  reporting_tasks_monday.csv    -> {len(reporting_tasks)} rows")


if __name__ == "__main__":
    main()
