import streamlit as st
from pathlib import Path
import json

def check_user_roles_file():
    """Check if user_roles.json exists and is properly formatted"""
    user_roles_file = Path("user_roles.json")
    
    if not user_roles_file.exists():
        st.error("user_roles.json file not found!")
        return None
    
    try:
        with open(user_roles_file, "r") as f:
            roles = json.load(f)
            return roles
    except Exception as e:
        st.error(f"Error reading user_roles.json: {str(e)}")
        return None

def display_session_state():
    """Display all session state values"""
    st.subheader("Session State Values")
    
    if not st.session_state:
        st.info("Session state is empty")
        return
    
    # Create a table of session state values
    data = []
    for key, value in st.session_state.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            data.append({"Key": key, "Value": str(value), "Type": type(value).__name__})
        else:
            data.append({"Key": key, "Value": "Complex data type", "Type": type(value).__name__})
    
    st.table(data)

st.title("Session Debug Dashboard")

# Check authentication status
st.subheader("Authentication Status")
is_authenticated = 'authenticated' in st.session_state and st.session_state.authenticated
st.write(f"Authenticated: {is_authenticated}")

if is_authenticated:
    st.write(f"Username: {st.session_state.get('username', 'Not set')}")
    st.write(f"User Role: {st.session_state.get('user_role', 'Not set')}")

# Check user_roles.json file
st.subheader("User Roles File")
roles = check_user_roles_file()
if roles:
    st.write("user_roles.json found and loaded successfully:")
    st.json(roles)
    
    # Check if uploader@akigroup.com is in the file
    has_uploader = "uploader@akigroup.com" in roles
    if has_uploader:
        st.success("✅ uploader@akigroup.com found with role: " + roles["uploader@akigroup.com"])
    else:
        st.error("❌ uploader@akigroup.com not found in user_roles.json")

# Display all session state values
display_session_state()

# Add option to reset session
if st.button("Reset Session State"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Session state has been reset. Refresh the page.")

st.write("---")
st.write("After fixing issues, you can return to the main application.")