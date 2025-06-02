import streamlit as st
import pandas as pd
from pathlib import Path
import datetime
import io
from excel_database_handler import upload_excel_database, EXCEL_DATABASE_FILE, PROCESSED_DATABASE_FILE

def render_uploader_dashboard(username):
    """Render the uploader dashboard"""
    st.title("Database Uploader Dashboard")
    st.subheader(f"Welcome, {username}")
    
    # Create tabs for different functionalities
    tabs = st.tabs(["Upload Database", "View Current Database"])
    
    # Upload Database Tab
    with tabs[0]:
        st.markdown("""
        ### Upload Excel Database File
        Upload an Excel file containing transaction data to be used for matching receipts.
        
        **Instructions for Bank Statement Excel Files:**
        1. Upload the complete bank statement Excel file
        2. The system will automatically extract transaction data
        3. Transactions need to have Date, Description, and Credit columns
        4. Descriptions should contain reference numbers (like REF.-E1234567890)
        """)
        
        uploaded_file = st.file_uploader("Choose an Excel file...", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            st.info("Preview of the uploaded Excel file (first 20 rows):")
            
            # Show a preview of the uploaded file
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df.head(20))
                
                # Reset the file pointer for later use
                uploaded_file.seek(0)
                
                # Upload button
                if st.button("Process and Save as Database", type="primary"):
                    with st.spinner("Processing Excel file..."):
                        success, message = upload_excel_database(uploaded_file)
                        
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            except Exception as e:
                st.error(f"Error processing Excel file: {e}")
    
    # View Current Database Tab
    with tabs[1]:
        st.markdown("### Current Transaction Database")
        
        # Show processed data if it exists, otherwise show the original
        target_file = PROCESSED_DATABASE_FILE if PROCESSED_DATABASE_FILE.exists() else EXCEL_DATABASE_FILE
        
        if target_file.exists():
            try:
                df = pd.read_excel(target_file)
                
                # Add filters for the dataframe
                st.write(f"Database contains {len(df)} transactions")
                
                # Filter options
                col1, col2 = st.columns(2)
                
                with col1:
                    # Date filter if available
                    if 'Date' in df.columns:
                        try:
                            # Convert to datetime if not already
                            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                            
                            # Get min and max dates
                            min_date = df['Date'].min().date()
                            max_date = df['Date'].max().date()
                            
                            # Add date range filter
                            date_range = st.date_input(
                                "Filter by date range",
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date
                            )
                            
                            if len(date_range) == 2:
                                start_date, end_date = date_range
                                mask = (df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)
                                df = df.loc[mask]
                        except Exception as e:
                            st.warning(f"Could not apply date filter: {e}")
                
                with col2:
                    # Text search filter
                    search_term = st.text_input("Search in descriptions")
                    if search_term:
                        if 'Description' in df.columns:
                            df = df[df['Description'].astype(str).str.contains(search_term, case=False)]
                
                # Display the filtered data
                st.dataframe(df)
                
                # Display reference numbers
                if 'Description' in df.columns:
                    from excel_database_handler import extract_reference_number
                    
                    st.subheader("Extracted Reference Numbers")
                    st.write("This shows what reference numbers would be used for matching receipts:")
                    
                    ref_data = []
                    for _, row in df.iterrows():
                        desc = str(row.get('Description', ''))
                        ref_num = extract_reference_number(desc)
                        if ref_num:
                            ref_data.append({
                                "Date": row.get('Date', ''),
                                "Reference Number": ref_num,
                                "Description": desc[:50] + "..." if len(desc) > 50 else desc
                            })
                    
                    if ref_data:
                        ref_df = pd.DataFrame(ref_data)
                        st.dataframe(ref_df)
                    else:
                        st.warning("No reference numbers found in the descriptions")
                
                # Add export options
                st.markdown("### Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download as CSV",
                        csv,
                        "transaction_database.csv",
                        "text/csv",
                        key='download-csv'
                    )
                
                with col2:
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False)
                    buffer.seek(0)
                    st.download_button(
                        "Download as Excel",
                        buffer,
                        "transaction_database.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key='download-excel'
                    )
                    
            except Exception as e:
                st.error(f"Error reading database file: {e}")
        else:
            st.warning("No database file found. Please upload an Excel file first.")
            
            # Option to create sample database
            if st.button("Create Sample Database"):
                from excel_database_handler import initialize_excel_dir
                initialize_excel_dir()
                st.success("Sample database created! Refresh the page to view it.")
                st.rerun()

if __name__ == "__main__":
    # For testing the uploader dashboard directly
    st.session_state.username = "uploader@akigroup.com"
    render_uploader_dashboard(st.session_state.username)