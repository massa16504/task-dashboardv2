import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet = xls.sheet_names[0]
        raw_df = pd.read_excel(xls, sheet_name=sheet, header=None)

        # Find the header row (where "Task" appears)
        header_idx = raw_df.index[raw_df.apply(lambda row: row.astype(str).str.lower().str.contains('task').any(), axis=1)].tolist()
        if not header_idx:
            raise Exception("Header row with 'Task' not found.")
        header_idx = header_idx[0]

        df = pd.read_excel(xls, sheet_name=sheet, header=header_idx)

        # Fill down the vendor name from merged cells
        vendor_col = raw_df.iloc[:header_idx, 0].dropna().tolist()
        vendor_labels = raw_df.iloc[:, 0].fillna(method='ffill')
        df.insert(0, 'vendor', vendor_labels[header_idx+1:].reset_index(drop=True))

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Rename key columns for consistency
        df.rename(columns={
            'target date': 'target_date',
            'action with': 'owner',
            'cross functional': 'cross_functional'
        }, inplace=True)

        # Drop blank and title rows
        df['task'] = df['task'].astype(str).fillna('').str.strip()
        df = df[df['task'].apply(lambda x: x.lower() not in ['', 'details', 'task'])]

        df['vendor'] = df['vendor'].astype(str).fillna('').str.strip()
        df['owner'] = df['owner'].fillna('Unassigned')

        df['target_date'] = pd.to_datetime(df['target_date'], errors='coerce')
        df['status'] = df['status'].fillna('').str.strip().str.title()
        df = df[df['status'] != '']

        overdue_df = df[(df['status'] != 'Completed') & (df['target_date'] < datetime.today())]

        st.subheader("📈 Overview")
        st.metric("Total Tasks", len(df))
        st.metric("Overdue Tasks", len(overdue_df))

        st.subheader("⚠️ Overdue Tasks by Owner")
        if not overdue_df.empty:
            chart = px.bar(overdue_df.groupby('owner').size().reset_index(name='Overdue Tasks'), x='owner', y='Overdue Tasks')
            st.plotly_chart(chart)
            st.dataframe(overdue_df[['vendor', 'outcome', 'task', 'target_date', 'status', 'owner', 'notes']])
        else:
            st.success("No overdue tasks!")

        st.subheader("📊 Task Status Distribution")
        status_count = df.groupby('status').size().reset_index(name='Count')
        pie_chart = px.pie(status_count, names='status', values='Count', title="Task Status Breakdown")
        st.plotly_chart(pie_chart)

        st.subheader("📄 All Tasks")
        st.dataframe(df[['vendor', 'outcome', 'task', 'start date', 'target_date', 'status', 'cross_functional', 'owner', 'notes']])

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload an Excel file to begin.")