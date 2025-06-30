import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        first_sheet = excel_file.sheet_names[0]
        df = pd.read_excel(excel_file, sheet_name=first_sheet, header=None)

        header_row_index = df.index[df.iloc[:, 0].astype(str).str.lower().str.contains("task")].tolist()
        header_row = header_row_index[0] if header_row_index else 0

        df = pd.read_excel(excel_file, sheet_name=first_sheet, header=header_row)
        df.columns = df.columns.str.strip().str.lower()

        required_cols = ['vendor', 'task', 'target date', 'status', 'action with']
        for col in required_cols:
            if col not in df.columns:
                df[col] = ''

        df.rename(columns={'nutanix': 'vendor', 'action with': 'owner', 'target date': 'target_date'}, inplace=True)

        df['target_date'] = pd.to_datetime(df['target_date'], errors='coerce')
        df['status'] = df['status'].fillna('').str.strip().str.title()
        df['owner'] = df['owner'].fillna("Unassigned")
        df['task'] = df['task'].fillna('')

        df = df[(~df['vendor'].str.lower().isin(['vendor', ''])) &
                (~df['task'].str.lower().isin(['details', 'task', '']))]

        overdue_df = df[(df['status'] != 'Completed') & (df['target_date'] < datetime.today())]

        st.subheader("📈 Overview")
        st.metric("Total Tasks", len(df))
        st.metric("Overdue Tasks", len(overdue_df))

        st.subheader("⚠️ Overdue Tasks by Owner")
        if not overdue_df.empty:
            chart = px.bar(overdue_df.groupby('owner').size().reset_index(name='Overdue Tasks'), x='owner', y='Overdue Tasks')
            st.plotly_chart(chart)
            st.dataframe(overdue_df[['vendor', 'task', 'owner', 'status', 'target_date']])
        else:
            st.success("No overdue tasks!")

        st.subheader("📊 Task Status Distribution")
        status_count = df.groupby('status').size().reset_index(name='Count')
        pie_chart = px.pie(status_count, names='status', values='Count', title="Task Status Breakdown")
        st.plotly_chart(pie_chart)

        st.subheader("📊 Tasks by Vendor")
        vendor_count = df.groupby('vendor').size().reset_index(name='Tasks')
        bar_chart = px.bar(vendor_count, x='vendor', y='Tasks', title="Tasks per Vendor")
        st.plotly_chart(bar_chart)

        st.subheader("📄 All Tasks")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload an Excel file to begin.")
