
import streamlit as st
import pandas as pd
import logging
from io import BytesIO
import datetime

from workflows.validation_workflow import ValidationWorkflow
from utils.config import config
from utils.database import DatabaseManager

st.title("Data Validation and Notification Workflow")

# Data source selection
st.sidebar.header("Data Source")
data_source = st.sidebar.radio(
    "Select data source:",
    ["Upload New File", "Use Existing Data"]
)

# Initialize database manager
db_manager = DatabaseManager()

if data_source == "Upload New File":
    # Use session state to reset sheet selection and store file name after each upload
    if 'sheet_names' not in st.session_state:
        st.session_state.sheet_names = []
    if 'sheet_name' not in st.session_state:
        st.session_state.sheet_name = None
    if 'uploaded_filename' not in st.session_state:
        st.session_state.uploaded_filename = None

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

    if uploaded_file is not None:
        # Save uploaded file to database and reset session state
        try:
            file_data = uploaded_file.getbuffer().tobytes()
            
            # Connect to database and store file
            if db_manager.connect():
                # First save to temp location for sheet analysis
                with open("data/uploaded.xlsx", "wb") as f:
                    f.write(file_data)
                
                excel_file = pd.ExcelFile("data/uploaded.xlsx")
                sheet_names = excel_file.sheet_names
                
                # Store in database
                success = db_manager.store_file_data(
                    filename=uploaded_file.name,
                    file_data=file_data,
                    file_type='xlsx',
                    sheet_names=sheet_names,
                    metadata={'upload_time': datetime.datetime.now().isoformat()}
                )
                
                if success:
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.sheet_names = sheet_names
                    st.session_state.sheet_name = None
                    st.success(f"Uploaded and stored file: {st.session_state.uploaded_filename}")
                    st.write("Available sheets:", st.session_state.sheet_names)
                else:
                    st.error("Failed to store file in database")
                
                db_manager.close()
            else:
                st.error("Failed to connect to database")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

elif data_source == "Use Existing Data":
    st.header("Available Files in Database")
    
    # Connect to database and get available files
    if db_manager.connect():
        available_files = db_manager.get_available_files()
        
        if available_files:
            # Display available files in a table
            files_df = pd.DataFrame(available_files)
            st.dataframe(files_df[['filename', 'upload_date', 'file_type']])
            
            # File selection
            selected_file_id = st.selectbox(
                "Select a file to validate:",
                options=[f['id'] for f in available_files],
                format_func=lambda x: next(f['filename'] for f in available_files if f['id'] == x)
            )
            
            if selected_file_id:
                selected_file_info = db_manager.get_file_info(selected_file_id)
                if selected_file_info:
                    st.session_state.uploaded_filename = selected_file_info['filename']
                    st.session_state.sheet_names = selected_file_info['sheet_names']
                    st.session_state.sheet_name = None
                    
                    # Get file data and save temporarily for validation
                    file_data = db_manager.get_file_data(selected_file_id)
                    if file_data:
                        with open("data/uploaded.xlsx", "wb") as f:
                            f.write(file_data)
                        st.success(f"Selected file: {selected_file_info['filename']}")
                        st.write("Available sheets:", st.session_state.sheet_names)
        else:
            st.info("No files found in database. Please upload a file first.")
        
        db_manager.close()
    else:
        st.error("Failed to connect to database")

# Rest of the validation workflow (unchanged)

if st.button("Run Validation") and st.session_state.sheet_names:
    workflow = ValidationWorkflow()
    result = workflow.run_all_sheets("data/uploaded.xlsx")

    st.subheader("Validation Results (All Sheets)")

    # Show aggregated summary
    aggregated_result = result.get("aggregated_result", {})
    if aggregated_result:
        summary = aggregated_result.get("summary", {})
        st.markdown("**Overall Validation Summary:**")
        st.info(f"Total Sheets: {aggregated_result.get('total_sheets', 0)} | Valid Sheets: {summary.get('valid_sheets', 0)} | Sheets with Issues: {summary.get('sheets_with_issues', 0)} | Total Errors: {summary.get('total_errors', 0)}")
        st.write({
            "Overall Status": "✅ Valid" if aggregated_result.get("is_valid") else "❌ Issues Found",
            "Periodic Trigger": aggregated_result.get("periodic_trigger", False)
        })

        # Show detailed table of missing/invalid data for all sheets
        errors = aggregated_result.get("errors", [])
        if errors:
            st.markdown("**Detailed Missing/Invalid Data Table (All Sheets):**")
            error_df = pd.DataFrame(errors)
            error_df = error_df[['sheet', 'row_index', 'status', 'missing_columns', 'invalid_values', 'details']]
            error_df.columns = ['Sheet', 'Row', 'Status', 'Missing Columns', 'Invalid Columns', 'Details']
            st.dataframe(error_df)
        else:
            st.success("✅ All sheets validated successfully - no missing or invalid data found!")

    # Show individual sheet results
    all_sheets_results = result.get("all_sheets_results", {})
    for sheet, sheet_result in all_sheets_results.items():
        st.markdown(f"### Sheet: {sheet}")
        validation_result = sheet_result.get("validation_result", {})
        product_issue_results = validation_result.get("product_issue_results", [])

        # Show summary for this sheet
        sheet_summary = validation_result.get("summary", {})
        st.info(f"Rows: {sheet_summary.get('total_rows', 0)} | Valid: {sheet_summary.get('valid_rows', 0)} | Missing: {sheet_summary.get('error_rows', 0)}")

        # Show detailed table for this sheet
        if product_issue_results:
            display_df = pd.DataFrame(product_issue_results)
            display_df = display_df[['row_index', 'status', 'missing_columns', 'invalid_values', 'details']]
            display_df.columns = ['Row', 'Status', 'Missing Columns', 'Invalid Columns', 'Details']
            st.dataframe(display_df)
            missing_columns = set()
            for r in product_issue_results:
                details = r.get('details', '')
                if 'Missing value(s) in required fields.' in details:
                    # Optionally, parse which columns are missing if you want more detail
                    missing_columns.update([col for col in ['Outcome', 'Outcome Statement', 'Test'] if pd.isnull(r.get(col))])
            if missing_columns:
                st.warning(f"Missing columns in this sheet: {', '.join(missing_columns)}")
        else:
            st.success(f"No missing data found in sheet '{sheet}'.")
