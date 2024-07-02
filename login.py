import os
import streamlit as st
import requests
from streamlit_cookies_manager import EncryptedCookieManager
import json

# Define your API endpoint
AUTH_ENDPOINT = "http://localhost:8000/auth"

# Initialize the encrypted cookie manager
cookies = EncryptedCookieManager(
    prefix="ktosiek/streamlit-cookies-manager/",
    password=os.environ.get("COOKIES_PASSWORD", "My secret password"),
)

if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.stop()

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
                save_user_data(user_data)
                st.experimental_rerun()  # Rerun the app to load the main page
            else:
                st.error("Authentication failed. Please check your User ID.")
        else:
            st.warning("Please enter your User ID.")

@st.cache_data
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

def save_user_data(user_data):
    user_data_str = json.dumps(user_data)
    cookies["authenticated"] = "True"
    cookies["user_data"] = user_data_str
    cookies.save()

def logout():
    cookies["authenticated"] = ""
    cookies["user_data"] = ""
    cookies.save()
    st.experimental_rerun()

def is_authenticated():
    return cookies.get("authenticated", "False") == "True"

def get_user_data():
    user_data_str = cookies.get("user_data", None)
    if user_data_str:
        return json.loads(user_data_str)
    return None

def main_page():
    user_data = get_user_data()
    if user_data:
        st.title(f"Welcome, {user_data['name']}!")

        # Custom CSS for buttons with centered alignment, fixed size, and no corner radius
        button_style = """
            <style>
                .button {
                    font-family: monospace;
                    background-color: #f3f7fe;
                    color: #00000;
                    border: none;
                    padding: 15px 30px; /* Increase padding for larger size */
                    margin: 10px 0; /* Top and bottom margin */
                    cursor: pointer;
                    transition: background-color 0.3s, box-shadow 0.3s, color 0.3s;
                    display: block; /* Make buttons block-level for stacking */
                    width: 200px; /* Fixed width */
                    height: 60px; /* Fixed height */
                    text-align: center; /* Center align text */
                    border-radius: 0; /* Remove corner radius */
                }

                .button:hover {
                    background-color: #3b82f6;
                    box-shadow: 0 0 0 5px #3b83f65f;
                    color: #fff;
                }

                .logout-button {
                    position: fixed; /* Fixed position */
                    top: 20px;
                    right: 20px;
                    z-index: 1000; /* Ensure logout button is above other elements */
                }
            </style>
        """

        # Use st.markdown with HTML and embedded style for styled buttons
        st.markdown(button_style, unsafe_allow_html=True)

        st.markdown(
            """
            <button class="button">📝 Create Task </button>
            <button class="button">📋 Team Board </button>
            """,
            unsafe_allow_html=True
        )

        if st.button("Logout"):
            logout()

# Main application logic
if __name__ == "__main__":
    if is_authenticated():
        main_page()
    else:
        authenticate()
