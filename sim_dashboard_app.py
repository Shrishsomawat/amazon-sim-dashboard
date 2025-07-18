# sim_dashboard_app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Amazon internal theme simulation ---
AMAZON_BLUE = "#146EB4"
AMAZON_ORANGE = "#FF9900"

st.set_page_config(page_title="Amazon SIM Dashboard", layout="wide")
st.markdown(f"""
    <style>
        .main {{
            background-color: #ffffff;
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}
        .footer {{
            text-align: center;
            font-size: 14px;
            padding-top: 50px;
            color: gray;
        }}
        h1, h2, h3, h4, h5 {{
            color: {AMAZON_BLUE};
        }}
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("📊 Amazon SIM Distribution Dashboard")

# --- FILE UPLOAD ---
st.sidebar.header("📂 Upload Excel File")
excel_file = st.sidebar.file_uploader("Upload your Excel File", type=["xlsm", "xlsx"])

if excel_file:
    xls = pd.ExcelFile(excel_file)

    # Load Sheets
    df_sim = pd.read_excel(xls, sheet_name="SIM Lobby")
    df_hc = pd.read_excel(xls, sheet_name="ActiveHC")
    df_log = pd.read_excel(xls, sheet_name="DistributionLog")

    # Rename SIM URL column if needed
    if "SIM URL" not in df_sim.columns:
        for col in df_sim.columns:
            if "url" in col.lower():
                df_sim.rename(columns={col: "SIM URL"}, inplace=True)
                break

    if "Assignee" not in df_sim.columns:
        for col in df_sim.columns:
            if "assignee" in col.lower():
                df_sim.rename(columns={col: "Assignee"}, inplace=True)
                break

    if "Timestamp" not in df_log.columns:
        for col in df_log.columns:
            if "time" in col.lower() or "date" in col.lower():
                df_log.rename(columns={col: "Timestamp"}, inplace=True)
                break

    # --- SIM DISTRIBUTION FUNCTION ---
    def run_sim_distribution(df_sim, df_hc, df_log):
        import datetime
        current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        hc_list = df_hc[df_hc.columns[0]].dropna().unique().tolist()
        sim_rows = df_sim.copy()

        # Remove SIMs from leavers
        removed_rows = sim_rows[~sim_rows["Assignee"].isin(hc_list)]
        sim_rows.loc[~sim_rows["Assignee"].isin(hc_list), "Assignee"] = ""
        cleaned_count = removed_rows.shape[0]

        # Count assigned SIMs
        hc_load = sim_rows["Assignee"].value_counts().to_dict()

        # Fill missing assignees with lowest load
        for idx, row in sim_rows[sim_rows["Assignee"] == ""].iterrows():
            min_loaded = min(hc_list, key=lambda x: hc_load.get(x, 0))
            sim_rows.at[idx, "Assignee"] = min_loaded
            hc_load[min_loaded] = hc_load.get(min_loaded, 0) + 1
            df_log.loc[len(df_log)] = [current_time, "Newly Assigned", row["SIM URL"], "", min_loaded]

        # Rebalance if needed
        max_sim = max(hc_load.values())
        min_sim = min(hc_load.values())

        while max_sim - min_sim > 1:
            overloaded = max(hc_load, key=hc_load.get)
            underloaded = min(hc_load, key=hc_load.get)

            for idx, row in sim_rows.iterrows():
                if row["Assignee"] == overloaded:
                    sim_rows.at[idx, "Assignee"] = underloaded
                    hc_load[overloaded] -= 1
                    hc_load[underloaded] += 1
                    df_log.loc[len(df_log)] = [current_time, "Fair Rebalance", row["SIM URL"], overloaded, underloaded]
                    break

            max_sim = max(hc_load.values())
            min_sim = min(hc_load.values())

        return sim_rows, df_log, hc_load, cleaned_count

    # --- SMART SIM DISTRIBUTION BUTTON ---
    st.markdown("---")
    if st.button("🚀 Run Smart SIM Distribution"):
        with st.spinner("Running smart distribution logic..."):
            updated_sim, updated_log, load_dict, cleaned = run_sim_distribution(df_sim, df_hc, df_log)

        st.success("✅ SIM Distribution Done Successfully!")

        # Show updated load table
        load_df = pd.DataFrame.from_dict(load_dict, orient="index", columns=["SIM Count"]).reset_index()
        load_df.columns = ["Assignee", "SIM Count"]
        st.dataframe(load_df.sort_values("SIM Count", ascending=False), use_container_width=True)

        # Allow export
        st.download_button("⬇ Download Updated SIM Lobby", data=updated_sim.to_csv(index=False), file_name="Updated_SIM_Lobby.csv")
        st.download_button("⬇ Download Updated Distribution Log", data=updated_log.to_csv(index=False), file_name="Updated_DistributionLog.csv")

    # --- KPIs ---
    total_sims = df_sim["SIM URL"].count()
    active_hcs = df_hc[df_hc.columns[0]].nunique()
    today = pd.to_datetime(datetime.today().date())

    if "Timestamp" in df_log.columns:
        df_log["Timestamp"] = pd.to_datetime(df_log["Timestamp"], errors="coerce")
        sims_today = df_log[df_log["Timestamp"].dt.date == today.date()]
        assigned_today = sims_today[sims_today["Action"] == "Newly Assigned"].shape[0]
        rebalanced_today = sims_today[sims_today["Action"] == "Fair Rebalance"].shape[0]
        leaver_today = sims_today[sims_today["Action"] == "Leaver Cleanup"].shape[0]
    else:
        assigned_today = rebalanced_today = leaver_today = 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📦 Total SIMs", total_sims)
    col2.metric("👤 Active Headcounts", active_hcs)
    col3.metric("🆕 Assigned Today", assigned_today)
    col4.metric("🔁 Rebalanced Today", rebalanced_today)
    col5.metric("❌ Leaver Cleanup Today", leaver_today)

    # --- SIMs per Assignee ---
    with st.expander("📊 SIMs Assigned per Headcount"):
        sim_distribution = df_sim["Assignee"].value_counts().reset_index()
        sim_distribution.columns = ["Assignee", "SIM Count"]
        sim_distribution["Color"] = AMAZON_BLUE
        top3 = sim_distribution.nlargest(3, "SIM Count").index.tolist()
        sim_distribution.loc[top3, "Color"] = AMAZON_ORANGE

        fig_bar = px.bar(sim_distribution, x="Assignee", y="SIM Count", color="Color",
                         title="Current Load per Headcount",
                         color_discrete_map={AMAZON_BLUE: AMAZON_BLUE, AMAZON_ORANGE: AMAZON_ORANGE})
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- Action Type Pie Chart ---
    with st.expander("📈 SIM Assignment Type Breakdown"):
        if "Action" in df_log.columns:
            pie_data = df_log["Action"].value_counts().reset_index()
            pie_data.columns = ["Action", "Count"]
            fig_pie = px.pie(pie_data, values="Count", names="Action", title="Distribution of Actions",
                             color_discrete_sequence=[AMAZON_BLUE, AMAZON_ORANGE, "#cccccc"])
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- Recent Changes Table ---
    with st.expander("📋 Last 10 Actions Logged"):
        if "Timestamp" in df_log.columns:
            recent_log = df_log.sort_values("Timestamp", ascending=False).head(10)
            st.dataframe(recent_log, use_container_width=True)

    # --- Dropdown Filter by Assignee ---
    st.markdown("---")
    assignees = df_sim["Assignee"].dropna().unique().tolist()
    selected_assignee = st.selectbox("🔍 Filter SIMs by Assignee", ["All"] + assignees)

    if selected_assignee != "All":
        filtered_df_sim = df_sim[df_sim["Assignee"] == selected_assignee]
    else:
        filtered_df_sim = df_sim

    st.dataframe(filtered_df_sim.sort_values("SIM URL"), use_container_width=True)

    # --- Dropdown Filter by Action ---
    st.markdown("---")
    actions = df_log["Action"].dropna().unique().tolist()
    selected_action = st.selectbox("📂 Filter Distribution Log by Action", ["All"] + actions)

    if selected_action != "All":
        filtered_log = df_log[df_log["Action"] == selected_action]
    else:
        filtered_log = df_log

    st.dataframe(filtered_log.sort_values("Timestamp", ascending=False), use_container_width=True)

    # --- Footer ---
    st.markdown("""
        <div class='footer'>
            Developed by Shrish | Amazon Internal Project Dashboard
        </div>
    """, unsafe_allow_html=True)

else:
    st.info("👈 Upload your Excel file from the sidebar to begin.")
