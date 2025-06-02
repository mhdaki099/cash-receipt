import streamlit as st
import base64
import requests
import json
from PIL import Image
import io
import os
import datetime
from dotenv import load_dotenv
import oracledb
from login import require_login
from login import require_login
from approval_system import submit_for_approval, get_notifications
from manager_dashboard import render_manager_dashboard
from salesperson_dashboard import render_salesperson_dashboard
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  
from approval_system import submit_for_approval, get_notifications
from duplicate_check import check_duplicate_receipt
from uploader_dashboard import render_uploader_dashboard
import oracledb

load_dotenv()
username, user_role = require_login()

try:
    oracledb.init_oracle_client()
    print("Oracle client initialized in thick mode")
except Exception as e:
    print(f"Warning: Could not initialize Oracle client: {e}")
    

if 'receipts' not in st.session_state:
    st.session_state.receipts = []

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

if 'db_connection_status' not in st.session_state:
    st.session_state.db_connection_status = None

if 'show_db_submit' not in st.session_state:
    st.session_state.show_db_submit = False
    
if 'last_receipt' not in st.session_state:
    st.session_state.last_receipt = None
    
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

if 'receipt_submitted' not in st.session_state:
    st.session_state.receipt_submitted = False

if 'approval_submitted' not in st.session_state:
    st.session_state.approval_submitted = False

if 'duplicate_error' not in st.session_state:
    st.session_state.duplicate_error = None

st.set_page_config(
    page_title="Receipt Data Extractor",
    page_icon="🧾",
    layout="centered"
)

UAE_BANKS = [
    "Select a Bank",
    "First Abu Dhabi Bank (FAB)",
    "Emirates NBD",
    "Abu Dhabi Commercial Bank (ADCB)",
    "Dubai Islamic Bank (DIB)",
    "Emirates Islamic Bank",
    "Abu Dhabi Islamic Bank (ADIB)",
    "Mashreq Bank",
    "RAKBANK (National Bank of Ras Al Khaimah)",
    "Commercial Bank of Dubai",
    "National Bank of Fujairah",
    "Sharjah Islamic Bank",
    "United Arab Bank",
    "Bank of Sharjah",
    "Ajman Bank",
    "Citibank UAE",
    "HSBC UAE",
    "Standard Chartered UAE",
    "Other"
]

def test_new_db_connection():
    """Test connection to the new Oracle database"""
    try:
        db_username = "apps"
        password = "apps"
        host = "10.50.65.11"
        port = "1526"
        service = "TEST"
        
        dsn = f"{host}:{port}/{service}"
        
        st.write(f"Testing connection to: {dsn}")
        st.write(f"Username: {db_username}")
        
        conn = oracledb.connect(
            user=db_username,
            password=password,
            dsn=dsn
        )
        
        # Test query to verify connection
        cur = conn.cursor()
        cur.execute("SELECT SYSDATE FROM DUAL")
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        st.success(f"✅ Successfully connected! Server time: {result[0]}")
        return True
        
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        return False
    

def check_db_connection():
    try:
        db_username = os.getenv("ORACLE_USERNAME", "apps")
        password = os.getenv("ORACLE_PASSWORD", "TestApps#2025")
        host = os.getenv("ORACLE_HOST", "10.50.65.11")
        port = os.getenv("ORACLE_PORT", "1526")
        service = os.getenv("ORACLE_SERVICE", "TEST")
        
        if not password:
            st.session_state.db_connection_status = "disconnected: No password found in environment variables"
            return False
            
        dsn = f"{host}:{port}/{service}"
        
        # Try thick mode first
        try:
            oracledb.init_oracle_client()
        except:
            pass  # Already initialized or not available
        
        conn = oracledb.connect(
            user=db_username,
            password=password,
            dsn=dsn
        )
        conn.close()
        st.session_state.db_connection_status = "connected"
        return True
    except Exception as e:
        st.session_state.db_connection_status = f"disconnected: {str(e)}"
    
    return False

if st.session_state.db_connection_status is None:
    check_db_connection()

# def insert_receipt_to_oracle(data):
#     st.markdown("### Oracle DB Connection", unsafe_allow_html=True)
    
#     # First check if we're already connected
#     if st.session_state.db_connection_status != "connected":
#         st.warning("Database connection not established. Attempting to reconnect...")
#         if not check_db_connection():
#             st.error("❌ Unable to connect to Oracle Database. Please check your configuration.")
#             return False
    
#     # Debug info to show connection attempt
#     st.write("Attempting to insert data into Oracle database...")
    
#     # Map your extracted data to the required columns
#     insert_sql = '''
#         INSERT INTO XXAKI_COLLECTIONS_EXT_STG (
#             RCPT_NO, RCPT_DATE, ORGANIZATION_ID, RECEIPT_SOURCE, COLLECTION_MODE, CUR_CODE, AMOUNT
#         ) VALUES (
#             :rcpt_no, :rcpt_date, :organization_id, :receipt_source, :collection_mode, :cur_code, :amount
#         )
#     '''
#     # Prompt for missing NOT NULL fields if not present
#     rcpt_no = data.get('reference_number') or st.text_input('Enter Receipt Number (RCPT_NO):', key='rcpt_no_input')
#     rcpt_date = data.get('deposit_date')
#     if isinstance(rcpt_date, str):
#         try:
#             rcpt_date = datetime.datetime.strptime(rcpt_date, "%d/%m/%Y")
#         except Exception as e:
#             st.warning(f"Date parsing error: {e}. Using current date.")
#             rcpt_date = datetime.datetime.now()
#     organization_id = data.get('organization_id') or st.number_input('Enter Organization ID (ORGANIZATION_ID):', min_value=1, key='org_id_input')
#     receipt_source = data.get('receipt_source') or st.text_input('Enter Receipt Source (RECEIPT_SOURCE):', value='BANK', key='rcpt_source_input')
#     collection_mode = data.get('collection_mode') or st.text_input('Enter Collection Mode (COLLECTION_MODE):', value='CASH', key='coll_mode_input')
#     cur_code = data.get('cur_code') or st.text_input('Enter Currency Code (CUR_CODE):', value='AED', key='cur_code_input')
#     amount = data.get('amount_aed') or 0
#     try:
#         amount = float(amount)
#     except Exception as e:
#         st.warning(f"Amount conversion error: {e}. Using 0.")
#         amount = 0

#     params = {
#         'rcpt_no': rcpt_no,
#         'rcpt_date': rcpt_date,
#         'organization_id': organization_id,
#         'receipt_source': receipt_source,
#         'collection_mode': collection_mode,
#         'cur_code': cur_code,
#         'amount': amount
#     }

#     # Display parameter values for debugging
#     with st.expander("Debug: Database Parameters"):
#         st.write(params)

#     # Add Insert button to extract section
#     if all(params.values()):
#         if st.button('Insert into Oracle DB', key='insert_db_button'):
#             try:
#                 # Debug connection parameters
#                 st.write("Connection parameters:")
#                 password = st.secrets["ORACLE_PASSWORD"] if "ORACLE_PASSWORD" in st.secrets else st.text_input('Oracle DB Password:', type='password', key='oracle_pw')
#                 st.write(f"User: system")
#                 st.write(f"DSN: localhost:1521/xe")
                
#                 conn = oracledb.connect(
#                     user='system',
#                     password=password,
#                     dsn='localhost:1521/xe'
#                 )
#                 st.success("✅ Connected to Oracle DB successfully!")
                
#                 cur = conn.cursor()
#                 cur.execute(insert_sql, params)
#                 conn.commit()
#                 cur.close()
#                 conn.close()
#                 st.success("✅ Receipt inserted into Oracle DB successfully!")
#             except Exception as e:
#                 st.error(f"❌ Failed to insert into Oracle DB: {e}")
#                 st.error("Please check your Oracle connection settings and try again.")
#     else:
#         st.info("Please fill all required fields above to enable DB insertion.")

#Worked 
# def insert_receipt_to_oracle(data):
#     st.markdown("### Oracle DB Connection", unsafe_allow_html=True)
    
#     # First check if we're already connected
#     if st.session_state.db_connection_status != "connected":
#         st.warning("Database connection not established. Attempting to reconnect...")
#         if not check_db_connection():
#             st.error("❌ Unable to connect to Oracle Database. Please check your .env file.")
#             st.info("Make sure your .env file contains: ORACLE_USERNAME, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT, and ORACLE_SERVICE")
#             return False
    
#     # Debug info to show connection attempt
#     st.write("Attempting to insert data into Oracle database...")
    
#     # Map your extracted data to the required columns
#     insert_sql = '''
#         INSERT INTO XXAKI_COLLECTIONS_EXT_STG (
#             RCPT_NO, RCPT_DATE, ORGANIZATION_ID, RECEIPT_SOURCE, COLLECTION_MODE, CUR_CODE, AMOUNT
#         ) VALUES (
#             :rcpt_no, :rcpt_date, :organization_id, :receipt_source, :collection_mode, :cur_code, :amount
#         )
#     '''
    
#     # Use DEFAULT_ORGANIZATION_ID from env if available
#     default_org_id = os.getenv("DEFAULT_ORGANIZATION_ID", "1")
    
#     # Prompt for missing NOT NULL fields if not present
#     rcpt_no = data.get('reference_number') or st.text_input('Enter Receipt Number (RCPT_NO):', key='rcpt_no_input')
#     rcpt_date = data.get('deposit_date')
#     if isinstance(rcpt_date, str):
#         try:
#             rcpt_date = datetime.datetime.strptime(rcpt_date, "%d/%m/%Y")
#         except Exception as e:
#             st.warning(f"Date parsing error: {e}. Using current date.")
#             rcpt_date = datetime.datetime.now()
#     organization_id = data.get('organization_id') or st.number_input('Enter Organization ID (ORGANIZATION_ID):', min_value=1, value=int(default_org_id), key='org_id_input')
#     receipt_source = data.get('receipt_source') or st.text_input('Enter Receipt Source (RECEIPT_SOURCE):', value='BANK', key='rcpt_source_input')
#     collection_mode = data.get('collection_mode') or st.text_input('Enter Collection Mode (COLLECTION_MODE):', value='CASH', key='coll_mode_input')
#     cur_code = data.get('cur_code') or st.text_input('Enter Currency Code (CUR_CODE):', value='AED', key='cur_code_input')
#     amount = data.get('amount_aed') or 0
#     try:
#         amount = float(amount)
#     except Exception as e:
#         st.warning(f"Amount conversion error: {e}. Using 0.")
#         amount = 0

#     params = {
#         'rcpt_no': rcpt_no,
#         'rcpt_date': rcpt_date,
#         'organization_id': organization_id,
#         'receipt_source': receipt_source,
#         'collection_mode': collection_mode,
#         'cur_code': cur_code,
#         'amount': amount
#     }

#     # Display parameter values for debugging
#     with st.expander("Debug: Database Parameters"):
#         st.write(params)

#     # Add Insert button to extract section
#     if all(params.values()):
#         if st.button('Insert into Oracle DB', key='insert_db_button'):
#             try:
#                 # Get credentials from environment variables
#                 username = os.getenv("ORACLE_USERNAME", "system")
#                 password = os.getenv("ORACLE_PASSWORD")
#                 host = os.getenv("ORACLE_HOST", "localhost")
#                 port = os.getenv("ORACLE_PORT", "1521")
#                 service = os.getenv("ORACLE_SERVICE", "xe")
                
#                 # Build DSN
#                 dsn = f"{host}:{port}/{service}"
                
#                 # Debug connection parameters
#                 st.write("Connection parameters:")
#                 st.write(f"User: {username}")
#                 st.write(f"DSN: {dsn}")
                
#                 conn = oracledb.connect(
#                     user=username,
#                     password=password,
#                     dsn=dsn
#                 )
#                 st.success("✅ Connected to Oracle DB successfully!")
                
#                 cur = conn.cursor()
#                 cur.execute(insert_sql, params)
#                 conn.commit()
#                 cur.close()
#                 conn.close()
#                 st.success("✅ Receipt inserted into Oracle DB successfully!")
#                 return True
#             except Exception as e:
#                 st.error(f"❌ Failed to insert into Oracle DB: {e}")
#                 st.error("Please check your Oracle connection settings and try again.")
#                 return False
#     else:
#         st.info("Please fill all required fields above to enable DB insertion.")
#         return False
#Worked    
# # def insert_receipt_to_oracle(data):
#     st.markdown("### Oracle DB Connection", unsafe_allow_html=True)
    
#     if hasattr(st.session_state, 'db_connection_status') and st.session_state.db_connection_status != "connected":
#         st.warning("Database connection not established. Attempting to reconnect...")
#         if not check_db_connection():
#             st.error("❌ Unable to connect to Oracle Database. Please check your configuration.")
#             return False
    
#     st.write("Attempting to insert data into Oracle database...")
    
#     insert_sql = '''
#         INSERT INTO XXAKI_COLLECTIONS_EXT_STG (
#             RCPT_NO, RCPT_DATE, RCPT_MTH_ID, BANK_ACCT_ID, SALESREP_ID, 
#             ORGANIZATION_ID, RECEIPT_SOURCE, CUSTOMER_ID, SITE_USE_ID, 
#             COLLECTION_MODE, CHEQUE_NO, CHEQUE_DATE, CUR_CODE, AMOUNT, 
#             INVOICE_ID, INVOICE_NO, APPROVED_BY
#         ) VALUES (
#             :rcpt_no, :rcpt_date, :rcpt_mth_id, :bank_acct_id, :salesrep_id,
#             :organization_id, :receipt_source, :customer_id, :site_use_id,
#             :collection_mode, :cheque_no, :cheque_date, :cur_code, :amount,
#             :invoice_id, :invoice_no, :approved_by
#         )
#     '''
    
#     rcpt_no = data.get('reference_number') or st.text_input('Enter Receipt Number (RCPT_NO):', key='rcpt_no_input')
    
#     if not rcpt_no:
#         st.error("Receipt reference number is required")
#         return False
    
#     is_duplicate, duplicate_source = check_duplicate_receipt(rcpt_no)
#     if is_duplicate:
#         error_msg = f"❌ Duplicate Receipt: A receipt with reference number '{rcpt_no}' already exists in {duplicate_source}."
#         st.session_state.duplicate_error = error_msg
#         st.error(error_msg)
#         return False
    
    
#     rcpt_date = data.get('deposit_date')
#     if isinstance(rcpt_date, str):
#         try:
#             rcpt_date = datetime.datetime.strptime(rcpt_date, "%d/%m/%Y")
#         except Exception as e:
#             st.warning(f"Date parsing error: {e}. Using current date.")
#             rcpt_date = datetime.datetime.now()
    
#     organization_id = os.getenv("DEFAULT_ORGANIZATION_ID") or st.number_input('Enter Organization ID (ORGANIZATION_ID):', min_value=1, value=1, key='org_id_input')
#     receipt_source = data.get('receipt_source') or st.text_input('Enter Receipt Source (RECEIPT_SOURCE):', value='BANK', key='rcpt_source_input')
#     collection_mode = data.get('collection_mode') or st.text_input('Enter Collection Mode (COLLECTION_MODE):', value='CASH', key='coll_mode_input')
#     cur_code = data.get('cur_code') or st.text_input('Enter Currency Code (CUR_CODE):', value='AED', key='cur_code_input')
    
#     amount = data.get('amount_aed') or 0
#     try:
#         amount = float(amount)
#     except Exception as e:
#         st.warning(f"Amount conversion error: {e}. Using 0.")
#         amount = 0

#     params = {
#         'rcpt_no': rcpt_no,
#         'rcpt_date': rcpt_date,
#         'rcpt_mth_id': None,  
#         'bank_acct_id': None,  
#         'salesrep_id': None,   
#         'organization_id': organization_id,
#         'receipt_source': receipt_source,
#         'customer_id': None,   
#         'site_use_id': None,    
#         'collection_mode': collection_mode,
#         'cheque_no': None,      
#         'cheque_date': None,    
#         'cur_code': cur_code,
#         'amount': amount,
#         'invoice_id': None,     
#         'invoice_no': None,     
#         'approved_by': None     
#     }

#     with st.expander("Debug: Database Parameters"):
#         st.write(params)

#     if st.button('Insert into Oracle DB', key='insert_db_button'):
#         try:
#             db_username  = os.getenv("ORACLE_USERNAME", "system")
#             password = os.getenv("ORACLE_PASSWORD")
#             host = os.getenv("ORACLE_HOST", "localhost")
#             port = os.getenv("ORACLE_PORT", "1521")
#             service = os.getenv("ORACLE_SERVICE", "xe")
            
#             if not password:
#                 st.error("Oracle database password not found in environment variables!")
#                 return False
            
#             dsn = f"{host}:{port}/{service}"
            
#             st.write("Connection parameters:")
#             st.write(f"User: {db_username}")
#             st.write(f"DSN: {dsn}")
            
#             try:
#                 conn = oracledb.connect(
#                     user=db_username ,
#                     password=password,
#                     dsn=dsn
#                 )
#                 st.success("✅ Connected to Oracle DB successfully!")
#             except Exception as e:
#                 st.error(f"❌ Connection failed: {str(e)}")
#                 return False
            
#             try:
#                 cur = conn.cursor()
#                 cur.execute(insert_sql, params)
#                 conn.commit()
#                 cur.close()
#                 conn.close()
#                 st.success("✅ Receipt inserted into Oracle DB successfully!")
                
#                 st.markdown("### Receipt added to database")
#                 st.markdown(f"""
#                     Receipt **{rcpt_no}** was successfully added with:
#                     - Amount: **{amount} {cur_code}**
#                     - Date: **{rcpt_date.strftime('%d-%b-%Y')}**
#                     - Organization: **{organization_id}**
#                 """)
#                 if user_role == "salesperson" and not st.session_state.get('approval_submitted', False):
#                     with st.spinner("Submitting for manager approval..."):
#                         approval_id = submit_for_approval(data, username)
#                         if approval_id:
#                             st.session_state.approval_submitted = True
#                             st.success(f"✅ Receipt submitted for manager approval (ID: {approval_id})")
#                         else:
#                             st.error("❌ Failed to submit for approval. Please try again.")
                
#                 st.session_state.form_submitted = False
#                 st.session_state.show_db_submit = False
#                 st.session_state.last_receipt = None


                
#                 return True
#             except Exception as e:
#                 st.error(f"❌ Insert failed: {str(e)}")
#                 st.error("Please check that the data you're trying to insert matches the requirements of the database.")
#                 if "unique constraint" in str(e).lower():
#                     st.warning("A receipt with this number may already exist in the database.")
#                 return False
                
#         except Exception as e:
#             st.error(f"❌ Failed to insert into Oracle DB: {e}")
#             st.error("Please check your Oracle connection settings and try again.")
#             return False
#     else:
#         st.info("Please fill all required fields above and click the button to insert data.")
#         return False

#     return False

def insert_receipt_to_oracle(data):
    """Insert receipt data into the new XAKI_AR_CASH_REC_AI_H table"""
    st.markdown("### Oracle DB Connection", unsafe_allow_html=True)
    
    if hasattr(st.session_state, 'db_connection_status') and st.session_state.db_connection_status != "connected":
        st.warning("Database connection not established. Attempting to reconnect...")
        if not check_db_connection():
            st.error("❌ Unable to connect to Oracle Database. Please check your configuration.")
            return False
    
    st.write("Attempting to insert data into Oracle database...")
    
    # Updated SQL for the new table structure
    insert_sql = '''
        INSERT INTO XAKI_AR_CASH_REC_AI_H (
            HEADER_ID, REC_SOURCE, REC_COLLECTION_MOD, REC_AMOUNT, REC_DATE, 
            REC_CURRENCY, REC_BANK_NAME, REC_BANK_ACCT_NUM, REC_REF_NUMBER, 
            REC_USER_NAME, SALES_FROM_DATE, SALES_TO_DATE, ORG_ID, STATUS, 
            CREATION_DATE
        ) VALUES (
            :header_id, :rec_source, :rec_collection_mod, :rec_amount, :rec_date,
            :rec_currency, :rec_bank_name, :rec_bank_acct_num, :rec_ref_number,
            :rec_user_name, :sales_from_date, :sales_to_date, :org_id, :status,
            :creation_date
        )
    '''
    
    rcpt_no = data.get('reference_number') or st.text_input('Enter Receipt Number (REC_REF_NUMBER):', key='rcpt_no_input')
    
    if not rcpt_no:
        st.error("Receipt reference number is required")
        return False
    
    # Check for duplicates
    is_duplicate, duplicate_source = check_duplicate_receipt(rcpt_no)
    if is_duplicate:
        error_msg = f"❌ Duplicate Receipt: A receipt with reference number '{rcpt_no}' already exists in {duplicate_source}."
        st.session_state.duplicate_error = error_msg
        st.error(error_msg)
        return False
    
    # Parse receipt date
    rcpt_date = data.get('deposit_date')
    if isinstance(rcpt_date, str):
        try:
            rcpt_date = datetime.datetime.strptime(rcpt_date, "%d/%m/%Y")
        except Exception as e:
            st.warning(f"Date parsing error: {e}. Using current date.")
            rcpt_date = datetime.datetime.now()
    
    # Parse sales dates
    sales_from_date = data.get('sales_from_date')
    sales_to_date = data.get('sales_to_date')
    
    if isinstance(sales_from_date, str):
        try:
            sales_from_date = datetime.datetime.strptime(sales_from_date, "%d/%m/%Y")
        except Exception:
            sales_from_date = datetime.datetime.now() - datetime.timedelta(days=30)
    
    if isinstance(sales_to_date, str):
        try:
            sales_to_date = datetime.datetime.strptime(sales_to_date, "%d/%m/%Y")
        except Exception:
            sales_to_date = datetime.datetime.now()
    
    # Get organization ID
    try:
        org_id = int(os.getenv("DEFAULT_ORGANIZATION_ID", "1"))
    except ValueError:
        org_id = 1
    
    # Parse amount
    amount = data.get('amount_aed') or 0
    try:
        amount = float(amount)
    except Exception as e:
        st.warning(f"Amount conversion error: {e}. Using 0.")
        amount = 0

    # Generate header ID (you might want to use a sequence from Oracle)
    header_id = int(datetime.datetime.now().timestamp())

    # Prepare parameters for the new table structure
    params = {
        'header_id': header_id,
        'rec_source': data.get('receipt_source', 'BANK'),
        'rec_collection_mod': data.get('collection_mode', 'CASH'),
        'rec_amount': amount,
        'rec_date': rcpt_date,
        'rec_currency': data.get('cur_code', 'AED'),
        'rec_bank_name': data.get('bank_account_name', ''),
        'rec_bank_acct_num': data.get('bank_account_number', ''),
        'rec_ref_number': rcpt_no,
        'rec_user_name': username,
        'sales_from_date': sales_from_date,
        'sales_to_date': sales_to_date,
        'org_id': org_id,
        'status': 'PENDING',
        'creation_date': datetime.datetime.now()
    }

    with st.expander("Debug: Database Parameters"):
        st.write(params)

    if st.button('Insert into Oracle DB', key='insert_db_button'):
        try:
            db_username = os.getenv("ORACLE_USERNAME", "system")
            password = os.getenv("ORACLE_PASSWORD")
            host = os.getenv("ORACLE_HOST", "localhost")
            port = os.getenv("ORACLE_PORT", "1521")
            service = os.getenv("ORACLE_SERVICE", "xe")
            
            if not password:
                st.error("Oracle database password not found in environment variables!")
                return False
            
            dsn = f"{host}:{port}/{service}"
            
            st.write("Connection parameters:")
            st.write(f"User: {db_username}")
            st.write(f"DSN: {dsn}")
            
            try:
                conn = oracledb.connect(
                    user=db_username,
                    password=password,
                    dsn=dsn
                )
                st.success("✅ Connected to Oracle DB successfully!")
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
                return False
            
            try:
                cur = conn.cursor()
                cur.execute(insert_sql, params)
                conn.commit()
                cur.close()
                conn.close()
                st.success("✅ Receipt inserted into Oracle DB successfully!")
                
                st.markdown("### Receipt added to database")
                st.markdown(f"""
                    Receipt **{rcpt_no}** was successfully added with:
                    - Amount: **{amount} {params['rec_currency']}**
                    - Date: **{rcpt_date.strftime('%d-%b-%Y')}**
                    - Organization: **{org_id}**
                    - Header ID: **{header_id}**
                """)
                
                if user_role == "salesperson" and not st.session_state.get('approval_submitted', False):
                    with st.spinner("Submitting for manager approval..."):
                        approval_id = submit_for_approval(data, username)
                        if approval_id:
                            st.session_state.approval_submitted = True
                            st.success(f"✅ Receipt submitted for manager approval (ID: {approval_id})")
                        else:
                            st.error("❌ Failed to submit for approval. Please try again.")
                
                st.session_state.form_submitted = False
                st.session_state.show_db_submit = False
                st.session_state.last_receipt = None
                
                return True
            except Exception as e:
                st.error(f"❌ Insert failed: {str(e)}")
                st.error("Please check that the data you're trying to insert matches the requirements of the database.")
                if "unique constraint" in str(e).lower():
                    st.warning("A receipt with this number may already exist in the database.")
                return False
                
        except Exception as e:
            st.error(f"❌ Failed to insert into Oracle DB: {e}")
            st.error("Please check your Oracle connection settings and try again.")
            return False
    else:
        st.info("Please fill all required fields above and click the button to insert data.")
        return False

    return False


st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
    }
    .receipt-data {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .form-container {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .form-header {
        background-color: #00529b;
        color: white;
        padding: 0.8rem;
        border-radius: 5px 5px 0 0;
        margin-bottom: 1rem;
    }
    .label-text {
        font-weight: 500;
        margin-bottom: 0.3rem;
        color: #333;
    }
    .receipt-item {
        border-left: 4px solid #00529b;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #f9f9f9;
        border-radius: 5px;
    }
    .big-button {
        font-size: 1.2rem !important;
        padding: 0.8rem 1.5rem !important;
        margin: 1rem 0 !important;
    }
    .extraction-container {
        margin: 1.5rem 0;
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #00529b;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 1rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def extract_receipt_data(image):
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None
    
    base64_image = encode_image(image)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",  # Updated to use GPT-4o instead of gpt-4-vision-preview
        "messages": [
            {
                "role": "system",
                "content": """You are an expert at extracting banking deposit receipt information with extremely high accuracy.
                
I will provide an image of a banking deposit receipt. You must extract EXACTLY the following information with 100% accuracy:

1. Deposit Date (in DD/MM/YYYY format) - Pay careful attention to the date format. In UAE, dates are typically shown as DD/MM/YYYY.
2. Amount in AED - Extract the total deposit amount.
3. Bank Account Number - Extract the EXACT account number, preserving all dashes, spaces, or special formatting.
4. Bank Account Name - This is the NAME OF THE BANK (e.g., UNITED ARAB BANK), not the customer name.
5. Reference/Sequence Number - This may be labeled as "SEQUENCE", "REF NO", "TRANSACTION ID", etc.

VERY IMPORTANT INSTRUCTIONS:
- Look CAREFULLY at each digit and character to ensure 100% accuracy
- Bank Account Name should be the NAME OF THE BANK, not the customer/company name
- The company name (e.g. ALPHAMED GENERAL TRADING LLC) is the company making the deposit, NOT the bank account name
- Do NOT interpret or change date formats - extract exactly as shown on the receipt
- For partial or masked account numbers (e.g., with X's), preserve the format exactly
- Extract the text EXACTLY as shown - do not "correct" or change spelling/capitalization
- If any field is not found, use the value "Not mentioned"

Your response must be ONLY valid JSON with absolutely no markdown formatting, explanations, or other text.

Format the response using the following structure EXACTLY:
{
  "deposit_date": "DD/MM/YYYY",
  "amount_aed": "XX,XXX.XX",
  "bank_account_number": "XXXXXXXX",
  "bank_account_name": "NAME OF THE BANK",
  "reference_number": "XXXXXXX"
}"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the banking deposit information from this receipt image with 100% accuracy. Focus on the exact deposit date (DD/MM/YYYY format), amount in AED, bank account number, bank name (not company name), and reference/sequence number."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

# def create_manual_form(initial_data=None, auto_extracted=False):
#     if initial_data is None:
#         initial_data = {
#             "deposit_date": datetime.date.today(),
#             "amount_aed": 0.0,
#             "bank_account_number": "",
#             "bank_account_name": "",
#             "reference_number": "",
#             "sales_from_date": datetime.date.today() - datetime.timedelta(days=30),
#             "sales_to_date": datetime.date.today()
#         }
    
#     with st.container():
#         st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
#         # Header changes based on whether data was auto-extracted
#         if auto_extracted:
#             st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">AI-Extracted Receipt Details</h3></div>', unsafe_allow_html=True)
#             st.markdown('<div class="success-message"><strong>✅ Data automatically extracted!</strong><br>Please review and make any necessary corrections.</div>', unsafe_allow_html=True)
#         else:
#             st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">Receipt Details</h3></div>', unsafe_allow_html=True)
        
#         with st.form("receipt_form", clear_on_submit=False):  # Changed to not clear on submit
#             st.markdown('<p class="label-text">Deposit Date</p>', unsafe_allow_html=True)
#             deposit_date = st.date_input("", initial_data["deposit_date"], label_visibility="collapsed")
            
#             st.markdown('<p class="label-text">Amount (AED)</p>', unsafe_allow_html=True)
#             amount = st.number_input("", min_value=0.0, format="%.2f", value=initial_data["amount_aed"], label_visibility="collapsed")
            
#             # Find the bank in the list if it exists
#             bank_index = 0
#             if initial_data["bank_account_name"] in UAE_BANKS:
#                 bank_index = UAE_BANKS.index(initial_data["bank_account_name"])
#                 other_bank_name = ""
#             elif initial_data["bank_account_name"]:
#                 bank_index = UAE_BANKS.index("Other")
#                 other_bank_name = initial_data["bank_account_name"]
#             else:
#                 other_bank_name = ""
                
#             st.markdown('<p class="label-text">Bank Name</p>', unsafe_allow_html=True)
#             selected_bank = st.selectbox("", options=UAE_BANKS, index=bank_index, label_visibility="collapsed")
            
#             st.markdown('<p class="label-text">Bank Account Number</p>', unsafe_allow_html=True)
#             account_number = st.text_input("", value=initial_data["bank_account_number"], label_visibility="collapsed")
            
#             if selected_bank == "Other":
#                 st.markdown('<p class="label-text">Other Bank Name</p>', unsafe_allow_html=True)
#                 bank_name = st.text_input("Other Bank Name", value=other_bank_name, label_visibility="collapsed")
#             else:
#                 bank_name = selected_bank if selected_bank != "Select a Bank" else ""
            
#             st.markdown('<p class="label-text">Deposit Reference Number</p>', unsafe_allow_html=True)
#             reference = st.text_input("Ref", value=initial_data["reference_number"], label_visibility="collapsed")
            
#             st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
#             st.markdown('<p class="label-text">Sales Period</p>', unsafe_allow_html=True)
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 st.markdown('<p class="label-text">From Date</p>', unsafe_allow_html=True)
#                 from_date = st.date_input("From", initial_data["sales_from_date"], label_visibility="collapsed")
#             with col2:
#                 st.markdown('<p class="label-text">To Date</p>', unsafe_allow_html=True)
#                 to_date = st.date_input("To", initial_data["sales_to_date"], label_visibility="collapsed")
            
#             st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
            
#             # Only show file uploader if we're not in auto-extracted mode (as we already have the image)
#             uploaded_file = None
#             if not auto_extracted:
#                 st.markdown('<p class="label-text">Upload Proof of Deposit (Image or PDF)</p>', unsafe_allow_html=True)
#                 uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "pdf"], label_visibility="collapsed")
            
#             submit_label = "💾 Confirm & Save Receipt" if auto_extracted else "💾 Save Receipt"
#             submitted = st.form_submit_button(submit_label, use_container_width=True)
            
#             if submitted:
#                 if selected_bank == "Select a Bank" and not bank_name:
#                     st.error("Please select a bank or enter a custom bank name.")
#                     return None
                    
#                 if not account_number or not reference:
#                     st.error("Please fill in all required fields.")
#                     return None
                    
#                 if from_date > to_date:
#                     st.error("Sales From Date cannot be after Sales To Date.")
#                     return None
                
#                 receipt_data = {
#                     "deposit_date": deposit_date.strftime("%d/%m/%Y"),
#                     "amount_aed": amount,
#                     "bank_account_number": account_number,
#                     "bank_account_name": bank_name,
#                     "reference_number": reference,
#                     "sales_from_date": from_date.strftime("%d/%m/%Y"),
#                     "sales_to_date": to_date.strftime("%d/%m/%Y"),
#                     "created_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#                 }
                
#                 # If we are saving from auto-extraction, use the stored image
#                 if auto_extracted and st.session_state.uploaded_image_data is not None:
#                     receipt_data['attachment'] = st.session_state.uploaded_image_data
#                     receipt_data['attachment_type'] = st.session_state.uploaded_image_type
#                 # Otherwise use the uploaded file from the form
#                 elif uploaded_file is not None:
#                     receipt_data['attachment'] = uploaded_file.getvalue()
#                     receipt_data['attachment_type'] = uploaded_file.type
                
#                 # Add receipt to session state
#                 # st.session_state.receipts.append(receipt_data)
                
                
#                 # Insert into Oracle DB (show prompt for missing NOT NULL fields)
#                 st.session_state.receipts.append(receipt_data)
#                 st.success("Receipt saved successfully!")
#                 st.session_state.show_db_submit = True
#                 st.session_state.last_receipt = receipt_data
                
#                 # Clear the extracted data and image data
#                 st.session_state.extracted_data = None
#                 st.session_state.uploaded_image_data = None
#                 st.session_state.uploaded_image_type = None
                
#                 # Success message will now be shown outside the form
#                 st.rerun()
                    
#         st.markdown('</div>', unsafe_allow_html=True)
#         return None

if 'show_db_submit' not in st.session_state:
    st.session_state.show_db_submit = False
    
if 'last_receipt' not in st.session_state:
    st.session_state.last_receipt = None
    
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False


# def create_manual_form(initial_data=None, auto_extracted=False):
#     if initial_data is None:
#         initial_data = {
#             "deposit_date": datetime.date.today(),
#             "amount_aed": 0.0,
#             "bank_account_number": "",
#             "bank_account_name": "",
#             "reference_number": "",
#             "sales_from_date": datetime.date.today() - datetime.timedelta(days=30),
#             "sales_to_date": datetime.date.today()
#         }
    
#     with st.container():
#         st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
#         if auto_extracted:
#             st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">AI-Extracted Receipt Details</h3></div>', unsafe_allow_html=True)
#             st.markdown('<div class="success-message"><strong>✅ Data automatically extracted!</strong><br>Please review and make any necessary corrections.</div>', unsafe_allow_html=True)
#         else:
#             st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">Receipt Details</h3></div>', unsafe_allow_html=True)
        
#         if st.session_state.form_submitted and st.session_state.last_receipt is not None:
#             receipt = st.session_state.last_receipt
            
#             st.markdown('<div class="success-message"><strong>✅ Receipt saved successfully!</strong></div>', unsafe_allow_html=True)
            
#             st.markdown(f"""
#             <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px;">
#                 <p><strong>Deposit Date:</strong> {receipt['deposit_date']}</p>
#                 <p><strong>Amount:</strong> {receipt['amount_aed']} AED</p>
#                 <p><strong>Bank:</strong> {receipt['bank_account_name']}</p>
#                 <p><strong>Account:</strong> {receipt['bank_account_number']}</p>
#                 <p><strong>Reference:</strong> {receipt['reference_number']}</p>
#                 <p><strong>Sales Period: Enter Manually Please</strong> {receipt['sales_from_date']} to {receipt['sales_to_date']}</p>
#             </div>
#             """, unsafe_allow_html=True)
            
#             st.markdown("""
#             <div style="padding: 15px; border-radius: 5px; background-color: #f0f7ff; border-left: 4px solid #0066cc; margin-bottom: 20px;">
#                 <h4 style="margin-top: 0;">Would you like to submit this receipt to the database?</h4>
#             </div>
#             """, unsafe_allow_html=True)
            
#             col1, col2 = st.columns(2)
#             with col1:
#                 if st.button("📥 Submit to Oracle Database", type="primary", use_container_width=True):
#                     receipt_data = st.session_state.last_receipt
                    
#                     db_username = os.getenv("ORACLE_USERNAME", "system")

#                     password = os.getenv("ORACLE_PASSWORD")
#                     host = os.getenv("ORACLE_HOST", "localhost")
#                     port = os.getenv("ORACLE_PORT", "1521")
#                     service = os.getenv("ORACLE_SERVICE", "xe")
                    
#                     if not password:
#                         st.error("Oracle database password not found in environment variables!")
#                         return False
                    
#                     dsn = f"{host}:{port}/{service}"
                    
#                     status_container = st.empty()
#                     status_container.info("Processing database insert...")
                    
#                     with st.expander("Debug Data"):
#                         st.write("Receipt data:", receipt_data)
                    
#                     try:
#                         rcpt_no = str(receipt_data.get('reference_number', ''))
                        
#                         try:
#                             rcpt_date_str = receipt_data.get('deposit_date', '')
#                             rcpt_date = datetime.datetime.strptime(rcpt_date_str, "%d/%m/%Y")
#                         except Exception as e:
#                             st.warning(f"Date parsing error: {e}. Using current date.")
#                             rcpt_date = datetime.datetime.now()
                        
#                         try:
#                             amount_raw = receipt_data.get('amount_aed', 0)
#                             if isinstance(amount_raw, (int, float)):
#                                 amount = float(amount_raw)
#                             else:
#                                 amount_str = str(amount_raw).replace(',', '').strip()
#                                 amount = float(amount_str) if amount_str else 0.0
#                         except Exception as e:
#                             st.warning(f"Amount conversion error: {e}. Using 0.")
#                             amount = 0.0
                        
#                         try:
#                             org_id_raw = os.getenv("DEFAULT_ORGANIZATION_ID", "1")
#                             organization_id = int(float(org_id_raw))  
#                         except Exception as e:
#                             st.warning(f"Organization ID conversion error: {e}. Using 1.")
#                             organization_id = 1
                            
#                         conn = oracledb.connect(
#                             user=db_username,
#                             password=password,
#                             dsn=dsn
#                         )
                        
#                         cur = conn.cursor()
                        
#                         insert_sql = '''
#                             INSERT INTO XAKI_AR_CASH_REC_AI_H (
#                                 HEADER_ID, REC_SOURCE, REC_COLLECTION_MOD, REC_AMOUNT, REC_DATE, 
#                                 REC_CURRENCY, REC_BANK_NAME, REC_BANK_ACCT_NUM, REC_REF_NUMBER, 
#                                 REC_USER_NAME, SALES_FROM_DATE, SALES_TO_DATE, ORG_ID, STATUS, 
#                                 CREATION_DATE
#                             ) VALUES (
#                                 :header_id, :rec_source, :rec_collection_mod, :rec_amount, :rec_date,
#                                 :rec_currency, :rec_bank_name, :rec_bank_acct_num, :rec_ref_number,
#                                 :rec_user_name, :sales_from_date, :sales_to_date, :org_id, :status,
#                                 :creation_date
#                             )
#                         '''
                        
#                         # params = {
#                         #     'rcpt_no': rcpt_no,
#                         #     'rcpt_date': rcpt_date,
#                         #     'organization_id': organization_id,
#                         #     'receipt_source': 'BANK',
#                         #     'collection_mode': 'CASH',
#                         #     'cur_code': 'AED',
#                         #     'amount': amount
#                         # }
                        
#                         with st.expander("Database Parameters"):
#                             st.write(params)
                        
#                         cur.execute(insert_sql, params)
#                         conn.commit()
#                         cur.close()
#                         conn.close()
                        
#                         status_container.success(f"✅ Receipt {rcpt_no} successfully inserted into database!")
                        
#                         st.session_state.receipt_submitted = True
                        
#                     except Exception as e:
#                         error_msg = str(e)
#                         status_container.error(f"❌ Database error: {error_msg}")
                        
#                         if "ORA-01722" in error_msg:
#                             st.error("This error typically happens when the database expected a number but received text.")
#                             st.write("Debug information:")
#                             st.write("- Amount value:", receipt_data.get('amount_aed'))
#                             st.write("- Organization ID:", os.getenv("DEFAULT_ORGANIZATION_ID", "1"))

                        
                        
#                     except Exception as e:
#                         status_container.error(f"❌ Database error: {str(e)}")
                    
#             with col2:
#                 if st.button("➕ Add Another Receipt", use_container_width=True):
#                     st.session_state.form_submitted = False
#                     st.session_state.show_db_submit = False
#                     st.session_state.last_receipt = None
#                     st.session_state.receipt_submitted = False
#                     st.session_state.extracted_data = None
#                     st.rerun()
                    
#             if st.session_state.get('receipt_submitted', False):
#                 st.success("This receipt has been submitted to the database.")
            
#         else:
#             with st.form("receipt_form", clear_on_submit=False):
#                 st.markdown('<p class="label-text">Deposit Date</p>', unsafe_allow_html=True)
#                 deposit_date = st.date_input("", initial_data["deposit_date"], label_visibility="collapsed")
                
#                 st.markdown('<p class="label-text">Amount (AED)</p>', unsafe_allow_html=True)
#                 amount = st.number_input("", min_value=0.0, format="%.2f", value=initial_data["amount_aed"], label_visibility="collapsed")
                
#                 bank_index = 0
#                 if initial_data["bank_account_name"] in UAE_BANKS:
#                     bank_index = UAE_BANKS.index(initial_data["bank_account_name"])
#                     other_bank_name = ""
#                 elif initial_data["bank_account_name"]:
#                     bank_index = UAE_BANKS.index("Other")
#                     other_bank_name = initial_data["bank_account_name"]
#                 else:
#                     other_bank_name = ""
                    
#                 st.markdown('<p class="label-text">Bank Name</p>', unsafe_allow_html=True)
#                 selected_bank = st.selectbox("", options=UAE_BANKS, index=bank_index, label_visibility="collapsed")
                
#                 st.markdown('<p class="label-text">Bank Account Number</p>', unsafe_allow_html=True)
#                 account_number = st.text_input("", value=initial_data["bank_account_number"], label_visibility="collapsed")
                
#                 if selected_bank == "Other":
#                     st.markdown('<p class="label-text">Other Bank Name</p>', unsafe_allow_html=True)
#                     bank_name = st.text_input("Other Bank Name", value=other_bank_name, label_visibility="collapsed")
#                 else:
#                     bank_name = selected_bank if selected_bank != "Select a Bank" else ""
                
#                 st.markdown('<p class="label-text">Deposit Reference Number</p>', unsafe_allow_html=True)
#                 reference = st.text_input("Ref", value=initial_data["reference_number"], label_visibility="collapsed")
                
#                 st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
#                 st.markdown('<p class="label-text">Sales Period</p>', unsafe_allow_html=True)
                
#                 col1, col2 = st.columns(2)
#                 with col1:
#                     st.markdown('<p class="label-text">From Date</p>', unsafe_allow_html=True)
#                     from_date = st.date_input("From", initial_data["sales_from_date"], label_visibility="collapsed")
#                 with col2:
#                     st.markdown('<p class="label-text">To Date</p>', unsafe_allow_html=True)
#                     to_date = st.date_input("To", initial_data["sales_to_date"], label_visibility="collapsed")
                
#                 st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
                
#                 uploaded_file = None
#                 if not auto_extracted:
#                     st.markdown('<p class="label-text">Upload Proof of Deposit (Image or PDF)</p>', unsafe_allow_html=True)
#                     uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "pdf"], label_visibility="collapsed")
                
#                 submit_label = "💾 Confirm & Save Receipt" if auto_extracted else "💾 Save Receipt"
#                 submitted = st.form_submit_button(submit_label, use_container_width=True)
                
#                 if submitted:
#                     is_duplicate, duplicate_source = check_duplicate_receipt(reference)
#                     if is_duplicate:
#                         # If it's a duplicate in Oracle DB but the check is disabled, proceed anyway
#                         if duplicate_source == "Oracle database" and not check_oracle_db:
#                             st.warning(f"Note: A receipt with reference number '{reference}' might exist in the Oracle database.")
#                             is_duplicate = False
#                         else:
#                             st.error(f"❌ Duplicate Receipt: A receipt with reference number '{reference}' already exists in {duplicate_source}.")
#                             return None
                    
#                     if selected_bank == "Select a Bank" and not bank_name:
#                         st.error("Please select a bank or enter a custom bank name.")
#                         return None
                        
#                     if not account_number or not reference:
#                         st.error("Please fill in all required fields.")
#                         return None
                        
#                     if from_date > to_date:
#                         st.error("Sales From Date cannot be after Sales To Date.")
#                         return None
                    
#                     receipt_data = {
#                         "deposit_date": deposit_date.strftime("%d/%m/%Y"),
#                         "amount_aed": amount,
#                         "bank_account_number": account_number,
#                         "bank_account_name": bank_name,
#                         "reference_number": reference,
#                         "sales_from_date": from_date.strftime("%d/%m/%Y"),
#                         "sales_to_date": to_date.strftime("%d/%m/%Y"),
#                         "created_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#                     }
                    
#                     if auto_extracted and st.session_state.uploaded_image_data is not None:
#                         receipt_data['attachment'] = st.session_state.uploaded_image_data
#                         receipt_data['attachment_type'] = st.session_state.uploaded_image_type
#                     elif uploaded_file is not None:
#                         receipt_data['attachment'] = uploaded_file.getvalue()
#                         receipt_data['attachment_type'] = uploaded_file.type

                    
                    
#                     st.session_state.receipts.append(receipt_data)
#                     st.session_state.last_receipt = receipt_data
#                     st.session_state.form_submitted = True

#                     if user_role == "salesperson":
#                         with st.spinner("Submitting for manager approval..."):
#                             approval_id = submit_for_approval(receipt_data, username)
#                             if approval_id:
#                                 st.session_state.approval_submitted = True
#                                 st.success(f"Receipt submitted for manager approval (ID: {approval_id})")
#                             else:
#                                 st.error("Failed to submit for approval. Please try again.")
            
                    
#                     st.rerun()
                        
#         st.markdown('</div>', unsafe_allow_html=True)
#         return None
    

def create_manual_form(initial_data=None, auto_extracted=False):
    if initial_data is None:
        initial_data = {
            "deposit_date": datetime.date.today(),
            "amount_aed": 0.0,
            "bank_account_number": "",
            "bank_account_name": "",
            "reference_number": "",
            "sales_from_date": datetime.date.today() - datetime.timedelta(days=30),
            "sales_to_date": datetime.date.today()
        }
    
    with st.container():
        st.markdown('<div class="form-container">', unsafe_allow_html=True)
        
        if auto_extracted:
            st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">AI-Extracted Receipt Details</h3></div>', unsafe_allow_html=True)
            st.markdown('<div class="success-message"><strong>✅ Data automatically extracted!</strong><br>Please review and make any necessary corrections.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">Receipt Details</h3></div>', unsafe_allow_html=True)
        
        if st.session_state.form_submitted and st.session_state.last_receipt is not None:
            receipt = st.session_state.last_receipt
            
            st.markdown('<div class="success-message"><strong>✅ Receipt saved successfully!</strong></div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px;">
                <p><strong>Deposit Date:</strong> {receipt['deposit_date']}</p>
                <p><strong>Amount:</strong> {receipt['amount_aed']} AED</p>
                <p><strong>Bank:</strong> {receipt['bank_account_name']}</p>
                <p><strong>Account:</strong> {receipt['bank_account_number']}</p>
                <p><strong>Reference:</strong> {receipt['reference_number']}</p>
                <p><strong>Sales Period:</strong> {receipt['sales_from_date']} to {receipt['sales_to_date']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="padding: 15px; border-radius: 5px; background-color: #f0f7ff; border-left: 4px solid #0066cc; margin-bottom: 20px;">
                <h4 style="margin-top: 0;">Would you like to submit this receipt to the database?</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Submit to Oracle Database", type="primary", use_container_width=True):
                    receipt_data = st.session_state.last_receipt
                    
                    db_username = os.getenv("ORACLE_USERNAME", "system")
                    password = os.getenv("ORACLE_PASSWORD")
                    host = os.getenv("ORACLE_HOST", "localhost")
                    port = os.getenv("ORACLE_PORT", "1521")
                    service = os.getenv("ORACLE_SERVICE", "xe")
                    
                    if not password:
                        st.error("Oracle database password not found in environment variables!")
                        return False
                    
                    dsn = f"{host}:{port}/{service}"
                    
                    status_container = st.empty()
                    status_container.info("Processing database insert...")
                    
                    with st.expander("Debug Data"):
                        st.write("Receipt data:", receipt_data)
                    
                    try:
                        rcpt_no = str(receipt_data.get('reference_number', ''))
                        
                        # Parse receipt date
                        try:
                            rcpt_date_str = receipt_data.get('deposit_date', '')
                            rcpt_date = datetime.datetime.strptime(rcpt_date_str, "%d/%m/%Y")
                        except Exception as e:
                            st.warning(f"Date parsing error: {e}. Using current date.")
                            rcpt_date = datetime.datetime.now()
                        
                        # Parse sales dates
                        try:
                            sales_from_str = receipt_data.get('sales_from_date', '')
                            sales_from_date = datetime.datetime.strptime(sales_from_str, "%d/%m/%Y")
                        except Exception:
                            sales_from_date = datetime.datetime.now() - datetime.timedelta(days=30)
                        
                        try:
                            sales_to_str = receipt_data.get('sales_to_date', '')
                            sales_to_date = datetime.datetime.strptime(sales_to_str, "%d/%m/%Y")
                        except Exception:
                            sales_to_date = datetime.datetime.now()
                        
                        # Parse amount
                        try:
                            amount_raw = receipt_data.get('amount_aed', 0)
                            if isinstance(amount_raw, (int, float)):
                                amount = float(amount_raw)
                            else:
                                amount_str = str(amount_raw).replace(',', '').strip()
                                amount = float(amount_str) if amount_str else 0.0
                        except Exception as e:
                            st.warning(f"Amount conversion error: {e}. Using 0.")
                            amount = 0.0
                        
                        # Get organization ID
                        try:
                            org_id_raw = os.getenv("DEFAULT_ORGANIZATION_ID", "1")
                            organization_id = int(float(org_id_raw))  
                        except Exception as e:
                            st.warning(f"Organization ID conversion error: {e}. Using 1.")
                            organization_id = 1
                        
                        # Generate header ID using timestamp
                        # header_id = int(datetime.datetime.now().timestamp())
                        header_id = "1234567890"
                            
                        conn = oracledb.connect(
                            user=db_username,
                            password=password,
                            dsn=dsn
                        )
                        
                        cur = conn.cursor()
                        
                        # Updated SQL for new table structure
                        insert_sql = '''
                            INSERT INTO XAKI_AR_CASH_REC_AI_H (
                                HEADER_ID, REC_SOURCE, REC_COLLECTION_MOD, REC_AMOUNT, REC_DATE, 
                                REC_CURRENCY, REC_BANK_NAME, REC_BANK_ACCT_NUM, REC_REF_NUMBER, 
                                REC_USER_NAME, SALES_FROM_DATE, SALES_TO_DATE, ORG_ID, STATUS, 
                                CREATION_DATE
                            ) VALUES (
                                :header_id, :rec_source, :rec_collection_mod, :rec_amount, :rec_date,
                                :rec_currency, :rec_bank_name, :rec_bank_acct_num, :rec_ref_number,
                                :rec_user_name, :sales_from_date, :sales_to_date, :org_id, :status,
                                :creation_date
                            )
                        '''
                        
                        params = {
                            'header_id': header_id,
                            'rec_source': 'CRAI',
                            'rec_collection_mod': 'CASH',
                            'rec_amount': amount,
                            'rec_date': rcpt_date,
                            'rec_currency': 'AED',
                            'rec_bank_name': receipt_data.get('bank_account_name', ''),
                            'rec_bank_acct_num': receipt_data.get('bank_account_number', ''),
                            'rec_ref_number': rcpt_no,
                            'rec_user_name': username,
                            'sales_from_date': sales_from_date,
                            'sales_to_date': sales_to_date,
                            'org_id': organization_id,
                            'status': 'False', 
                            'creation_date': datetime.datetime.now()
                        }
                        
                        with st.expander("Database Parameters"):
                            st.write(params)
                        
                        cur.execute(insert_sql, params)
                        conn.commit()
                        cur.close()
                        conn.close()
                        
                        status_container.success(f"✅ Receipt {rcpt_no} successfully inserted into database!")
                        
                        st.session_state.receipt_submitted = True
                        
                    except Exception as e:
                        error_msg = str(e)
                        status_container.error(f"❌ Database error: {error_msg}")
                        
                        if "ORA-01722" in error_msg:
                            st.error("This error typically happens when the database expected a number but received text.")
                            st.write("Debug information:")
                            st.write("- Amount value:", receipt_data.get('amount_aed'))
                            st.write("- Organization ID:", os.getenv("DEFAULT_ORGANIZATION_ID", "1"))
                    
            with col2:
                if st.button("➕ Add Another Receipt", use_container_width=True):
                    st.session_state.form_submitted = False
                    st.session_state.show_db_submit = False
                    st.session_state.last_receipt = None
                    st.session_state.receipt_submitted = False
                    st.session_state.extracted_data = None
                    st.rerun()
                    
            if st.session_state.get('receipt_submitted', False):
                st.success("This receipt has been submitted to the database.")
            
        else:
            with st.form("receipt_form", clear_on_submit=False):
                st.markdown('<p class="label-text">Deposit Date</p>', unsafe_allow_html=True)
                deposit_date = st.date_input("", initial_data["deposit_date"], label_visibility="collapsed")
                
                st.markdown('<p class="label-text">Amount (AED)</p>', unsafe_allow_html=True)
                amount = st.number_input("", min_value=0.0, format="%.2f", value=initial_data["amount_aed"], label_visibility="collapsed")
                
                bank_index = 0
                if initial_data["bank_account_name"] in UAE_BANKS:
                    bank_index = UAE_BANKS.index(initial_data["bank_account_name"])
                    other_bank_name = ""
                elif initial_data["bank_account_name"]:
                    bank_index = UAE_BANKS.index("Other")
                    other_bank_name = initial_data["bank_account_name"]
                else:
                    other_bank_name = ""
                    
                st.markdown('<p class="label-text">Bank Name</p>', unsafe_allow_html=True)
                selected_bank = st.selectbox("", options=UAE_BANKS, index=bank_index, label_visibility="collapsed")
                
                st.markdown('<p class="label-text">Bank Account Number</p>', unsafe_allow_html=True)
                account_number = st.text_input("", value=initial_data["bank_account_number"], label_visibility="collapsed")
                
                if selected_bank == "Other":
                    st.markdown('<p class="label-text">Other Bank Name</p>', unsafe_allow_html=True)
                    bank_name = st.text_input("Other Bank Name", value=other_bank_name, label_visibility="collapsed")
                else:
                    bank_name = selected_bank if selected_bank != "Select a Bank" else ""
                
                st.markdown('<p class="label-text">Deposit Reference Number</p>', unsafe_allow_html=True)
                reference = st.text_input("Ref", value=initial_data["reference_number"], label_visibility="collapsed")
                
                st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
                st.markdown('<p class="label-text">Sales Period</p>', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<p class="label-text">From Date</p>', unsafe_allow_html=True)
                    from_date = st.date_input("From", initial_data["sales_from_date"], label_visibility="collapsed")
                with col2:
                    st.markdown('<p class="label-text">To Date</p>', unsafe_allow_html=True)
                    to_date = st.date_input("To", initial_data["sales_to_date"], label_visibility="collapsed")
                
                st.markdown('<div style="margin: 1.5rem 0;"><hr style="border-top: 1px solid #eee;"></div>', unsafe_allow_html=True)
                
                uploaded_file = None
                if not auto_extracted:
                    st.markdown('<p class="label-text">Upload Proof of Deposit (Image or PDF)</p>', unsafe_allow_html=True)
                    uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "pdf"], label_visibility="collapsed")
                
                submit_label = "💾 Confirm & Save Receipt" if auto_extracted else "💾 Save Receipt"
                submitted = st.form_submit_button(submit_label, use_container_width=True)
                
                if submitted:
                    # Check for duplicates
                    is_duplicate, duplicate_source = check_duplicate_receipt(reference)
                    if is_duplicate:
                        st.error(f"❌ Duplicate Receipt: A receipt with reference number '{reference}' already exists in {duplicate_source}.")
                        return None
                    
                    if selected_bank == "Select a Bank" and not bank_name:
                        st.error("Please select a bank or enter a custom bank name.")
                        return None
                        
                    if not account_number or not reference:
                        st.error("Please fill in all required fields.")
                        return None
                        
                    if from_date > to_date:
                        st.error("Sales From Date cannot be after Sales To Date.")
                        return None
                    
                    receipt_data = {
                        "deposit_date": deposit_date.strftime("%d/%m/%Y"),
                        "amount_aed": amount,
                        "bank_account_number": account_number,
                        "bank_account_name": bank_name,
                        "reference_number": reference,
                        "sales_from_date": from_date.strftime("%d/%m/%Y"),
                        "sales_to_date": to_date.strftime("%d/%m/%Y"),
                        "created_at": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    }
                    
                    if auto_extracted and st.session_state.uploaded_image_data is not None:
                        receipt_data['attachment'] = st.session_state.uploaded_image_data
                        receipt_data['attachment_type'] = st.session_state.uploaded_image_type
                    elif uploaded_file is not None:
                        receipt_data['attachment'] = uploaded_file.getvalue()
                        receipt_data['attachment_type'] = uploaded_file.type
                    
                    st.session_state.receipts.append(receipt_data)
                    st.session_state.last_receipt = receipt_data
                    st.session_state.form_submitted = True

                    if user_role == "salesperson":
                        with st.spinner("Submitting for manager approval..."):
                            approval_id = submit_for_approval(receipt_data, username)
                            if approval_id:
                                st.session_state.approval_submitted = True
                                st.success(f"Receipt submitted for manager approval (ID: {approval_id})")
                            else:
                                st.error("Failed to submit for approval. Please try again.")
                    
                    st.rerun()
                        
        st.markdown('</div>', unsafe_allow_html=True)
        return None

def display_previous_receipts():
    if not st.session_state.receipts:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 1rem; background-color: #f9f9f9; border-radius: 10px; margin: 1rem 0;">
            <img src="https://img.icons8.com/fluency/96/document.png" style="width: 64px; margin-bottom: 1rem;">
            <h3>No receipts yet</h3>
            <p style="color: #666;">Upload a receipt image or take a photo to get started.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader(f"You have {len(st.session_state.receipts)} saved receipt(s)")
        for receipt in st.session_state.receipts:
            with st.expander(f"📝 {receipt['deposit_date']} | {receipt['amount_aed']} AED | Ref: {receipt['reference_number']}"):
                st.markdown('<div class="receipt-item">', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<p style="font-weight: 500; color: #666;">Bank Account:</p>', unsafe_allow_html=True)
                    st.markdown('<p style="font-weight: 500; color: #666;">Deposit Reference:</p>', unsafe_allow_html=True)
                    st.markdown('<p style="font-weight: 500; color: #666;">Sales Period - Enter Manually Please:</p>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<p style="font-weight: 400;">{receipt["bank_account_name"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="font-weight: 400;">{receipt["reference_number"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="font-weight: 400;">{receipt["sales_from_date"]} to {receipt["sales_to_date"]}</p>', unsafe_allow_html=True)
                
                if 'attachment' in receipt and 'attachment_type' in receipt:
                    st.markdown('<p style="font-weight: 500; color: #666; margin-top: 1rem;">Attachment:</p>', unsafe_allow_html=True)
                    if receipt['attachment_type'].startswith('image'):
                        st.image(Image.open(io.BytesIO(receipt['attachment'])),width=None)
                    elif receipt['attachment_type'] == 'application/pdf':
                        b64_pdf = base64.b64encode(receipt['attachment']).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

if 'uploaded_image_data' not in st.session_state:
    st.session_state.uploaded_image_data = None
    
if 'uploaded_image_type' not in st.session_state:
    st.session_state.uploaded_image_type = None


st.title("Banking Deposit Receipt Extractor for AKI")
st.markdown("📷 Take a picture of your deposit receipt and let AI extract the key information")

if st.session_state.db_connection_status == "connected":
    st.sidebar.success("✅ Connected to AKI Oracle Database")
elif st.session_state.db_connection_status is not None:
    st.sidebar.error(f"❌ Database Disconnected: {st.session_state.db_connection_status.split(':', 1)[1] if ':' in st.session_state.db_connection_status else 'Check configuration'}")
    if st.sidebar.button("🔄 Retry Connection"):
        check_db_connection()
        st.rerun()
else:
    st.sidebar.info("⏳ Checking database connection...")
    check_db_connection()
    st.rerun()


st.sidebar.markdown("---")
st.sidebar.markdown(f"Logged in as: **{username}**")
st.sidebar.markdown(f"Role: **{user_role.title()}**")
st.sidebar.markdown("### Debug Options")
check_oracle_db = st.sidebar.checkbox("Check Oracle DB for duplicates", value=False)
os.environ["CHECK_ORACLE_DB_DUPLICATES"] = "true" if check_oracle_db else "false"


# Add notifications badge 
notifications = get_notifications(username, user_role)
unread_count = sum(1 for n in notifications if not n.get("read", False))

if unread_count > 0:
    st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; margin-top: 10px;">
        <span>📫 Notifications</span>
        <span class="notification-badge">{unread_count}</span>
    </div>
    """, unsafe_allow_html=True)

if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_role = None
    st.rerun()

# tab1, tab2 = st.tabs(["📋 Previous Receipts", "➕ New Receipt"])

# tab1, tab2 = st.tabs(["📋 Previous Receipts", "➕ New Receipt"])
if user_role == "manager":
    # Show manager tabs - Approvals Dashboard and Receipt Processing
    app_tabs = st.tabs(["📊 Approvals Dashboard", "🧾 Receipt Processing"])
    
    with app_tabs[0]:
        render_manager_dashboard(username)
    
    with app_tabs[1]:
        # Inside the Receipt Processing tab, define the inner tabs
        tab1, tab2 = st.tabs(["📋 Previous Receipts", "➕ New Receipt"])
        
        with tab1:
            display_previous_receipts()
        
        with tab2:
            # Receipt upload code...
            st.subheader("Upload or Take a Receipt Photo")
            
            input_method = st.radio("Choose input method:", ["Upload Image", "Take Photo", "Manual Entry"])
            
            if st.session_state.extracted_data is not None:
                create_manual_form(st.session_state.extracted_data, auto_extracted=True)
            else:
                if input_method == "Manual Entry":
                    create_manual_form()
                else:
                    uploaded_image = None
                    
                    if input_method == "Upload Image":
                        uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "jpeg", "png"])
                        if uploaded_file is not None:
                            uploaded_image = Image.open(uploaded_file)
                            st.session_state.uploaded_image_data = uploaded_file.getvalue()
                            st.session_state.uploaded_image_type = uploaded_file.type
                            st.image(uploaded_image, caption="Uploaded Receipt", width=None)
                    
                    else:  # Take Photo
                        st.write("Please allow camera access to take a photo of your receipt.")
                        photo = st.camera_input("Take a picture")
                        if photo is not None:
                            uploaded_image = Image.open(photo)
                            st.session_state.uploaded_image_data = photo.getvalue()
                            st.session_state.uploaded_image_type = photo.type
                            st.image(uploaded_image, caption="Captured Receipt", width=None)
                    
                    if uploaded_image is not None:
                        if st.button("🔍 Extract Banking Information", type="primary", help="Use AI to automatically extract data from your receipt", use_container_width=True):
                            with st.spinner("Analyzing receipt..."):
                                progress_container = st.empty()
                                progress_container.markdown('<div class="extraction-container"><p>🤖 AI is analyzing your receipt...</p><div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div></div>', unsafe_allow_html=True)
                                
                                extracted_data_json = extract_receipt_data(uploaded_image)
                                
                                if extracted_data_json:
                                    try:
                                        cleaned_data = extracted_data_json
                                        if "```json" in cleaned_data:
                                            cleaned_data = cleaned_data.split("```json")[1].split("```")[0].strip()
                                        elif "```" in cleaned_data:
                                            cleaned_data = cleaned_data.split("```")[1].split("```")[0].strip()
                                        
                                        receipt_data = json.loads(cleaned_data)
                                        
                                        try:
                                            date_str = receipt_data.get("deposit_date", datetime.date.today().strftime("%d/%m/%Y"))
                                            date_formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]
                                            deposit_date = None
                                            
                                            for fmt in date_formats:
                                                try:
                                                    deposit_date = datetime.datetime.strptime(date_str, fmt).date()
                                                    break
                                                except ValueError:
                                                    continue
                                            
                                            if deposit_date is None:
                                                deposit_date = datetime.date.today()
                                                
                                            amount_str = receipt_data.get("amount_aed", "0")
                                            amount_str = amount_str.replace("AED", "").replace("Dhs", "").replace("د.إ", "").replace(",", "").replace(" ", "").strip()
                                            amount_str = ''.join([c for c in amount_str if c.isdigit() or c == '.'])
                                            
                                            amount_value = float(amount_str) if amount_str else 0.0
                                            
                                            initial_data = {
                                                "deposit_date": deposit_date,
                                                "amount_aed": amount_value,
                                                "bank_account_number": receipt_data.get("bank_account_number", ""),
                                                "bank_account_name": receipt_data.get("bank_account_name", ""),
                                                "reference_number": receipt_data.get("reference_number", ""),
                                                "sales_from_date": datetime.date.today() - datetime.timedelta(days=30),
                                                "sales_to_date": datetime.date.today()
                                            }
                                            
                                            st.session_state.extracted_data = initial_data
                                            
                                            progress_container.empty()
                                            
                                            st.success("✅ Data successfully extracted! Review the details below.")
                                            
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Error processing extracted data: {str(e)}")
                                            st.code(cleaned_data)
                                    
                                    except json.JSONDecodeError:
                                        st.error("Failed to parse the extracted data as JSON. Please try again with a clearer image.")
                                        st.code(extracted_data_json)
                                else:
                                    st.error("Failed to extract data from the receipt. Please try again with a clearer image or enter the details manually.")
                        
                        st.markdown("""
                        <div style="text-align: center; margin-top: 1rem;">
                            <p>Having trouble with automatic extraction?</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Enter Receipt Details Manually", use_container_width=True):
                            st.session_state.extracted_data = None
                            st.session_state.input_method = "Manual Entry"
                            st.rerun()

elif user_role == "salesperson":
    # Show salesperson tabs - My Receipts and New Receipt
    app_tabs = st.tabs(["📋 My Receipts", "➕ New Receipt"])
    
    with app_tabs[0]:
        render_salesperson_dashboard(username)
    
    with app_tabs[1]:
        # Inside the New Receipt tab, define the inner tabs
        tab1, tab2 = st.tabs(["📋 Previous Receipts", "➕ New Receipt"])
        
        with tab1:
            display_previous_receipts()
        
        with tab2:
            # Receipt upload code...
            st.subheader("Upload or Take a Receipt Photo")
            
            input_method = st.radio("Choose input method:", ["Upload Image", "Take Photo", "Manual Entry"])
            
            if st.session_state.extracted_data is not None:
                create_manual_form(st.session_state.extracted_data, auto_extracted=True)
            else:
                if input_method == "Manual Entry":
                    create_manual_form()
                else:
                    uploaded_image = None
                    
                    if input_method == "Upload Image":
                        uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "jpeg", "png"])
                        if uploaded_file is not None:
                            uploaded_image = Image.open(uploaded_file)
                            st.session_state.uploaded_image_data = uploaded_file.getvalue()
                            st.session_state.uploaded_image_type = uploaded_file.type
                            st.image(uploaded_image, caption="Uploaded Receipt", width=None)
                    
                    else:  # Take Photo
                        st.write("Please allow camera access to take a photo of your receipt.")
                        photo = st.camera_input("Take a picture")
                        if photo is not None:
                            uploaded_image = Image.open(photo)
                            st.session_state.uploaded_image_data = photo.getvalue()
                            st.session_state.uploaded_image_type = photo.type
                            st.image(uploaded_image, caption="Captured Receipt", width=None)
                    
                    if uploaded_image is not None:
                        if st.button("🔍 Extract Banking Information", type="primary", help="Use AI to automatically extract data from your receipt", use_container_width=True):
                            with st.spinner("Analyzing receipt..."):
                                progress_container = st.empty()
                                progress_container.markdown('<div class="extraction-container"><p>🤖 AI is analyzing your receipt...</p><div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div></div>', unsafe_allow_html=True)
                                
                                extracted_data_json = extract_receipt_data(uploaded_image)
                                
                                if extracted_data_json:
                                    try:
                                        cleaned_data = extracted_data_json
                                        if "```json" in cleaned_data:
                                            cleaned_data = cleaned_data.split("```json")[1].split("```")[0].strip()
                                        elif "```" in cleaned_data:
                                            cleaned_data = cleaned_data.split("```")[1].split("```")[0].strip()
                                        
                                        receipt_data = json.loads(cleaned_data)
                                        
                                        try:
                                            date_str = receipt_data.get("deposit_date", datetime.date.today().strftime("%d/%m/%Y"))
                                            date_formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]
                                            deposit_date = None
                                            
                                            for fmt in date_formats:
                                                try:
                                                    deposit_date = datetime.datetime.strptime(date_str, fmt).date()
                                                    break
                                                except ValueError:
                                                    continue
                                            
                                            if deposit_date is None:
                                                deposit_date = datetime.date.today()
                                                
                                            amount_str = receipt_data.get("amount_aed", "0")
                                            amount_str = amount_str.replace("AED", "").replace("Dhs", "").replace("د.إ", "").replace(",", "").replace(" ", "").strip()
                                            amount_str = ''.join([c for c in amount_str if c.isdigit() or c == '.'])
                                            
                                            amount_value = float(amount_str) if amount_str else 0.0
                                            
                                            initial_data = {
                                                "deposit_date": deposit_date,
                                                "amount_aed": amount_value,
                                                "bank_account_number": receipt_data.get("bank_account_number", ""),
                                                "bank_account_name": receipt_data.get("bank_account_name", ""),
                                                "reference_number": receipt_data.get("reference_number", ""),
                                                "sales_from_date": datetime.date.today() - datetime.timedelta(days=30),
                                                "sales_to_date": datetime.date.today()
                                            }
                                            
                                            st.session_state.extracted_data = initial_data
                                            
                                            progress_container.empty()
                                            
                                            st.success("✅ Data successfully extracted! Review the details below.")
                                            
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Error processing extracted data: {str(e)}")
                                            st.code(cleaned_data)
                                    
                                    except json.JSONDecodeError:
                                        st.error("Failed to parse the extracted data as JSON. Please try again with a clearer image.")
                                        st.code(extracted_data_json)
                                else:
                                    st.error("Failed to extract data from the receipt. Please try again with a clearer image or enter the details manually.")
                        
                        st.markdown("""
                        <div style="text-align: center; margin-top: 1rem;">
                            <p>Having trouble with automatic extraction?</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Enter Receipt Details Manually", use_container_width=True):
                            st.session_state.extracted_data = None
                            st.session_state.input_method = "Manual Entry"
                            st.rerun()

elif user_role == "uploader":
    # Show uploader dashboard
    render_uploader_dashboard(username)


# # Instructions and tips
# with st.expander("Tips for best results"):
#     st.markdown("""
#     - Ensure good lighting when taking a photo
#     - Keep the receipt flat and avoid wrinkles
#     - Verify all extracted information before saving
#     """)

# Footer
st.markdown("---")
st.markdown("Powered by AKI-GPT")

# def insert_receipt_to_oracle(data):
#     # Map your extracted data to the required columns
#     insert_sql = '''
#         INSERT INTO XXAKI_COLLECTIONS_EXT_STG (
#             RCPT_NO, RCPT_DATE, ORGANIZATION_ID, RECEIPT_SOURCE, COLLECTION_MODE, CUR_CODE, AMOUNT
#         ) VALUES (
#             :rcpt_no, :rcpt_date, :organization_id, :receipt_source, :collection_mode, :cur_code, :amount
#         )
#     '''
#     # Prompt for missing NOT NULL fields if not present
#     rcpt_no = data.get('reference_number') or st.text_input('Enter Receipt Number (RCPT_NO):', key='rcpt_no_input')
#     rcpt_date = data.get('deposit_date')
#     if isinstance(rcpt_date, str):
#         try:
#             rcpt_date = datetime.datetime.strptime(rcpt_date, "%d/%m/%Y")
#         except Exception:
#             rcpt_date = datetime.datetime.now()
#     organization_id = data.get('organization_id') or st.number_input('Enter Organization ID (ORGANIZATION_ID):', min_value=1, key='org_id_input')
#     receipt_source = data.get('receipt_source') or st.text_input('Enter Receipt Source (RECEIPT_SOURCE):', value='BANK', key='rcpt_source_input')
#     collection_mode = data.get('collection_mode') or st.text_input('Enter Collection Mode (COLLECTION_MODE):', value='CASH', key='coll_mode_input')
#     cur_code = data.get('cur_code') or st.text_input('Enter Currency Code (CUR_CODE):', value='AED', key='cur_code_input')
#     amount = data.get('amount_aed') or 0
#     try:
#         amount = float(amount)
#     except Exception:
#         amount = 0

#     params = {
#         'rcpt_no': rcpt_no,
#         'rcpt_date': rcpt_date,
#         'organization_id': organization_id,
#         'receipt_source': receipt_source,
#         'collection_mode': collection_mode,
#         'cur_code': cur_code,
#         'amount': amount
#     }

#     # Only show the insert button if all required fields are present
#     if all(params.values()):
#         if st.button('Insert into Oracle DB'):
#             try:
#                 conn = oracledb.connect(
#                     user='system',
#                     password=st.secrets["ORACLE_PASSWORD"] if "ORACLE_PASSWORD" in st.secrets else st.text_input('Oracle DB Password:', type='password', key='oracle_pw'),
#                     dsn='localhost:1521/xe'
#                 )
#                 cur = conn.cursor()
#                 cur.execute(insert_sql, params)
#                 conn.commit()
#                 cur.close()
#                 conn.close()
#                 st.success("Receipt inserted into Oracle DB successfully!")
#             except Exception as e:
#                 st.error(f"Failed to insert into Oracle DB: {e}")
#     else:
#         st.info("Please fill all required fields above to enable DB insertion.")


