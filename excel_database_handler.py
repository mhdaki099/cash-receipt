import streamlit as st
import pandas as pd
import re
import os
from pathlib import Path
import io

DATA_DIR = Path("data")
EXCEL_DATABASE_DIR = DATA_DIR / "excel_database"
EXCEL_DATABASE_FILE = EXCEL_DATABASE_DIR / "transactions_database.xlsx"
PROCESSED_DATABASE_FILE = EXCEL_DATABASE_DIR / "processed_transactions.xlsx"

def initialize_excel_dir():
    """Initialize directory for Excel database files"""
    EXCEL_DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create a sample Excel file if none exists (for testing)
    if not PROCESSED_DATABASE_FILE.exists() and not EXCEL_DATABASE_FILE.exists():
        # Create sample data
        data = {
            'Date': ['31/03/2025', '30/03/2025', '29/03/2025'],
            'Description': [
                'SDM DEPOSIT CRSDM REF.-E4010262250107773;MIZHER MALL BRANCH SDME4010262250107773 - AE1306364',
                'STANDING ORDERTRF FRM 1015314156901 1014481491501 - S82874175',
                'CASH DEPOSIT REF.-E8872513390178865;AL QUOZ BRANCH 8872513390178865 - AE7316354'
            ],
            'Debit': [0.0, 0.0, 0.0],
            'Credit': [5000.00, 3000.00, 2500.00],
            'Balance': [10533371.29, 10528371.29, 10525371.29]
        }
        df = pd.DataFrame(data)
        df.to_excel(PROCESSED_DATABASE_FILE, index=False)

def extract_transaction_data_from_bank_statement(df):
    """
    Extract the transaction data from a bank statement Excel file.
    Bank statements typically have account information at the top followed by transactions.
    This function will skip the header information and extract just the transaction data.
    """
    try:
        # Try to find where the transaction data starts by looking for common header rows
        header_indicators = ['Date', 'Description', 'Debit', 'Credit', 'Balance']
        
        # Look for rows that might contain the transaction headers
        header_row_index = None
        for idx, row in df.iterrows():
            # Convert row values to strings for comparison
            row_values = [str(val).lower() if val is not None else '' for val in row.values]
            
            # Count how many indicators are in this row
            matches = sum(1 for indicator in header_indicators if any(indicator.lower() in val for val in row_values))
            
            # If we find at least 2 indicators, this is likely our header row
            if matches >= 2:
                header_row_index = idx
                break
                
        if header_row_index is None:
            # If no header row was found, try a different approach - look for date patterns
            for idx, row in df.iterrows():
                for val in row.values:
                    if isinstance(val, str) and re.search(r'\d{1,2}/\d{1,2}/\d{4}', val):
                        # Look at the next row to see if it contains transaction data
                        if idx + 1 < len(df):
                            header_row_index = idx - 1  # The header is typically one row before the dates
                            break
                if header_row_index is not None:
                    break
        
        if header_row_index is None:
            # Still no luck - fall back to assuming row 12 (index 11) is the header based on screenshot
            header_row_index = 12
            st.warning("Could not automatically detect transaction headers. Using row 13 as the header row.")
        
        # Use the header row to create a new DataFrame
        headers = df.iloc[header_row_index].tolist()
        
        # Clean up header names - replace None or empty with column position
        clean_headers = []
        for i, header in enumerate(headers):
            if pd.isna(header) or header is None or str(header).strip() == '':
                clean_headers.append(f"Column_{i}")
            else:
                clean_headers.append(str(header).strip())
        
        # Get the data rows (everything after the header row)
        data = df.iloc[header_row_index + 1:].copy()
        
        # Reset the index and set the column names
        data = data.reset_index(drop=True)
        data.columns = clean_headers
        
        # Filter out completely empty rows
        data = data.dropna(how='all')
        
        # Ensure we have the required columns
        required_columns = ['Date', 'Description']
        missing_columns = [col for col in required_columns if not any(col.lower() in header.lower() for header in clean_headers)]
        
        if missing_columns:
            # Try to identify and rename columns based on content
            if 'Date' in missing_columns:
                # Look for a column that contains date-like strings
                for col in data.columns:
                    if data[col].iloc[0] and re.search(r'\d{1,2}/\d{1,2}/\d{4}', str(data[col].iloc[0])):
                        data.rename(columns={col: 'Date'}, inplace=True)
                        missing_columns.remove('Date')
                        break
            
            if 'Description' in missing_columns:
                # Look for a column that contains longer text strings
                for col in data.columns:
                    if data[col].iloc[0] and isinstance(data[col].iloc[0], str) and len(str(data[col].iloc[0])) > 15:
                        data.rename(columns={col: 'Description'}, inplace=True)
                        missing_columns.remove('Description')
                        break
        
        if missing_columns:
            st.warning(f"Could not find required columns: {', '.join(missing_columns)}")
        
        # Try to ensure we have a Credit/Amount column
        if not any('credit' in col.lower() for col in data.columns):
            # Look for columns with numeric values that might be amounts
            for col in data.columns:
                if col not in ['Date', 'Description'] and data[col].iloc[0] and pd.to_numeric(data[col], errors='coerce').notna().any():
                    data.rename(columns={col: 'Credit'}, inplace=True)
                    break
        
        return data
        
    except Exception as e:
        st.error(f"Error extracting transaction data: {str(e)}")
        return None

def upload_excel_database(uploaded_file):
    """Upload and save Excel file to be used as the database"""
    try:
        # Ensure the directory exists
        initialize_excel_dir()
        
        # Read the Excel file - skip rows that are clearly header information
        df = pd.read_excel(uploaded_file)
        
        # Display the raw dataframe for debugging
        st.write("Raw Excel Data Preview:")
        st.dataframe(df.head(20))
        
        # Extract the transaction data
        transaction_data = extract_transaction_data_from_bank_statement(df)
        
        if transaction_data is None or len(transaction_data) == 0:
            return False, "Could not extract transaction data from the Excel file"
        
        # Display the extracted transaction data
        st.write("Extracted Transaction Data:")
        st.dataframe(transaction_data.head(10))
        
        # Save both the original and processed data
        df.to_excel(EXCEL_DATABASE_FILE, index=False)
        transaction_data.to_excel(PROCESSED_DATABASE_FILE, index=False)
        
        return True, f"Excel database successfully uploaded! Extracted {len(transaction_data)} transactions."
    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}"

def extract_reference_number(description):
    """Extract reference number from description text"""
    # Pattern to look for REF.-EXXXXXXXXXX or similar patterns
    ref_pattern = r'REF\.-E?(\d+)'
    match = re.search(ref_pattern, description)
    
    if match:
        return match.group(1)  # Return just the numeric part
    
    # Secondary pattern for standing orders
    standing_order_pattern = r'S(\d+)'
    match = re.search(standing_order_pattern, description)
    
    if match:
        return match.group(1)
    
    return None

def match_receipt_with_database(receipt_data):
    """
    Check if the receipt matches with a transaction in the Excel database
    
    Args:
        receipt_data: Dictionary containing receipt info
        
    Returns:
        (bool, dict): Tuple of (is_match, match_details)
    """
    if not PROCESSED_DATABASE_FILE.exists():
        return False, {"error": "Excel database not found"}
    
    try:
        # Read the processed Excel database
        df = pd.read_excel(PROCESSED_DATABASE_FILE)
        
        # Get the reference number from receipt
        receipt_ref_num = receipt_data.get('reference_number', '')
        
        # Convert date format if needed
        try:
            receipt_date = pd.to_datetime(receipt_data.get('deposit_date', ''), format='%d/%m/%Y')
        except:
            # If date parsing fails, use a broad date range
            receipt_date = None
        
        # Get amount from receipt
        try:
            receipt_amount = float(receipt_data.get('amount_aed', 0))
        except:
            receipt_amount = 0
        
        # Look for matching transactions
        matches = []
        
        for _, row in df.iterrows():
            # Extract reference number from database description
            description = str(row.get('Description', ''))
            db_ref_num = extract_reference_number(description)
            
            # Skip if no reference number found
            if not db_ref_num:
                continue
                
            # Check if reference numbers match (partial match)
            if db_ref_num in receipt_ref_num or receipt_ref_num in db_ref_num:
                # Check if amounts are close (within 0.01)
                # Try different column names for credit amount
                credit_col = None
                for col in ['Credit', 'Amount', 'Deposit']:
                    if col in df.columns:
                        credit_col = col
                        break
                
                if credit_col is None:
                    # Try to find a column that might contain amounts
                    for col in df.columns:
                        if col not in ['Date', 'Description', 'Debit', 'Balance']:
                            try:
                                val = float(row[col])
                                if val > 0:  # Positive value could be a credit
                                    credit_col = col
                                    break
                            except:
                                pass
                
                db_amount = 0
                if credit_col:
                    try:
                        db_amount = float(row[credit_col]) if not pd.isna(row[credit_col]) else 0
                    except:
                        db_amount = 0
                
                amount_match = abs(db_amount - receipt_amount) < 0.01
                
                # Check date if available
                date_match = True
                if receipt_date is not None:
                    try:
                        db_date = pd.to_datetime(row['Date'], format='%d/%m/%Y')
                        date_match = (db_date == receipt_date)
                    except:
                        date_match = False
                
                # If both reference and amount match, consider it a match
                if amount_match:  # We can make this stricter by adding "&& date_match" if needed
                    matches.append({
                        "database_date": str(row.get('Date', '')),
                        "database_description": description,
                        "database_amount": db_amount,
                        "database_reference": db_ref_num,
                        "match_quality": "High" if (amount_match and date_match) else "Medium"
                    })
        
        if matches:
            return True, {"matches": matches}
        else:
            return False, {"message": "No matching transactions found in database"}
            
    except Exception as e:
        return False, {"error": f"Error matching receipt: {str(e)}"}