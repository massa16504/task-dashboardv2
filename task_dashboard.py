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
            'outcome': 'service',
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

            service_options = df['service'].dropna().unique().tolist()
            selected_services = st.multiselect("Filter by Service", service_options, default=service_options)

            owner_options = df['owner'].dropna().unique().tolist()
            selected_owners = st.multiselect("Filter by Owner", owner_options, default=owner_options)

            status_options = df['status'].dropna().unique().tolist()
            selected_statuses = st.multiselect("Filter by Status", status_options, default=status_options)

        filtered_df = df[
            (df['vendor'].isin(selected_vendors)) &
            (df['service'].isin(selected_services)) &
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
        st.subheader("⚠️ Overdue Tasks by Owner")
        if not overdue_df.empty:
            overdue_count = overdue_df.groupby(['owner']).size().reset_index(name='Overdue Tasks')
            bar_chart = px.bar(overdue_count, x='owner', y='Overdue Tasks', color='owner', title="Overdue Tasks by Owner")
            st.plotly_chart(bar_chart, use_container_width=True)
            st.dataframe(overdue_df[['vendor', 'service', 'task', 'owner', 'status', 'target_date']].sort_values(by='target_date'))
        else:
            st.success("🎉 No overdue tasks!")

        st.markdown("---")
        st.subheader("👥 Task Distribution by Owner and Vendor")
        task_count = filtered_df.groupby(['vendor', 'owner']).size().reset_index(name='Task Count')
        owner_chart = px.bar(task_count, x='owner', y='Task Count', color='vendor', title="Tasks by Owner and Vendor", barmode='stack')
        st.plotly_chart(owner_chart, use_container_width=True)

        st.subheader("📆 Timeline View")
        filtered_df['task_display'] = filtered_df['task'].astype(str).str[:40]
        timeline = px.timeline(
            filtered_df.dropna(subset=['target_date']),
            x_start="target_date",
            x_end="target_date",
            y="task_display",
            color="status",
            hover_data=["vendor", "service", "owner"],
            title="Task Timeline by Target Date"
        )
        timeline.update_yaxes(autorange="reversed")
        st.plotly_chart(timeline, use_container_width=True)

        st.markdown("---")
        st.subheader("📄 Full Task Table")
        st.dataframe(filtered_df.reset_index(drop=True))

    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("📁 Upload your Excel file with a 'Harsha' sheet to begin.")
