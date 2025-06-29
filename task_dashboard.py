import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Weekly Task Dashboard", layout="wide")
st.title("📊 CDI Weekly Task Dashboard — Nutanix Launch")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Harsha", header=1)

        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns={
            'nutanix': 'vendor',
            'task': 'task',
            'target date': 'target_date',
            'status': 'status',
            'action with': 'owner'
        }, inplace=True)

        df['target_date'] = pd.to_datetime(df['target_date'], errors='coerce')
        df['status'] = df['status'].str.strip().str.title()
        df['owner'] = df['owner'].fillna("Unassigned")

        with st.sidebar:
            st.header("🔍 Filters")
            vendor_options = df['vendor'].dropna().unique().tolist()
            selected_vendors = st.multiselect("Filter by Vendor", vendor_options, default=vendor_options)

            owner_options = df['owner'].dropna().unique().tolist()
            selected_owners = st.multiselect("Filter by Owner", owner_options, default=owner_options)

            status_options = df['status'].dropna().unique().tolist()
            selected_statuses = st.multiselect("Filter by Status", status_options, default=status_options)

        filtered_df = df[
            (df['vendor'].isin(selected_vendors)) &
            (df['owner'].isin(selected_owners)) &
            (df['status'].isin(selected_statuses))
        ]

        total = len(filtered_df)
        completed = len(filtered_df[filtered_df['status'] == 'Completed'])
        in_progress = len(filtered_df[filtered_df['status'] == 'In Progress'])
        not_started = len(filtered_df[filtered_df['status'] == 'Not Started'])
        overdue_df = filtered_df[(filtered_df['status'] != 'Completed') & (filtered_df['target_date'] < datetime.today())]
        overdue = len(overdue_df)

        st.subheader("📈 Weekly Summary")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📋 Total Tasks", total)
        col2.metric("✅ Completed", completed)
        col3.metric("🚧 In Progress", in_progress)
        col4.metric("⏳ Not Started", not_started)
        col5.metric("⚠️ Overdue", overdue)

        st.markdown("---")
        st.subheader("⚠️ Overdue Tasks by Vendor")
        if not overdue_df.empty:
            overdue_count = overdue_df.groupby(['vendor']).size().reset_index(name='Overdue Tasks')
            bar_chart = px.bar(overdue_count, x='vendor', y='Overdue Tasks', color='vendor', title="Overdue Tasks by Vendor")
            st.plotly_chart(bar_chart, use_container_width=True)
            st.dataframe(overdue_df[['vendor', 'task', 'owner', 'status', 'target_date']].sort_values(by=['vendor', 'status', 'target_date']))
        else:
            st.success("🎉 No overdue tasks!")

        st.markdown("---")
        st.subheader("🏷️ Task Distribution by Vendor")
        task_count = filtered_df.groupby(['vendor']).size().reset_index(name='Task Count')
        vendor_chart = px.bar(task_count, x='vendor', y='Task Count', color='vendor', title="Tasks per Vendor")
        st.plotly_chart(vendor_chart, use_container_width=True)

        st.subheader("📆 Timeline View")
        filtered_df['task_display'] = filtered_df['task'].astype(str).str[:40]
        timeline = px.timeline(
            filtered_df.dropna(subset=['target_date']).sort_values(by=['vendor', 'status', 'target_date']),
            x_start="target_date",
            x_end="target_date",
            y="task_display",
            color="vendor",
            hover_data=["vendor", "owner", "status"],
            title="Task Timeline by Target Date"
        )
        timeline.update_yaxes(autorange="reversed")
        st.plotly_chart(timeline, use_container_width=True)

        st.markdown("---")
        st.subheader("📄 Full Task Table (Sorted by Vendor and Status)")
        st.dataframe(filtered_df.sort_values(by=['vendor', 'status', 'target_date']).reset_index(drop=True))

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📁 Upload your Excel file with a 'Harsha' sheet to begin.")
