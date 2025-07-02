import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px

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
        df = df[~df['Task'].str.lower().isin(['', 'details', 'task'])]  # remove placeholders
        df = df[df['Task'].str.len() > 3]  # ignore super short / nonsense tasks
        df = df[df['Task'].str.contains(r'[a-zA-Z]', na=False)]  # remove entries with no real text

        # STEP 6: Clean other columns
        df['Target Date'] = pd.to_datetime(df['Target Date'], errors='coerce')
        df['Status'] = df['Status'].fillna('').str.strip().str.title()
        df = df[df['Status'] != '']
        df['Owner'] = df['Owner'].fillna('Unassigned')

        # STEP 7: Compute overdue tasks
        today = pd.to_datetime(datetime.today().date())
        overdue_df = df[(df['Status'] != 'Completed') & (df['Target Date'] < today)]

        # DASHBOARD SECTIONS

        # 1. Overview
        st.subheader("📈 Overview")
        st.metric("Total Tasks", len(df))
        st.metric("Overdue Tasks", len(overdue_df))

        # 2. Task Status Distribution
        st.subheader("📊 Task Status Distribution")
        st.plotly_chart(
            px.pie(df.groupby('Status').size().reset_index(name='Count'),
                   names='Status', values='Count', title="Task Status Breakdown"))

        # 3. Overdue Tasks
        st.subheader("⚠️ Overdue Tasks by Owner")
        if not overdue_df.empty:
            st.plotly_chart(
                px.bar(overdue_df.groupby('Owner').size().reset_index(name='Overdue Tasks'),
                       x='Owner', y='Overdue Tasks', title="Overdue Tasks by Owner"))

            st.experimental_data_editor(
                overdue_df[['Vendor', 'Outcome', 'Task', 'Target Date', 'Status', 'Owner', 'Notes']],
                num_rows="dynamic",
                use_container_width=True
            )
        else:
            st.success("No overdue tasks found!")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
