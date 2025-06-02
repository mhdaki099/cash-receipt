import streamlit as st
from PIL import Image
import io
import base64
from approval_system import (
    get_receipts_by_salesperson,
    get_notifications,
    mark_notification_read
)

def render_salesperson_dashboard(username):
    """Render the salesperson dashboard"""
    st.title("Salesperson Dashboard")
    st.subheader(f"Welcome, {username}")
    
    # Display notifications
    display_notifications(username, "salesperson")
    
    # Get user receipts
    user_receipts = get_receipts_by_salesperson(username)
    
    # Create metrics display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Approval", f"{len(user_receipts['pending'])} receipts", 
                 f"AED {sum(float(r.get('amount_aed', 0)) for r in user_receipts['pending']):.2f}")
    with col2:
        st.metric("Approved", f"{len(user_receipts['approved'])} receipts", 
                 f"AED {sum(float(r.get('amount_aed', 0)) for r in user_receipts['approved']):.2f}")
    with col3:
        st.metric("Rejected", f"{len(user_receipts['rejected'])} receipts", 
                 f"AED {sum(float(r.get('amount_aed', 0)) for r in user_receipts['rejected']):.2f}")
    
    # Create tabs for different receipt statuses
    tabs = st.tabs(["Pending Approval", "Approved", "Rejected"])
    
    # Pending Approvals Tab
    with tabs[0]:
        if not user_receipts['pending']:
            st.info("No receipts pending approval")
        else:
            st.write(f"### Receipts Pending Approval ({len(user_receipts['pending'])})")
            
            for receipt in user_receipts['pending']:
                render_receipt_card(receipt, "pending")
    
    # Approved Receipts Tab
    with tabs[1]:
        if not user_receipts['approved']:
            st.info("No approved receipts")
        else:
            st.write(f"### Approved Receipts ({len(user_receipts['approved'])})")
            
            for receipt in user_receipts['approved']:
                render_receipt_card(receipt, "approved")
    
    # Rejected Receipts Tab
    with tabs[2]:
        if not user_receipts['rejected']:
            st.info("No rejected receipts")
        else:
            st.write(f"### Rejected Receipts ({len(user_receipts['rejected'])})")
            
            for receipt in user_receipts['rejected']:
                render_receipt_card(receipt, "rejected")

# def render_receipt_card(receipt, status):
#     """Render a card for a receipt with appropriate styling based on status"""
#     status_colors = {
#         "pending": "#ffc107",  # Yellow
#         "approved": "#28a745", # Green
#         "rejected": "#dc3545"  # Red
#     }
#     color = status_colors.get(status, "#6c757d")  # Default gray
    
#     with st.container():
#         st.markdown(f"""
#         <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid {color};">
#             <h4>Receipt {receipt.get('approval_id', 'Unknown ID')}</h4>
#             <p><strong>Submitted on:</strong> {receipt.get('submission_date', 'Unknown')}</p>
#             <p><strong>Amount:</strong> AED {receipt.get('amount_aed', 0)}</p>
#             <p><strong>Reference:</strong> {receipt.get('reference_number', 'Unknown')}</p>
#             <p><strong>Bank:</strong> {receipt.get('bank_account_name', 'Unknown')}</p>
#             <p><strong>Status:</strong> <span style="color: {color}; font-weight: bold;">{status.upper()}</span></p>
#         """, unsafe_allow_html=True)
        
#         # Show approval/rejection details
#         if status == "approved":
#             st.markdown(f"""
#             <p><strong>Approved by:</strong> {receipt.get('approved_by', 'Unknown')}</p>
#             <p><strong>Approved on:</strong> {receipt.get('approval_date', 'Unknown')}</p>
#             """, unsafe_allow_html=True)
            
#             if receipt.get('approval_notes'):
#                 st.markdown(f"""
#                 <p><strong>Notes:</strong> {receipt.get('approval_notes')}</p>
#                 """, unsafe_allow_html=True)
                
#         elif status == "rejected":
#             st.markdown(f"""
#             <p><strong>Rejected by:</strong> {receipt.get('rejected_by', 'Unknown')}</p>
#             <p><strong>Rejected on:</strong> {receipt.get('rejection_date', 'Unknown')}</p>
#             <p><strong>Reason:</strong> {receipt.get('rejection_reason', 'No reason provided')}</p>
#             """, unsafe_allow_html=True)
            
#         st.markdown("</div>", unsafe_allow_html=True)
        
#         # Display receipt image if available
#         if 'attachment' in receipt and 'attachment_type' in receipt:
#             with st.expander("View Receipt Image"):
#                 try:
#                     if receipt['attachment_type'].startswith('image'):
#                         # Base64-encoded image
#                         image_data = receipt['attachment']
#                         if isinstance(image_data, str) and image_data.startswith('data:image'):
#                             # Extract base64 part from data URL
#                             image_data = image_data.split(',')[1]
                            
#                         # Convert to bytes and display
#                         if isinstance(image_data, str):
#                             image_bytes = base64.b64decode(image_data)
#                         else:
#                             image_bytes = image_data
                            
#                         image = Image.open(io.BytesIO(image_bytes))
#                         st.image(image, width=300)
#                     elif receipt['attachment_type'] == 'application/pdf':
#                         # PDF attachment - show download link
#                         pdf_data = receipt['attachment']
#                         if isinstance(pdf_data, str):
#                             pdf_bytes = base64.b64decode(pdf_data)
#                         else:
#                             pdf_bytes = pdf_data
                            
#                         st.download_button(
#                             "Download PDF Receipt",
#                             pdf_bytes,
#                             file_name=f"receipt_{receipt.get('reference_number', 'unknown')}.pdf",
#                             mime="application/pdf"
#                         )
#                 except Exception as e:
#                     st.warning(f"Could not display receipt image: {str(e)}")

def render_receipt_card(receipt, status):
    """Render a card for a receipt with appropriate styling based on status"""
    status_colors = {
        "pending": "#ffc107",  # Yellow
        "approved": "#28a745", # Green
        "rejected": "#dc3545"  # Red
    }
    color = status_colors.get(status, "#6c757d")  # Default gray
    
    with st.container():
        st.markdown(f"""
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid {color};">
            <h4>Receipt {receipt.get('approval_id', 'Unknown ID')}</h4>
            <p><strong>Submitted on:</strong> {receipt.get('submission_date', 'Unknown')}</p>
            <p><strong>Amount:</strong> AED {receipt.get('amount_aed', 0)}</p>
            <p><strong>Reference:</strong> {receipt.get('reference_number', 'Unknown')}</p>
            <p><strong>Bank:</strong> {receipt.get('bank_account_name', 'Unknown')}</p>
            <p><strong>Status:</strong> <span style="color: {color}; font-weight: bold;">{status.upper()}</span></p>
        """, unsafe_allow_html=True)
        
        # Show approval/rejection details
        if status == "approved":
            st.markdown(f"""
            <p><strong>Approved by:</strong> {receipt.get('approved_by', 'Unknown')}</p>
            <p><strong>Approved on:</strong> {receipt.get('approval_date', 'Unknown')}</p>
            """, unsafe_allow_html=True)
            
            if receipt.get('approval_notes'):
                st.markdown(f"""
                <p><strong>Notes:</strong> {receipt.get('approval_notes')}</p>
                """, unsafe_allow_html=True)
                
            # Display database match information if available
            if "database_match" in receipt:
                database_match = receipt.get("database_match", False)
                match_details = receipt.get("match_details", {})
                
                if database_match:
                    match_color = "#28a745"  # Green for match
                    st.markdown(f"""
                    <p style="color: {match_color};">✅ <strong>Database Match:</strong> This receipt matches with a transaction in our database</p>
                    """, unsafe_allow_html=True)
                    
                    # Show match details
                    if "matches" in match_details:
                        with st.expander("View Database Match Details"):
                            for idx, match in enumerate(match_details["matches"]):
                                st.markdown(f"""
                                <div style="padding: 10px; background-color: #e8f4e8; border-radius: 5px; margin-bottom: 10px;">
                                    <p><strong>Match Quality:</strong> {match.get('match_quality', 'Unknown')}</p>
                                    <p><strong>Date:</strong> {match.get('database_date', 'Unknown')}</p>
                                    <p><strong>Amount:</strong> AED {match.get('database_amount', 0)}</p>
                                    <p><strong>Reference:</strong> {match.get('database_reference', 'Unknown')}</p>
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    match_color = "#ffc107"  # Yellow for no match
                    st.markdown(f"""
                    <p style="color: {match_color};"><strong>⚠️ No Database Match:</strong> This receipt does not match any transaction in our database</p>
                    """, unsafe_allow_html=True)
                
        elif status == "rejected":
            st.markdown(f"""
            <p><strong>Rejected by:</strong> {receipt.get('rejected_by', 'Unknown')}</p>
            <p><strong>Rejected on:</strong> {receipt.get('rejection_date', 'Unknown')}</p>
            <p><strong>Reason:</strong> {receipt.get('rejection_reason', 'No reason provided')}</p>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display receipt image if available
        if 'attachment' in receipt and 'attachment_type' in receipt:
            with st.expander("View Receipt Image"):
                try:
                    if receipt['attachment_type'].startswith('image'):
                        # Base64-encoded image
                        image_data = receipt['attachment']
                        if isinstance(image_data, str) and image_data.startswith('data:image'):
                            # Extract base64 part from data URL
                            image_data = image_data.split(',')[1]
                            
                        # Convert to bytes and display
                        if isinstance(image_data, str):
                            image_bytes = base64.b64decode(image_data)
                        else:
                            image_bytes = image_data
                            
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, width=300)
                    elif receipt['attachment_type'] == 'application/pdf':
                        # PDF attachment - show download link
                        pdf_data = receipt['attachment']
                        if isinstance(pdf_data, str):
                            pdf_bytes = base64.b64decode(pdf_data)
                        else:
                            pdf_bytes = pdf_data
                            
                        st.download_button(
                            "Download PDF Receipt",
                            pdf_bytes,
                            file_name=f"receipt_{receipt.get('reference_number', 'unknown')}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.warning(f"Could not display receipt image: {str(e)}")

def display_notifications(username, user_type):
    """Display notifications for the user"""
    notifications = get_notifications(username, user_type)
    
    # Count unread notifications
    unread_count = sum(1 for n in notifications if not n.get("read", False))
    
    if unread_count > 0:
        with st.expander(f"📫 You have {unread_count} unread notifications"):
            for notification in notifications:
                if not notification.get("read", False):
                    st.markdown(f"""
                    <div style="padding: 10px; background-color: #e6f3ff; border-radius: 5px; margin-bottom: 10px;">
                        <p><strong>{notification.get('timestamp')}</strong></p>
                        <p>{notification.get('message')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Mark as Read", key=f"mark_read_{notification['id']}"):
                        mark_notification_read(notification['id'])
                        st.rerun()
    
    # Show all notifications in another expander
    if notifications:
        with st.expander("View All Notifications"):
            for notification in notifications:
                st.markdown(f"""
                <div style="padding: 10px; background-color: {'#f8f9fa' if notification.get('read', False) else '#e6f3ff'}; border-radius: 5px; margin-bottom: 10px;">
                    <p><strong>{notification.get('timestamp')}</strong> {' (Read)' if notification.get('read', False) else ''}</p>
                    <p>{notification.get('message')}</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    # For testing the salesperson dashboard directly
    st.session_state.username = "sales@akigroup.com"
    render_salesperson_dashboard(st.session_state.username)