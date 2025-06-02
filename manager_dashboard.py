import streamlit as st
from PIL import Image
import io
import base64
import datetime
import json
from pathlib import Path
from approval_system import (
    load_data, 
    get_receipt_stats, 
    approve_receipt,
    reject_receipt,
    get_notifications,
    mark_notification_read,
    PENDING_FILE,
    APPROVED_FILE,
    REJECTED_FILE
)

def render_manager_dashboard(username):
    """Render the manager dashboard"""
    st.title("Manager Dashboard")
    st.subheader(f"Welcome, {username}")
    
    # Display notifications
    display_notifications(username, "manager")
    
    # Get receipt statistics
    stats = get_receipt_stats()
    
    # Create metrics display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending Approval", f"{stats['pending_count']} receipts", f"AED {stats['pending_total']:.2f}")
    with col2:
        st.metric("Approved", f"{stats['approved_count']} receipts", f"AED {stats['approved_total']:.2f}")
    with col3:
        st.metric("Rejected", f"{stats['rejected_count']} receipts", f"AED {stats['rejected_total']:.2f}")
    
    # Create tabs for different receipt statuses
    tabs = st.tabs(["Pending Approval", "Approved", "Rejected"])
    
    # Load receipt data
    pending_receipts = load_data(PENDING_FILE)
    approved_receipts = load_data(APPROVED_FILE)
    rejected_receipts = load_data(REJECTED_FILE)
    
    # Pending Approvals Tab
    with tabs[0]:
        if not pending_receipts:
            st.info("No receipts pending approval")
        else:
            st.write(f"### Receipts Pending Approval ({len(pending_receipts)})")
            
            for receipt in pending_receipts:
                render_pending_receipt_card(receipt)
    
    # Approved Receipts Tab
    with tabs[1]:
        if not approved_receipts:
            st.info("No approved receipts")
        else:
            st.write(f"### Approved Receipts ({len(approved_receipts)})")
            
            for receipt in approved_receipts:
                render_receipt_card(receipt, "approved")
    
    # Rejected Receipts Tab
    with tabs[2]:
        if not rejected_receipts:
            st.info("No rejected receipts")
        else:
            st.write(f"### Rejected Receipts ({len(rejected_receipts)})")
            
            for receipt in rejected_receipts:
                render_receipt_card(receipt, "rejected")

def render_pending_receipt_card(receipt):
    """Render a card for a pending receipt with approval/rejection options"""
    with st.container():
        st.markdown(f"""
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
            <h4>Receipt {receipt.get('approval_id', 'Unknown ID')}</h4>
            <p><strong>Submitted by:</strong> {receipt.get('submitted_by', 'Unknown')}</p>
            <p><strong>Date:</strong> {receipt.get('submission_date', 'Unknown')}</p>
            <p><strong>Amount:</strong> AED {receipt.get('amount_aed', 0)}</p>
            <p><strong>Reference:</strong> {receipt.get('reference_number', 'Unknown')}</p>
            <p><strong>Bank:</strong> {receipt.get('bank_account_name', 'Unknown')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display receipt image if available
        if 'attachment' in receipt and 'attachment_type' in receipt:
            st.markdown("<strong>Receipt Image:</strong>", unsafe_allow_html=True)
            
            # Handle image data based on format
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
        
        # Approval/Rejection buttons
        col1, col2 = st.columns(2)
        
        # Create a unique key for this receipt
        receipt_id = receipt.get('approval_id', 'unknown')
        approve_key = f"approve_{receipt_id}"
        
        with col1:
            if st.button(f"✅ Approve", key=f"btn_{approve_key}"):
                # Set a session state flag for this receipt approval
                st.session_state[approve_key] = True
        
        # Check if this receipt needs approval
        if st.session_state.get(approve_key, False):
            with st.form(key=f"form_{approve_key}"):
                notes = st.text_area("Add approval notes (optional)")
                submitted = st.form_submit_button("Confirm Approval")
                
                if submitted:
                    success, message = approve_receipt(receipt_id, st.session_state.username, notes)
                    
                    if success:
                        st.success(message)
                        # Clear the flag
                        st.session_state[approve_key] = False
                        # Force a refresh
                        st.rerun()
                    else:
                        st.error(message)
        
        with col2:
            # Create unique keys for each receipt rejection flow
            reject_btn_key = f"reject_btn_{receipt.get('approval_id')}"
            reject_state_key = f"reject_state_{receipt.get('approval_id')}"
            
            # Initialize the state if not already present
            if reject_state_key not in st.session_state:
                st.session_state[reject_state_key] = False
            
            # Show the reject button only if we're not already in rejection mode
            if not st.session_state[reject_state_key]:
                if st.button(f"❌ Reject", key=reject_btn_key):
                    # Set the state to show the rejection form
                    st.session_state[reject_state_key] = True
                    st.rerun()  # Rerun to show the form
            
            # Show the rejection form if in rejection mode
            if st.session_state.get(reject_state_key, False):
                with st.form(key=f"reject_form_{receipt.get('approval_id')}"):
                    reason = st.text_area("Rejection reason (required)")
                    cancel, submit = st.columns(2)
                    
                    with cancel:
                        if st.form_submit_button("Cancel"):
                            st.session_state[reject_state_key] = False
                            st.rerun()
                    
                    with submit:
                        if st.form_submit_button("Confirm Rejection"):
                            if not reason:
                                st.error("Please provide a reason for rejection")
                            else:
                                success, message = reject_receipt(
                                    receipt.get('approval_id'), 
                                    st.session_state.username, 
                                    reason
                                )
                                
                                if success:
                                    st.session_state[reject_state_key] = False
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)

# def render_receipt_card(receipt, status):
#     """Render a card for an approved or rejected receipt"""
#     status_color = "#28a745" if status == "approved" else "#dc3545"
#     action_text = "Approved" if status == "approved" else "Rejected"
#     action_by = receipt.get('approved_by' if status == "approved" else 'rejected_by', 'Unknown')
#     action_date = receipt.get('approval_date' if status == "approved" else 'rejection_date', 'Unknown')
    
#     with st.container():
#         st.markdown(f"""
#         <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid {status_color};">
#             <h4>Receipt {receipt.get('approval_id', 'Unknown ID')}</h4>
#             <p><strong>Submitted by:</strong> {receipt.get('submitted_by', 'Unknown')}</p>
#             <p><strong>Date:</strong> {receipt.get('submission_date', 'Unknown')}</p>
#             <p><strong>Amount:</strong> AED {receipt.get('amount_aed', 0)}</p>
#             <p><strong>Reference:</strong> {receipt.get('reference_number', 'Unknown')}</p>
#             <p><strong>{action_text} by:</strong> {action_by}</p>
#             <p><strong>{action_text} on:</strong> {action_date}</p>
#         """, unsafe_allow_html=True)
        
#         # Show notes or reason
#         if status == "approved" and receipt.get('approval_notes'):
#             st.markdown(f"""
#             <p><strong>Notes:</strong> {receipt.get('approval_notes')}</p>
#             """, unsafe_allow_html=True)
#         elif status == "rejected" and receipt.get('rejection_reason'):
#             st.markdown(f"""
#             <p><strong>Reason for rejection:</strong> {receipt.get('rejection_reason')}</p>
#             """, unsafe_allow_html=True)
        
#         st.markdown("</div>", unsafe_allow_html=True)
        
#         # Display receipt image if available (in expander for approved/rejected to save space)
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
    """Render a card for an approved or rejected receipt"""
    status_color = "#28a745" if status == "approved" else "#dc3545"
    action_text = "Approved" if status == "approved" else "Rejected"
    action_by = receipt.get('approved_by' if status == "approved" else 'rejected_by', 'Unknown')
    action_date = receipt.get('approval_date' if status == "approved" else 'rejection_date', 'Unknown')
    
    with st.container():
        st.markdown(f"""
        <div style="padding: 15px; background-color: #f8f9fa; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid {status_color};">
            <h4>Receipt {receipt.get('approval_id', 'Unknown ID')}</h4>
            <p><strong>Submitted by:</strong> {receipt.get('submitted_by', 'Unknown')}</p>
            <p><strong>Date:</strong> {receipt.get('submission_date', 'Unknown')}</p>
            <p><strong>Amount:</strong> AED {receipt.get('amount_aed', 0)}</p>
            <p><strong>Reference:</strong> {receipt.get('reference_number', 'Unknown')}</p>
            <p><strong>{action_text} by:</strong> {action_by}</p>
            <p><strong>{action_text} on:</strong> {action_date}</p>
        """, unsafe_allow_html=True)
        
        # Show notes or reason
        if status == "approved" and receipt.get('approval_notes'):
            st.markdown(f"""
            <p><strong>Notes:</strong> {receipt.get('approval_notes')}</p>
            """, unsafe_allow_html=True)
        elif status == "rejected" and receipt.get('rejection_reason'):
            st.markdown(f"""
            <p><strong>Reason for rejection:</strong> {receipt.get('rejection_reason')}</p>
            """, unsafe_allow_html=True)
        
        # Display database match information if available
        if status == "approved" and "database_match" in receipt:
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
                                <p><strong>Description:</strong> {match.get('database_description', 'Unknown')}</p>
                                <p><strong>Amount:</strong> AED {match.get('database_amount', 0)}</p>
                                <p><strong>Reference:</strong> {match.get('database_reference', 'Unknown')}</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                match_color = "#ffc107"  # Yellow for no match
                st.markdown(f"""
                <p style="color: {match_color};"><strong>⚠️ No Database Match:</strong> This receipt does not match any transaction in our database</p>
                """, unsafe_allow_html=True)
                
                if "message" in match_details:
                    st.info(match_details["message"])
                elif "error" in match_details:
                    st.error(match_details["error"])
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Display receipt image if available (in expander for approved/rejected to save space)
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
    # For testing the manager dashboard directly
    st.session_state.username = "manager@akigroup.com"
    render_manager_dashboard(st.session_state.username)