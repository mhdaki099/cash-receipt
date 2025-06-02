import oracledb
import os
import streamlit as st

def check_duplicate_receipt(reference_number):
    """
    Check if a receipt with the given reference number already exists in any of the receipt files
    or in the Oracle database.
    
    Args:
        reference_number: The reference number to check
        
    Returns:
        (bool, str): Tuple of (is_duplicate, source) where source indicates where the duplicate was found
    """
    # If the reference number is empty, return False
    if not reference_number:
        return False, ""
    
    # First check local JSON files
    from approval_system import load_data, PENDING_FILE, APPROVED_FILE, REJECTED_FILE
    
    # Debug: Print the reference number being checked
    st.write(f"Debug: Checking for duplicates of reference number: {reference_number}")
    
    # Check pending receipts
    pending_receipts = load_data(PENDING_FILE)
    for receipt in pending_receipts:
        if receipt.get('reference_number') == reference_number:
            return True, "pending approvals"
            
    # Check approved receipts
    approved_receipts = load_data(APPROVED_FILE)
    for receipt in approved_receipts:
        if receipt.get('reference_number') == reference_number:
            return True, "approved receipts"
            
    # Check rejected receipts
    rejected_receipts = load_data(REJECTED_FILE)
    for receipt in rejected_receipts:
        if receipt.get('reference_number') == reference_number:
            return True, "rejected receipts"
    
    # Then check Oracle database if connected
    # For now, skip Oracle DB check as it's giving false positives
    # Only do the actual Oracle DB check if explicitly enabled in the environment variables
    check_oracle_db = os.getenv("CHECK_ORACLE_DB_DUPLICATES", "false").lower() == "true"
    
    if check_oracle_db and hasattr(st.session_state, 'db_connection_status') and st.session_state.db_connection_status == "connected":
        try:
            # Get database connection parameters
            db_username = os.getenv("ORACLE_USERNAME", "system")
            password = os.getenv("ORACLE_PASSWORD")
            host = os.getenv("ORACLE_HOST", "localhost")
            port = os.getenv("ORACLE_PORT", "1521")
            service = os.getenv("ORACLE_SERVICE", "xe")
            
            if not password:
                st.warning("Oracle database password not found in environment variables.")
                return False, ""
                
            dsn = f"{host}:{port}/{service}"
            
            # Connect to database
            conn = oracledb.connect(
                user=db_username,
                password=password,
                dsn=dsn
            )
            
            # Query to check if reference number exists
            query = """
                SELECT COUNT(*) 
                FROM XAKI_AR_CASH_REC_AI_H 
                WHERE REC_REF_NUMBER = :reference_number
            """
            
            cur = conn.cursor()
            cur.execute(query, reference_number=reference_number)
            count = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            st.write(f"Debug: Oracle DB query result count: {count}")
            
            if count > 0:
                return True, "Oracle database"
                
        except Exception as e:
            st.error(f"Error checking database for duplicates: {str(e)}")
            
    # If no duplicates found
    return False, ""