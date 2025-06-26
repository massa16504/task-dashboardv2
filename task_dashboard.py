import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Weekly Task Dashboard", layout="wide")
st.title("📊 CDI Weekly Task Dashboard")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Harsha", header=1)

        # Rename columns for convenience
        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns={
            'task': 'task',
            'target date': 'target_date',
            'status': 'status',
            'action with': 'owner'
        }, inplace=True)

        df['target_date'] = pd.to_datetime(df['target_date'], errors='coerce')
        df['status'] = df['status'].str.strip().str.title()
        df['owner'] = df['owner'].fillna("Unassigned")

        # Sidebar filters
        with st.sidebar:
            st.header("🔍 Filters")
            owners = df['owner'].dropna().unique().tolist()
            selected_owners = st.multiselect("Filter by Owner", owners, default=owners)
            statuses = df['status'].dropna().unique().tolist()
            selected_statuses = st.multiselect("Filter by Status", statuses, default=statuses)

        # Filtered data
        filtered_df = df[
            (df['owner'].isin(selected_owners)) &
            (df['status'].isin(selected_statuses))
        ]

        # KPIs
        total = len(filtered_df)
        completed = len(filtered_df[filtered_df['status'] == 'Completed'])
        in_progress = len(filtered_df[filtered_df['status'] == 'In Progress'])
        not_started = len(filtered_df[filtered_df['status'] == 'Not Started'])
        overdue = len(filtered_df[(filtered_df['status'] != 'Completed') & (filtered_df['target_date'] < datetime.today())])

        st.subheader("📈 Weekly Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total Tasks", total)
        col2.metric("✅ Completed", completed)
        col3.metric("🚧 In Progress", in_progress)
        col4.metric("⏳ Not Started", not_started)
        col5.metric("⚠️ Overdue", overdue)

        st.markdown("---")
        st.subheader("📌 Task Status Breakdown")
        pie = px.pie(filtered_df, names="status", title="Status Distribution", hole=0.45)
        st.plotly_chart(pie, use_container_width=True)

        st.subheader("📆 Task Timeline")
        filtered_df['task_display'] = filtered_df['task'].astype(str).str[:40]
        gantt = px.timeline(
            filtered_df.dropna(subset=['target_date']),
            x_start="target_date",
            x_end="target_date",
            y="task_display",
            color="status",
            hover_name="owner",
            title="Timeline by Target Date"
        )
        gantt.update_yaxes(autorange="reversed")
        st.plotly_chart(gantt, use_container_width=True)

        st.markdown("---")
        st.subheader("📄 Full Task Table")
        st.dataframe(filtered_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📁 Upload your Excel file with a 'Harsha' sheet to begin.")
