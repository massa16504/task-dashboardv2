import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

# Constants
EXPECTED_COLUMNS = ['Task', 'Target Date', 'Status', 'Action with']
SAMPLE_DATA = {
    'Task': ['Review contract', 'Update documentation', 'Monthly report'],
    'Target Date': [datetime(2023,12,31), datetime(2023,11,15), datetime(2023,10,1)],
    'Status': ['Pending', 'In Progress', 'Overdue'],
    'Action with': ['Legal Team', 'Technical Team', 'Management']
}

def create_sample_file():
    """Generate a sample Excel file for download"""
    df = pd.DataFrame(SAMPLE_DATA)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sample Vendor')
    return output.getvalue()

def validate_dataframe(df):
    """Check if dataframe contains required columns"""
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
        return False
    return True

def process_sheet(sheet_name, sheet_df):
    """Process a single sheet from the Excel file"""
    sheet_df = sheet_df.dropna(how='all').reset_index(drop=True)
    vendor_rows = sheet_df[sheet_df.iloc[:,0].notna() & 
                         ~sheet_df.iloc[:,0].str.lower().str.contains('details|task', na=False)]
    
    results = []
    for idx in vendor_rows.index:
        vendor = sheet_df.iloc[idx, 0]
        section = sheet_df.iloc[idx+1:].reset_index(drop=True)
        
        # Set headers from first row after vendor name
        if not section.empty:
            section.columns = section.iloc[0]
            section = section[1:]
            section = section.dropna(subset=['Task'])
            
            if not section.empty and validate_dataframe(section):
                # Convert Target Date to datetime if it's not already
                if 'Target Date' in section:
                    section['Target Date'] = pd.to_datetime(section['Target Date'], errors='coerce')
                
                overdue = section[section['Target Date'] < pd.Timestamp.today()] if 'Target Date' in section else pd.DataFrame()
                results.append({
                    'vendor': vendor,
                    'sheet_name': sheet_name,
                    'all_tasks': section,
                    'overdue_tasks': overdue
                })
    return results

def display_vendor_data(vendor_data):
    """Display processed vendor data in the dashboard"""
    for data in vendor_data:
        with st.expander(f"Vendor: {data['vendor']} - {data['sheet_name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Tasks", len(data['all_tasks']))
            
            with col2:
                st.metric("Overdue Tasks", len(data['overdue_tasks']))
            
            st.subheader("Overdue Tasks")
            if not data['overdue_tasks'].empty:
                st.dataframe(data['overdue_tasks'][EXPECTED_COLUMNS])
            else:
                st.success("No overdue tasks!")
            
            st.subheader("All Tasks")
            st.dataframe(data['all_tasks'])

def main():
    """Main dashboard function"""
    st.title("📊 Task Dashboard")
    st.markdown("Upload an Excel file to analyze task status by vendor")
    
    # Sample file download
    sample_file = create_sample_file()
    st.download_button(
        label="Download Sample File",
        data=sample_file,
        file_name="task_sample.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
    
    if uploaded_file:
        try:
            with st.spinner("Processing file..."):
                df = pd.read_excel(uploaded_file, sheet_name=None)
            
            all_vendor_data = []
            for sheet_name, sheet_df in df.items():
                vendor_data = process_sheet(sheet_name, sheet_df)
                all_vendor_data.extend(vendor_data)
            
            if all_vendor_data:
                st.success(f"Processed {len(all_vendor_data)} vendor sections")
                display_vendor_data(all_vendor_data)
            else:
                st.warning("No valid vendor data found in the uploaded file.")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()