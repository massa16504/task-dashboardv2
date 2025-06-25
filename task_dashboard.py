import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Load sheet and auto-detect real header
        preview_df = pd.read_excel(uploaded_file, sheet_name="Harsha", header=None)
        header_row = None

        for i, row in preview_df.iterrows():
            lowercase_row = row.astype(str).str.lower().str.strip()
            if "status" in lowercase_row.values and "task" in lowercase_row.values:
                header_row = i
                break

        if header_row is None:
            st.error("❌ Could not find valid column headers (e.g. 'Status', 'Task'). Please check your file.")
        else:
            df = pd.read_excel(uploaded_file, sheet_name="Harsha", header=header_row)
            df.columns = df.columns.str.strip().str.lower().str.replace("\n", " ")

            required_cols = ['status', 'target date', 'task']
            if not all(col in df.columns for col in required_cols):
                st.error(f"❌ Missing one or more required columns: {required_cols}")
            else:
                # Standardize data
                df['target date'] = pd.to_datetime(df['target date'], errors='coerce')
                df['status'] = df['status'].str.strip().str.title()

                # Optional filters
                with st.sidebar:
                    st.header("🔍 Filters")
                    owner_col = st.selectbox("Owner column", options=df.columns, index=df.columns.get_loc("owner") if "owner" in df.columns else 0)
                    unique_owners = df[owner_col].dropna().unique().tolist()
                    selected_owners = st.multiselect("Filter by Owner", unique_owners, default=unique_owners)

                    status_filter = st.multiselect("Filter by Status", df['status'].unique(), default=df['status'].unique())

                # Apply filters
                filtered_df = df[
                    (df[owner_col].isin(selected_owners)) &
                    (df['status'].isin(status_filter))
                ]

                # KPI metrics
                total = len(filtered_df)
                completed = len(filtered_df[filtered_df['status'] == 'Completed'])
                in_progress = len(filtered_df[filtered_df['status'] == 'In Progress'])
                not_started = len(filtered_df[filtered_df['status'] == 'Not Started'])
                overdue = len(filtered_df[(filtered_df['status'] != 'Completed') & (filtered_df['target date'] < datetime.today())])

                st.subheader("📈 Weekly Summary Metrics")
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("📋 Total", total)
                col2.metric("✅ Completed", completed)
                col3.metric("🚧 In Progress", in_progress)
                col4.metric("⏳ Not Started", not_started)
                col5.metric("⚠️ Overdue", overdue)

                st.markdown("---")
                st.subheader("📌 Task Status Breakdown")
                chart = px.pie(filtered_df, names="status", title="Task Distribution", hole=0.4)
                st.plotly_chart(chart, use_container_width=True)

                if "target date" in filtered_df.columns and "task" in filtered_df.columns:
                    st.subheader("📆 Timeline View (Gantt-style)")
                    filtered_df['task_display'] = filtered_df['task'].astype(str).str[:30]
                    timeline = filtered_df.dropna(subset=['target date'])
                    timeline_chart = px.timeline(
                        timeline,
                        x_start="target date",
                        x_end="target date",
                        y="task_display",
                        color="status",
                        title="Task Due Dates Timeline",
                    )
                    timeline_chart.update_yaxes(autorange="reversed")
                    st.plotly_chart(timeline_chart, use_container_width=True)

                st.markdown("---")
                st.subheader("📄 Task Table")
                st.dataframe(filtered_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("📁 Upload an Excel file with a 'Harsha' sheet to get started.")
