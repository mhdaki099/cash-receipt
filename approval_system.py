import streamlit as st
import json
import datetime
import os
from pathlib import Path
import time
import base64
from excel_database_handler import match_receipt_with_database


__all__ = [
    'initialize_files', 'load_data', 'save_data', 'submit_for_approval',
    'approve_receipt', 'reject_receipt', 'add_notification',
    'get_notifications', 'mark_notification_read', 'get_receipt_stats',
    'get_receipts_by_salesperson'
]

DATA_DIR = Path("data")
RECEIPTS_FILE = DATA_DIR / "receipts.json"
PENDING_FILE = DATA_DIR / "pending_approvals.json"
APPROVED_FILE = DATA_DIR / "approved_receipts.json"
REJECTED_FILE = DATA_DIR / "rejected_receipts.json"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"

DATA_DIR.mkdir(exist_ok=True)

def initialize_files():
    """Initialize JSON files for storing receipt data"""
    if not RECEIPTS_FILE.exists():
        with open(RECEIPTS_FILE, "w") as f:
            json.dump([], f)
    
    if not PENDING_FILE.exists():
        with open(PENDING_FILE, "w") as f:
            json.dump([], f)
    
    if not APPROVED_FILE.exists():
        with open(APPROVED_FILE, "w") as f:
            json.dump([], f)
    
    if not REJECTED_FILE.exists():
        with open(REJECTED_FILE, "w") as f:
            json.dump([], f)
            
    if not NOTIFICATIONS_FILE.exists():
        with open(NOTIFICATIONS_FILE, "w") as f:
            json.dump([], f)

def load_data(file_path):
    """Load data from a JSON file"""
    if file_path.exists():
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"JSON error in file {file_path}: {str(e)}")
            # Optionally dump the content of the file for inspection
            with open(file_path, "r") as f:
                print(f"File content: {f.read()}")
            # Return an empty list instead of failing
            return []
    return []

def save_data(data, file_path):
    """Save data to a JSON file"""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# def submit_for_approval(receipt_data, submitted_by):
#     """Submit a receipt for manager approval"""
#     pending_approvals = load_data(PENDING_FILE)
    
#     receipt_data["submitted_by"] = submitted_by
#     receipt_data["submission_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#     receipt_data["status"] = "pending"
#     receipt_data["approval_id"] = f"APR-{int(time.time())}"
    
#     pending_approvals.append(receipt_data)
#     save_data(pending_approvals, PENDING_FILE)
    
#     add_notification(
#         recipient_type="manager",
#         recipient=None, 
#         message=f"New receipt submitted for approval by {submitted_by}",
#         receipt_id=receipt_data["approval_id"],
#         receipt_data=receipt_data
#     )
    
#     return receipt_data["approval_id"]

def get_notifications(username, user_type):
    """Get notifications for a specific user"""
    notifications = load_data(NOTIFICATIONS_FILE)
    user_notifications = []
    
    for notification in notifications:
        # Include notifications for all users of this type
        if notification["recipient_type"] == user_type and (notification["recipient"] is None or notification["recipient"] == username):
            user_notifications.append(notification)
    
    # Sort by timestamp (newest first)
    user_notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    return user_notifications

def submit_for_approval(receipt_data, submitted_by):
    """Submit a receipt for manager approval"""
    # Make a copy to avoid modifying the original
    receipt_to_save = receipt_data.copy()
    
    # Check for binary attachment data and convert to base64 if needed
    if 'attachment' in receipt_to_save and isinstance(receipt_to_save['attachment'], bytes):
        receipt_to_save['attachment'] = base64.b64encode(receipt_to_save['attachment']).decode('utf-8')
    
    # Load current pending approvals
    pending_approvals = load_data(PENDING_FILE)
    
    # Add submission metadata
    receipt_to_save["submitted_by"] = submitted_by
    receipt_to_save["submission_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    receipt_to_save["status"] = "pending"
    receipt_to_save["approval_id"] = f"APR-{int(time.time())}"
    
    # Add to pending approvals
    pending_approvals.append(receipt_to_save)
    save_data(pending_approvals, PENDING_FILE)
    
    # Add notification for managers
    add_notification(
        recipient_type="manager",
        recipient=None,  # All managers
        message=f"New receipt submitted for approval by {submitted_by}",
        receipt_id=receipt_to_save["approval_id"],
        receipt_data=receipt_to_save
    )
    
    return receipt_to_save["approval_id"]

# def approve_receipt(approval_id, approved_by, notes=""):
    """Approve a receipt"""
    pending_approvals = load_data(PENDING_FILE)
    approved_receipts = load_data(APPROVED_FILE)
    
    receipt_index = None
    receipt_data = None
    for i, receipt in enumerate(pending_approvals):
        if receipt.get("approval_id") == approval_id:
            receipt_index = i
            receipt_data = receipt
            break
    
    if receipt_index is None:
        return False, "Receipt not found"
    
    receipt_data["status"] = "approved"
    receipt_data["approved_by"] = approved_by
    receipt_data["approval_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    receipt_data["approval_notes"] = notes
    
    approved_receipts.append(receipt_data)
    del pending_approvals[receipt_index]
    
    save_data(pending_approvals, PENDING_FILE)
    save_data(approved_receipts, APPROVED_FILE)
    
    add_notification(
        recipient_type="salesperson",
        recipient=receipt_data["submitted_by"],
        message=f"Your receipt {approval_id} has been approved",
        receipt_id=approval_id,
        receipt_data=receipt_data
    )
    
    return True, "Receipt approved successfully"

# def approve_receipt(approval_id, approved_by, notes=""):
#     """Approve a receipt"""
#     try:
#         # Debug info
#         print(f"Approving receipt: {approval_id} by {approved_by}")
        
#         pending_approvals = load_data(PENDING_FILE)
#         approved_receipts = load_data(APPROVED_FILE)
        
#         # Debug info
#         print(f"Found {len(pending_approvals)} pending approvals")
        
#         receipt_index = None
#         receipt_data = None
#         for i, receipt in enumerate(pending_approvals):
#             if receipt.get("approval_id") == approval_id:
#                 receipt_index = i
#                 receipt_data = receipt
#                 break
        
#         # Debug info
#         if receipt_index is None:
#             print(f"Receipt with ID {approval_id} not found in pending approvals")
#             return False, f"Receipt with ID {approval_id} not found"
        
#         print(f"Found receipt at index {receipt_index}")
        
#         receipt_data["status"] = "approved"
#         receipt_data["approved_by"] = approved_by
#         receipt_data["approval_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#         receipt_data["approval_notes"] = notes
        
#         approved_receipts.append(receipt_data)
#         del pending_approvals[receipt_index]
        
#         save_data(pending_approvals, PENDING_FILE)
#         save_data(approved_receipts, APPROVED_FILE)
        
#         # Add notification
#         add_notification(
#             recipient_type="salesperson",
#             recipient=receipt_data["submitted_by"],
#             message=f"Your receipt {approval_id} has been approved",
#             receipt_id=approval_id,
#             receipt_data=receipt_data
#         )
        
#         # Debug info
#         print(f"Successfully approved receipt {approval_id}")
        
#         return True, "Receipt approved successfully"
#     except Exception as e:
#         print(f"Error approving receipt: {str(e)}")
#         return False, f"Error: {str(e)}"

def approve_receipt(approval_id, approved_by, notes=""):
    """Approve a receipt"""
    try:
        # Debug info
        print(f"Approving receipt: {approval_id} by {approved_by}")
        
        pending_approvals = load_data(PENDING_FILE)
        approved_receipts = load_data(APPROVED_FILE)
        
        # Debug info
        print(f"Found {len(pending_approvals)} pending approvals")
        
        receipt_index = None
        receipt_data = None
        for i, receipt in enumerate(pending_approvals):
            if receipt.get("approval_id") == approval_id:
                receipt_index = i
                receipt_data = receipt
                break
        
        # Debug info
        if receipt_index is None:
            print(f"Receipt with ID {approval_id} not found in pending approvals")
            return False, f"Receipt with ID {approval_id} not found"
        
        print(f"Found receipt at index {receipt_index}")
        
        # Check if the receipt matches with the Excel database
        is_match, match_details = match_receipt_with_database(receipt_data)
        
        # Add match information to the receipt data
        receipt_data["database_match"] = is_match
        receipt_data["match_details"] = match_details
        
        receipt_data["status"] = "approved"
        receipt_data["approved_by"] = approved_by
        receipt_data["approval_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        receipt_data["approval_notes"] = notes
        
        approved_receipts.append(receipt_data)
        del pending_approvals[receipt_index]
        
        save_data(pending_approvals, PENDING_FILE)
        save_data(approved_receipts, APPROVED_FILE)
        
        # Add notification with match details
        message = f"Your receipt {approval_id} has been approved"
        if is_match:
            message += " and matches with a transaction in our database"
        
        add_notification(
            recipient_type="salesperson",
            recipient=receipt_data["submitted_by"],
            message=message,
            receipt_id=approval_id,
            receipt_data=receipt_data
        )
        
        # Debug info
        print(f"Successfully approved receipt {approval_id}")
        
        return True, "Receipt approved successfully"
    except Exception as e:
        print(f"Error approving receipt: {str(e)}")
        return False, f"Error: {str(e)}"

# def reject_receipt(approval_id, rejected_by, reason):
#     """Reject a receipt with a reason"""
#     pending_approvals = load_data(PENDING_FILE)
#     rejected_receipts = load_data(REJECTED_FILE)
    
#     receipt_index = None
#     receipt_data = None
#     for i, receipt in enumerate(pending_approvals):
#         if receipt.get("approval_id") == approval_id:
#             receipt_index = i
#             receipt_data = receipt
#             break
    
#     if receipt_index is None:
#         return False, "Receipt not found"
    
#     if not reason:
#         return False, "Rejection reason is required"
    
#     receipt_data["status"] = "rejected"
#     receipt_data["rejected_by"] = rejected_by
#     receipt_data["rejection_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
#     receipt_data["rejection_reason"] = reason
    
#     rejected_receipts.append(receipt_data)
#     del pending_approvals[receipt_index]
    
#     save_data(pending_approvals, PENDING_FILE)
#     save_data(rejected_receipts, REJECTED_FILE)
    
#     add_notification(
#         recipient_type="salesperson",
#         recipient=receipt_data["submitted_by"],
#         message=f"Your receipt {approval_id} has been rejected: {reason}",
#         receipt_id=approval_id,
#         receipt_data=receipt_data
#     )
    
#     return True, "Receipt rejected successfully"

def reject_receipt(approval_id, rejected_by, reason):
    """Reject a receipt with a reason"""

    st.write(f"Debug: Rejecting receipt {approval_id} by {rejected_by} with reason: {reason}")
    # pending_approvals = load_data(PENDING_FILE)
    pending_approvals = load_data(PENDING_FILE)
    rejected_receipts = load_data(REJECTED_FILE)
    st.write(f"Debug: Found {len(pending_approvals)} pending approvals")

    
    receipt_index = None
    receipt_data = None
    for i, receipt in enumerate(pending_approvals):
        if receipt.get("approval_id") == approval_id:
            receipt_index = i
            receipt_data = receipt
            break
    
    if receipt_index is None:
        return False, "Receipt not found"
    
    if not reason:
        return False, "Rejection reason is required"
    
    receipt_data["status"] = "rejected"
    receipt_data["rejected_by"] = rejected_by
    receipt_data["rejection_date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    receipt_data["rejection_reason"] = reason
    
    rejected_receipts.append(receipt_data)
    del pending_approvals[receipt_index]
    
    save_data(pending_approvals, PENDING_FILE)
    save_data(rejected_receipts, REJECTED_FILE)
    
    add_notification(
        recipient_type="salesperson",
        recipient=receipt_data["submitted_by"],
        message=f"Your receipt {approval_id} has been rejected: {reason}",
        receipt_id=approval_id,
        receipt_data=receipt_data
    )
    
    return True, "Receipt rejected successfully"

def add_notification(recipient_type, recipient, message, receipt_id, receipt_data):
    """Add a notification for a user"""
    notifications = load_data(NOTIFICATIONS_FILE)
    
    notification = {
        "id": f"NOTIF-{int(time.time())}-{len(notifications)}",
        "recipient_type": recipient_type,
        "recipient": recipient, 
        "message": message,
        "receipt_id": receipt_id,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "read": False,
        "receipt_data": receipt_data
    }
    
    notifications.append(notification)
    save_data(notifications, NOTIFICATIONS_FILE)
    return notification["id"]

# def get_notifications(username, user_type):
#     """Get notifications for a specific user"""
#     notifications = load_data(NOTIFICATIONS_FILE)
#     user_notifications = []
    
#     for notification in notifications:
#         if notification["recipient_type"] == user_type and (notification["recipient"] is None or notification["recipient"] == username):
#             user_notifications.append(notification)
    
#     user_notifications.sort(key=lambda x: x["timestamp"], reverse=True)
#     return user_notifications

def add_notification(recipient_type, recipient, message, receipt_id, receipt_data):
    """Add a notification for a user"""
    notifications = load_data(NOTIFICATIONS_FILE)
    
    # Make a copy to avoid modifying the original
    receipt_to_save = receipt_data.copy() if receipt_data else None
    
    # Check for binary attachment data and convert to base64 if needed
    if receipt_to_save and 'attachment' in receipt_to_save and isinstance(receipt_to_save['attachment'], bytes):
        receipt_to_save['attachment'] = base64.b64encode(receipt_to_save['attachment']).decode('utf-8')
    
    notification = {
        "id": f"NOTIF-{int(time.time())}-{len(notifications)}",
        "recipient_type": recipient_type,
        "recipient": recipient,  # None means all users of that type
        "message": message,
        "receipt_id": receipt_id,
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "read": False,
        "receipt_data": receipt_to_save
    }
    
    notifications.append(notification)
    save_data(notifications, NOTIFICATIONS_FILE)
    return notification["id"]

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notifications = load_data(NOTIFICATIONS_FILE)
    
    for notification in notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
    
    save_data(notifications, NOTIFICATIONS_FILE)

def get_receipt_stats():
    """Get statistics about receipts for managers"""
    pending = load_data(PENDING_FILE)
    approved = load_data(APPROVED_FILE)
    rejected = load_data(REJECTED_FILE)
    
    pending_total = sum(float(receipt.get("amount_aed", 0)) for receipt in pending)
    approved_total = sum(float(receipt.get("amount_aed", 0)) for receipt in approved)
    rejected_total = sum(float(receipt.get("amount_aed", 0)) for receipt in rejected)
    
    stats = {
        "pending_count": len(pending),
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "pending_total": pending_total,
        "approved_total": approved_total,
        "rejected_total": rejected_total,
        "total_count": len(pending) + len(approved) + len(rejected),
        "total_amount": pending_total + approved_total + rejected_total
    }
    
    return stats

def get_receipts_by_salesperson(username):
    """Get all receipts submitted by a specific salesperson"""
    pending = load_data(PENDING_FILE)
    approved = load_data(APPROVED_FILE)
    rejected = load_data(REJECTED_FILE)
    
    user_pending = [r for r in pending if r.get("submitted_by") == username]
    user_approved = [r for r in approved if r.get("submitted_by") == username]
    user_rejected = [r for r in rejected if r.get("submitted_by") == username]
    
    return {
        "pending": user_pending,
        "approved": user_approved,
        "rejected": user_rejected
    }



initialize_files()