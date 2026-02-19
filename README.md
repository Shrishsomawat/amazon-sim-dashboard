# Amazon SIM Distribution Dashboard

A production-grade internal operations dashboard built with 
Python + Streamlit, deployed to automate SIM (workflow ticket) 
distribution across Amazon ROC team headcount.

**This tool is actively used by a real team at Amazon.**

---

## What Problem Does This Solve?

Before this dashboard, SIM tickets were manually assigned to 
team members — a slow, error-prone process that created 
uneven workload distribution and wasted analyst time daily.

This dashboard replaced that entirely.

---

## What It Does

- Auto-assigns unassigned SIMs to active headcount using a 
  load-balancing algorithm
- Detects and cleans up SIMs assigned to team members who 
  have left (leaver cleanup)
- Rebalances workload so no single person is overloaded 
  (max-min difference ≤ 1)
- Tracks every assignment action in an audit log with timestamps
- Visualizes current load per headcount with Plotly bar charts
- Exports updated assignment files as downloadable CSVs

---

## Impact

- Reduced manual SIM assignment effort by ~80%
- Improved operational data accuracy to ~99%
- Saved ~30% of daily analyst time previously spent on 
  manual reconciliation
- Used daily by the Amazon ROC transportation operations team

---

## Tech Stack

| Tool | Usage |
|------|-------|
| Python | Core logic and data processing |
| Streamlit | Dashboard UI and deployment |
| Pandas | Data manipulation and cleaning |
| Plotly | Interactive charts and visualizations |
| Excel/xlsm | Source data ingestion |

---

## How to Run Locally
```bash
git clone https://github.com/Shrishsomawat/amazon-sim-dashboard
cd amazon-sim-dashboard
pip install -r requirements.txt
streamlit run sim_dashboard_app.py
```

Upload your Excel file with three sheets:
- `SIM Lobby` — current SIM tickets with assignees
- `ActiveHC` — list of active headcount
- `DistributionLog` — audit trail of all actions

---

## Algorithm Logic

1. Load active headcount list from `ActiveHC` sheet
2. Identify and clean SIMs assigned to leavers
3. Assign unassigned SIMs to the least-loaded active member
4. Rebalance until max load − min load ≤ 1
5. Log every action with timestamp to `DistributionLog`

---

## Built By

Shrish Somawat — Data Engineer  
[LinkedIn](https://linkedin.com/in/YOUR_LINKEDIN_URL)  
[GitHub](https://github.com/Shrishsomawat)
