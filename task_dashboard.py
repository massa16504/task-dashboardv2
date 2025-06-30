import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        df_raw = pd.read_excel(uploaded_file, sheet_name=0, header=1)
        df_raw.columns = df_raw.columns.str.strip().str.lower()

        df_raw['vendor'] = df_raw['vendor'].astype(str).fillna('').str.strip()
        df = df_raw.rename(columns={'target date': 'target_date', 'action with': 'owner'})

        # Keep only rows where vendor looks like a real vendor (non-empty, not placeholder)
        df = df[(df['vendor'] != '') & (~df['vendor'].str.lower().isin(['vendor', 'details']))]

        df['task'] = df['task'].astype(str).fillna('').str.strip()
        df = df[(~df['task'].str.lower().isin(['details', 'task', '']))]

        df['target_date'] = pd.to_datetime(df['target_date'], errors='coerce')
        df['status'] = df['status'].fillna('').str.strip().str.title()
        df['owner'] = df['owner'].fillna('Unassigned')

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

        st.subheader("📄 All Tasks")
        st.dataframe(df)

    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Upload an Excel file to begin.")
