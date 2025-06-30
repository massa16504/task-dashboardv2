import pandas as pd
import streamlit as st

st.title("Task Dashboard")
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=None)
    
    for sheet_name, sheet_df in df.items():
        sheet_df = sheet_df.dropna(how='all')
        vendor_rows = sheet_df[sheet_df.iloc[:,0].notna() & ~sheet_df.iloc[:,0].str.lower().isin(['details', 'task'])]
        
        for idx in vendor_rows.index:
            vendor = sheet_df.iloc[idx,0]
            section = sheet_df.iloc[idx+1:]
            section.columns = section.iloc[0]
            section = section[1:]
            section = section.dropna(subset=['Task'])
            
            if not section.empty:
                overdue = section[section['Target Date'] < pd.Timestamp.today()]
                st.subheader(f"Vendor: {vendor} - {sheet_name}")
                st.write("**Overdue Tasks:**")
                st.dataframe(overdue[['Task', 'Target Date', 'Status', 'Action with']])
                st.write("**All Tasks:**")
                st.dataframe(section)
