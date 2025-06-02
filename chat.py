import streamlit as st
import base64
import requests
import json
from PIL import Image
import io
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize session state for receipts if not exists
if 'receipts' not in st.session_state:
    st.session_state.receipts = []

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# Set page configuration
st.set_page_config(
    page_title="Receipt Data Extractor",
    page_icon="🧾",
    layout="centered"
)

# UAE Banks list
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

# Add custom CSS
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

# Function to encode image to base64
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to extract data using OpenAI GPT-4o API
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

# Function to create manual entry form
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
        
        # Header changes based on whether data was auto-extracted
        if auto_extracted:
            st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">AI-Extracted Receipt Details</h3></div>', unsafe_allow_html=True)
            st.markdown('<div class="success-message"><strong>✅ Data automatically extracted!</strong><br>Please review and make any necessary corrections.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="form-header"><h3 style="margin: 0; text-align: center;">Receipt Details</h3></div>', unsafe_allow_html=True)
        
        with st.form("receipt_form", clear_on_submit=False):  # Changed to not clear on submit
            st.markdown('<p class="label-text">Deposit Date</p>', unsafe_allow_html=True)
            deposit_date = st.date_input("", initial_data["deposit_date"], label_visibility="collapsed")
            
            st.markdown('<p class="label-text">Amount (AED)</p>', unsafe_allow_html=True)
            amount = st.number_input("", min_value=0.0, format="%.2f", value=initial_data["amount_aed"], label_visibility="collapsed")
            
            # Find the bank in the list if it exists
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
            
            # Only show file uploader if we're not in auto-extracted mode (as we already have the image)
            uploaded_file = None
            if not auto_extracted:
                st.markdown('<p class="label-text">Upload Proof of Deposit (Image or PDF)</p>', unsafe_allow_html=True)
                uploaded_file = st.file_uploader("Choose a file", type=["jpg", "jpeg", "png", "pdf"], label_visibility="collapsed")
            
            submit_label = "💾 Confirm & Save Receipt" if auto_extracted else "💾 Save Receipt"
            submitted = st.form_submit_button(submit_label, use_container_width=True)
            
            if submitted:
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
                
                # If we are saving from auto-extraction, use the stored image
                if auto_extracted and st.session_state.uploaded_image_data is not None:
                    receipt_data['attachment'] = st.session_state.uploaded_image_data
                    receipt_data['attachment_type'] = st.session_state.uploaded_image_type
                # Otherwise use the uploaded file from the form
                elif uploaded_file is not None:
                    receipt_data['attachment'] = uploaded_file.getvalue()
                    receipt_data['attachment_type'] = uploaded_file.type
                
                # Add receipt to session state
                st.session_state.receipts.append(receipt_data)
                st.success("Receipt saved successfully!")
                
                # Clear the extracted data and image data
                st.session_state.extracted_data = None
                st.session_state.uploaded_image_data = None
                st.session_state.uploaded_image_type = None
                
                # Rerun to show updated UI
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        return None

# Function to display previous receipts
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
                    st.markdown('<p style="font-weight: 500; color: #666;">Sales Period:</p>', unsafe_allow_html=True)
                with col2:
                    st.markdown(f'<p style="font-weight: 400;">{receipt["bank_account_name"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="font-weight: 400;">{receipt["reference_number"]}</p>', unsafe_allow_html=True)
                    st.markdown(f'<p style="font-weight: 400;">{receipt["sales_from_date"]} to {receipt["sales_to_date"]}</p>', unsafe_allow_html=True)
                
                if 'attachment' in receipt and 'attachment_type' in receipt:
                    st.markdown('<p style="font-weight: 500; color: #666; margin-top: 1rem;">Attachment:</p>', unsafe_allow_html=True)
                    if receipt['attachment_type'].startswith('image'):
                        st.image(Image.open(io.BytesIO(receipt['attachment'])), use_container_width=True)
                    elif receipt['attachment_type'] == 'application/pdf':
                        b64_pdf = base64.b64encode(receipt['attachment']).decode('utf-8')
                        pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)

# Store uploaded image in session state
if 'uploaded_image_data' not in st.session_state:
    st.session_state.uploaded_image_data = None
    
if 'uploaded_image_type' not in st.session_state:
    st.session_state.uploaded_image_type = None

# Main app functionality
st.title("Banking Deposit Receipt Extractor")
st.markdown("📷 Take a picture of your deposit receipt and let AI extract the key information")

# Create tabs for different sections
tab1, tab2 = st.tabs(["📋 Previous Receipts", "➕ New Receipt"])

with tab1:
    display_previous_receipts()

with tab2:
    st.subheader("Upload or Take a Receipt Photo")
    
    # Option to choose input method - removed the "Manual Entry" option as default
    input_method = st.radio("Choose input method:", ["Upload Image", "Take Photo", "Manual Entry"])
    
    # If we have extracted data in the session state, show the form
    if st.session_state.extracted_data is not None:
        create_manual_form(st.session_state.extracted_data, auto_extracted=True)
    # Otherwise show the input method options
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
                    st.image(uploaded_image, caption="Uploaded Receipt", use_container_width=True)
            
            else:  # Take Photo
                st.write("Please allow camera access to take a photo of your receipt.")
                photo = st.camera_input("Take a picture")
                if photo is not None:
                    uploaded_image = Image.open(photo)
                    st.session_state.uploaded_image_data = photo.getvalue()
                    st.session_state.uploaded_image_type = photo.type
                    st.image(uploaded_image, caption="Captured Receipt", use_container_width=True)
            
            # Process the image automatically or with a button click
            if uploaded_image is not None:
                # Use a more prominent button for extraction
                if st.button("🔍 Extract Banking Information", type="primary", help="Use AI to automatically extract data from your receipt", use_container_width=True):
                    with st.spinner("Analyzing receipt..."):
                        # Show processing animation
                        progress_container = st.empty()
                        progress_container.markdown('<div class="extraction-container"><p>🤖 AI is analyzing your receipt...</p><div class="progress"><div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%"></div></div></div>', unsafe_allow_html=True)
                        
                        # Extract data using GPT-4o
                        extracted_data_json = extract_receipt_data(uploaded_image)
                        
                        if extracted_data_json:
                            try:
                                # Clean the input - sometimes GPT adds markdown code blocks or extra text
                                cleaned_data = extracted_data_json
                                # Remove any markdown code block formatting
                                if "```json" in cleaned_data:
                                    cleaned_data = cleaned_data.split("```json")[1].split("```")[0].strip()
                                elif "```" in cleaned_data:
                                    cleaned_data = cleaned_data.split("```")[1].split("```")[0].strip()
                                
                                # Parse the JSON data
                                receipt_data = json.loads(cleaned_data)
                                
                                # Convert the extracted data to the format expected by the form
                                try:
                                    # Handle different date formats
                                    date_str = receipt_data.get("deposit_date", datetime.date.today().strftime("%d/%m/%Y"))
                                    # Try different date formats
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
                                        
                                    # Handle amount formatting
                                    amount_str = receipt_data.get("amount_aed", "0")
                                    # Remove currency symbols, commas, and spaces
                                    amount_str = amount_str.replace("AED", "").replace("Dhs", "").replace("د.إ", "").replace(",", "").replace(" ", "").strip()
                                    # Extract just the numbers and decimal point
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
                                    
                                    # Store in session state and clear the progress container
                                    st.session_state.extracted_data = initial_data
                                    progress_container.empty()
                                    
                                    # Rerun to show the form with extracted data
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error processing extracted data: {str(e)}")
                                    st.code(cleaned_data)
                            
                            except json.JSONDecodeError:
                                st.error("Failed to parse the extracted data as JSON. Please try again with a clearer image.")
                                st.code(extracted_data_json)
                        else:
                            st.error("Failed to extract data from the receipt. Please try again with a clearer image or enter the details manually.")
                
                # Add a manual entry option as fallback
                st.markdown("""
                <div style="text-align: center; margin-top: 1rem;">
                    <p>Having trouble with automatic extraction?</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Enter Receipt Details Manually", use_container_width=True):
                    # Set input method to manual
                    st.session_state.extracted_data = None
                    st.session_state.input_method = "Manual Entry"
                    st.rerun()

# Instructions and tips
with st.expander("Tips for best results"):
    st.markdown("""
    - Ensure good lighting when taking a photo
    - Keep the receipt flat and avoid wrinkles
    - Make sure all text is visible and in focus
    - Include the entire receipt in the frame
    - Verify all extracted information before saving
    """)

# Footer
st.markdown("---")
st.markdown("Powered by AKI-GPT")