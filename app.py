import streamlit as st
from pages import welcome
from streamlit_cookies_manager import EncryptedCookieManager
import os

from task_app_front import login

# Initialize the encrypted cookie manager
cookies = EncryptedCookieManager(
    prefix="ktosiek/streamlit-cookies-manager/",
    password=os.environ.get("COOKIES_PASSWORD", "My secret password"),
)

if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.stop()

def is_authenticated():
    return cookies.get("authenticated", "False") == "True"

def main():
    if is_authenticated():
        welcome()
    else:
        login()

if __name__ == "__main__":
    main()
