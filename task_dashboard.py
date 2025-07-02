import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard")

uploaded_file = st.file_uploader("📅 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # STEP 1: Find the header row containing 'Task'
        header_row_idx = raw_df.index[
            raw_df.apply(lambda row: row.astype(str).str.lower().str.contains('task').any(), axis=1)
        ].tolist()
        if not header_row_idx:
            raise Exception("❌ Could not find header row containing 'Task'")
        header_row_idx = header_row_idx[0]

        # STEP 2: Read main DataFrame using header row
        df = pd.read_excel(xls, sheet_name=sheet, header=header_row_idx)

        # STEP 3: Rebuild vendor column by forward-filling first column
        vendor_series = raw_df.iloc[:, 0].fillna(method='ffill')
        vendor_values = vendor_series[header_row_idx + 1:].reset_index(drop=True)
        df.insert(0, 'Vendor', vendor_values)

        # STEP 4: Clean and rename columns
        df.columns = df.columns.str.strip()
        df.rename(columns={
            'Target Date': 'Target Date',
            'Start Date': 'Start Date',
            'Action with': 'Owner',
            'Cross Functional': 'Cross Functional'
        }, inplace=True)

        # STEP 5: Filter Task column
        df['Task'] = df['Task'].astype(str).str.strip()
        df = df[~df['Task'].str.lower().isin(['', 'details', 'task'])]
        df = df[df['Task'].str.len() > 3]
        df = df[df['Task'].str.contains(r'[a-zA-Z]', na=False)]

        # STEP 6: Clean other columns
        df['Target Date'] = pd.to_datetime(df['Target Date'], errors='coerce')
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        df['Status'] = df['Status'].fillna('').str.strip().str.title()
        df = df[df['Status'] != '']
        df['Owner'] = df['Owner'].fillna('Unassigned')

        # STEP 7: Compute overdue tasks
        today = pd.to_datetime(datetime.today().date())
        overdue_df = df[(df['Status'] != 'Completed') & (df['Target Date'] < today)]

        # 🔍 SIDEBAR FILTER: VENDOR
        with st.sidebar:
            st.header("🔎 Filter")
            selected_vendors = st.multiselect(
                "Select Vendor(s)", options=sorted(df['Vendor'].dropna().unique()), default=None
            )

        if selected_vendors:
            df = df[df['Vendor'].isin(selected_vendors)]
            overdue_df = overdue_df[overdue_df['Vendor'].isin(selected_vendors)]

        # DASHBOARD SECTIONS

        # 1. Overview
        st.subheader("📈 Overview")
        st.metric("Total Tasks", len(df))
        st.metric("Overdue Tasks", len(overdue_df))

        # 2. Task Status Distribution
        st.subheader("📊 Task Status Distribution")
        st.plotly_chart(
            px.pie(df.groupby('Status').size().reset_index(name='Count'),
                   names='Status', values='Count', title="Task Status Breakdown")
        )

        # 3. Overdue Tasks Section
        st.subheader("⚠️ Overdue Tasks by Owner")
        if not overdue_df.empty:
            st.plotly_chart(
                px.bar(overdue_df.groupby('Owner').size().reset_index(name='Overdue Tasks'),
                       x='Owner', y='Overdue Tasks', title="Overdue Tasks by Owner")
            )

            st.markdown("### 🗂️ Overdue Task Table")

            df_display = overdue_df[['Vendor', 'Outcome', 'Task', 'Target Date', 'Status', 'Owner', 'Notes']]
            gb = GridOptionsBuilder.from_dataframe(df_display)
            gb.configure_default_column(filter=True, sortable=True, resizable=True)
            grid_options = gb.build()

            AgGrid(
                df_display,
                gridOptions=grid_options,
                height=400,
                theme="streamlit",
                enable_enterprise_modules=True
            )
        else:
            st.success("No overdue tasks found!")

        # 4. ✅ Vendor Completion Status
        st.subheader("📦 Vendor Completion Status")
        vendor_status = df.groupby(['Vendor', 'Status']).size().unstack(fill_value=0)
        vendor_status['Total'] = vendor_status.sum(axis=1)
        if 'Completed' not in vendor_status.columns:
            vendor_status['Completed'] = 0
        vendor_status['% Completed'] = (vendor_status['Completed'] / vendor_status['Total']) * 100

        st.plotly_chart(
            px.bar(
                vendor_status.reset_index(),
                x='% Completed',
                y='Vendor',
                orientation='h',
                title="Vendor Task Completion Percentage",
                text='% Completed',
                labels={'% Completed': 'Completion %'}
            ).update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        )

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")

