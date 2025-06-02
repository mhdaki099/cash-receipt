import streamlit as st
import base64
import requests
import json
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Receipt Data Extractor",
    page_icon="🧾",
    layout="centered"
)

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
</style>
""", unsafe_allow_html=True)

# App title
st.title("Banking Deposit Receipt Extractor for AKI")
st.markdown("📷 Take a picture of your deposit receipt and let AI extract the key information")

# Add a demonstration section
st.markdown("### What This App Extracts")
st.markdown("""
This app focuses on extracting the following banking information:
- **Deposit Date** (DD/MM/YYYY format)
- **Amount in AED**
- **Bank Account Number**
- **Bank Account Name**
- **Reference/Sequence Number**

If any information is not found in the receipt, it will be marked as "Not mentioned".
""")

# Function to encode image to base64
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Function to extract data using OpenAI API
def extract_receipt_data(image):
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        st.error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return None
    
    # Encode the image
    base64_image = encode_image(image)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
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
  "amount_aed": "X,XXX.XX",
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
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

# Main app functionality
st.subheader("Upload or Take a Receipt Photo")

# Option to choose input method
input_method = st.radio("Choose input method:", ["Upload Image", "Take Photo"])

uploaded_image = None

if input_method == "Upload Image":
    uploaded_file = st.file_uploader("Choose a receipt image...", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file)
        st.image(uploaded_image, caption="Uploaded Receipt", use_container_width=True)

else:  # Take Photo
    st.write("Please allow camera access to take a photo of your receipt.")
    photo = st.camera_input("Take a picture")
    if photo is not None:
        uploaded_image = Image.open(photo)
        st.image(uploaded_image, caption="Captured Receipt", use_container_width=True)

# Process the image when the button is clicked
if uploaded_image is not None:
    if st.button("Extract Banking Information"):
        with st.spinner("Analyzing receipt..."):
            # Show processing message
            progress_text = st.empty()
            progress_text.text("Reading receipt content...")
            
            # Extract data using GPT-4o
            extracted_data = extract_receipt_data(uploaded_image)
            
            progress_text.text("Organizing results...")
            
            if extracted_data:
                # First display the raw result
                with st.expander("View Raw GPT-4o Response"):
                    st.code(extracted_data)
                
                try:
                    # Clean the input - sometimes GPT adds markdown code blocks or extra text
                    cleaned_data = extracted_data
                    # Remove any markdown code block formatting
                    if "```json" in cleaned_data:
                        cleaned_data = cleaned_data.split("```json")[1].split("```")[0].strip()
                    elif "```" in cleaned_data:
                        cleaned_data = cleaned_data.split("```")[1].split("```")[0].strip()
                    
                    # Parse the JSON data
                    receipt_data = json.loads(cleaned_data)
                    
                # Display the extracted data
                    st.subheader("Extracted Banking Information")
                    
                    # Create a formatted display
                    with st.container():
                        st.markdown('<div class="receipt-data">', unsafe_allow_html=True)
                        
                        # Display each field in a clear format
                        if "deposit_date" in receipt_data:
                            st.markdown(f"**Deposit Date:** {receipt_data['deposit_date']}")
                        
                        if "amount_aed" in receipt_data:
                            st.markdown(f"**Amount AED:** {receipt_data['amount_aed']}")
                        
                        if "bank_account_number" in receipt_data:
                            st.markdown(f"**Bank Account Number:** {receipt_data['bank_account_number']}")
                        
                        if "bank_account_name" in receipt_data:
                            st.markdown(f"**Bank Account Name:** {receipt_data['bank_account_name']}")
                        
                        if "reference_number" in receipt_data:
                            st.markdown(f"**Reference/Sequence Number:** {receipt_data['reference_number']}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Option to download as JSON
                    st.download_button(
                        label="Download Banking Data as JSON",
                        data=json.dumps(receipt_data, indent=4),
                        file_name="deposit_data.json",
                        mime="application/json",
                    )
                
                except json.JSONDecodeError:
                    st.error("Failed to parse the extracted data as JSON. Check the raw output above for more details.")
                    
                    # Let's try to help the user understand the problem
                    st.info("The AI response wasn't in the expected JSON format. This might happen due to:")
                    st.markdown("""
                    - Complex receipt layout that the AI struggled to interpret
                    - Poor image quality or lighting
                    - The AI provided explanations instead of just JSON
                    
                    Try again with a clearer image, or you can manually extract the data from the raw output.""")
            else:
                st.error("Failed to extract data from the receipt. Please try with a clearer image.")

# Instructions and tips
with st.expander("Tips for best results"):
    st.markdown("""
    - Ensure good lighting when taking a photo
    - Keep the receipt flat and avoid wrinkles
    - Make sure all text is visible and in focus
    - Include the entire receipt in the frame
    """)

# Footer
st.markdown("---")
st.markdown("Powered by AKI-GPT")
