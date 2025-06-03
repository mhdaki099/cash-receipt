import streamlit as st
import os
import hashlib
import json
import re
from pathlib import Path

# Define the path for the user credentials file
CREDENTIALS_FILE = Path("credentials.json")
USER_ROLES_FILE = Path("user_roles.json")

def load_credentials():
    """Load user credentials from file"""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    else:
        # Create default admin user if no credentials exist
        default_credentials = {
            "admin": hash_password("admin123")
        }
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(default_credentials, f)
        return default_credentials

def load_user_roles():
    """Load user roles from file"""
    if USER_ROLES_FILE.exists():
        with open(USER_ROLES_FILE, "r") as f:
            return json.load(f)
    else:
        # Create default roles if no file exists
        default_roles = {
            "admin": "manager",
            "manager@akigroup.com": "manager",
            "sales@akigroup.com": "salesperson"
        }
        with open(USER_ROLES_FILE, "w") as f:
            json.dump(default_roles, f)
        return default_roles

def hash_password(password):
    """Create a SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(username, password, credentials):
    """Verify the provided username and password"""
    # Allow access for any @akigroup.com email with password "12345"
    if re.match(r'.+@akigroup\.com$', username) and password == "12345":
        return True
    
    # Otherwise check the stored credentials
    if username in credentials:
        return credentials[username] == hash_password(password)
    
    return False

# def get_user_role(username):
#     """Get the role of a user"""
#     roles = load_user_roles()
    
#     # If specific user is in roles, return that role
#     if username in roles:
#         return roles[username]
    
#     # For @akigroup.com emails, check if there's a pattern-based role
#     if re.match(r'.+@akigroup\.com$', username):
#         # Check for domain-wide role definitions
#         if "manager" in username.lower():
#             return "manager"
#         else:
#             return "salesperson"  # Default role for akigroup.com emails
    
#     # Default role
#     return "salesperson"

def get_user_role(username):
    """Get the role of a user"""
    roles = load_user_roles()
    
    # If specific user is in roles, return that role
    if username in roles:
        return roles[username]
    
    # For @akigroup.com emails, check if there's a pattern-based role
    if re.match(r'.+@akigroup\.com$', username):
        # Check for specific username patterns
        if "uploader" in username.lower():
            return "uploader"
        elif "manager" in username.lower():
            return "manager"
        else:
            return "salesperson"  # Default role for akigroup.com emails
    
    # Default role
    return "salesperson"

def login_page():
    """Create a login page"""
    st.set_page_config(
        page_title="Receipt Data Extractor - AKI Login",
        page_icon="🔐",
        layout="centered"
    )
    
    # Apply some CSS to style the login form
    st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }

        .login-header {
            text-align: center;
            margin-bottom: 20px;
        }
        .stButton button {
            width: 100%;
            border-radius: 5px;
            height: 3rem;
            background-color: #FF4B4B;
            color: white;
            font-weight: bold;
        }
        .login-instructions {
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 0.9em;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="login-header"><h1>Login</h1><p>Receipt Data Extractor for AKI </p></div>', unsafe_allow_html=True)
    
    # Load credentials
    credentials = load_credentials()
    
    # Create login form
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # If user is already authenticated, show logout option
        if 'authenticated' in st.session_state and st.session_state.authenticated:
            st.success(f"Logged in as {st.session_state.username}")
            if st.button("Logout"):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.user_role = None
                st.rerun()
        else:
            # Login form
            with st.form("login_form"):
                st.markdown('<p style="font-weight: 500;">Email Address / Username</p>', unsafe_allow_html=True)
                username = st.text_input("", placeholder="Enter your email address", label_visibility="collapsed")
                
                st.markdown('<p style="font-weight: 500;">Password</p>', unsafe_allow_html=True)
                password = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
                
                login_button = st.form_submit_button("Login")
                
                if login_button:
                    if verify_password(username, password, credentials):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        
                        # Set user role in session
                        user_role = get_user_role(username)
                        st.session_state.user_role = user_role
                        
                        st.success(f"Login successful! You are logged in as a {user_role}.")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
            
 
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Return whether the user is authenticated
    return 'authenticated' in st.session_state and st.session_state.authenticated

# Function to check authentication status
def is_authenticated():
    return 'authenticated' in st.session_state and st.session_state.authenticated

# Function to require login
def require_login():
    if not is_authenticated():
        login_page()
        st.stop()  # Stop execution if not authenticated
    return st.session_state.username, st.session_state.user_role

# For testing the login page directly
if __name__ == "__main__":
    if login_page():
        st.write("You are now logged in and can access the application!")
        st.write(f"Welcome, {st.session_state.username}!")
        st.write(f"Your role is: {st.session_state.user_role}")
