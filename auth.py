import streamlit as st
import requests
import sys
import os

# Add the parent directory to sys.path to import routes
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from routes import AUTH_ENDPOINT

def authenticate():
    st.title("Login")
    
    with st.form("login_form"):
        uid = st.text_input("User ID")
        submit_button = st.form_submit_button("Login")

    if submit_button:
        if uid:
            # Attempt to authenticate
            auth_status, user_data = login_user(uid)
            if auth_status:
                st.success(f"Welcome, {user_data['name']}!")
                st.session_state['authenticated'] = True
                st.session_state['user_data'] = user_data
                return True, user_data
            else:
                st.error("Authentication failed. Please check your User ID.")
        else:
            st.warning("Please enter your User ID.")
    
    return False, None

def login_user(uid):
    try:
        response = requests.post(AUTH_ENDPOINT, json={"uid": uid})
        if response.status_code == 200:
            user_data = response.json()
            return True, user_data
        else:
            return False, None
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return False, None

def logout():
    if st.button("Logout"):
        st.session_state['authenticated'] = False
        st.session_state['user_data'] = None
        st.experimental_rerun()

def is_authenticated():
    return st.session_state.get('authenticated', False)

def get_user_data():
    return st.session_state.get('user_data', None)
