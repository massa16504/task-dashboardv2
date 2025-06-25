import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Task Dashboard", layout="wide")
st.title("📊 Task Dashboard — Harsha Tab")

uploaded_file = st.file_uploader("📤 Upload your Excel file", type=["xlsx"])

if uploaded_file:
    try:
        # Try loading without header first to detect real headers
        preview_df = pd.read_excel(uploaded_file, sheet_name="Harsha", header=None)
        header_row = None

        # Search for the first row that likely contains the real headers
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
                df['target date'] = pd.to_datetime(df['target date'], errors='coerce')

                total = len(df)
                completed = len(df[df['status'].str.lower() == 'completed'])
                in_progress = len(df[df['status'].str.lower() == 'in progress'])
                not_started = len(df[df['status'].str.lower() == 'not started'])
                overdue = len(df[(df['status'].str.lower() != 'completed') & (df['target date'] < datetime.today())])

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("📋 Total", total)
                col2.metric("✅ Completed", completed)
                col3.metric("🚧 In Progress", in_progress)
                col4.metric("⏳ Not Started", not_started)
                col5.metric("⚠️ Overdue", overdue)

                st.markdown("---")
                st.subheader("📌 Task Distribution by Status")
                chart = px.pie(df, names="status", title="Task Status Breakdown", hole=0.4)
                st.plotly_chart(chart, use_container_width=True)

                st.subheader("🗂 Preview (first 10 rows)")
                st.dataframe(df.head(10))

    except Exception as e:
        st.error(f"❌ Error reading file: {e}")
else:
    st.info("📁 Upload an Excel file with a 'Harsha' sheet to get started.")
