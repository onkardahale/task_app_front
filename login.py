import os
import streamlit as st
import requests
from streamlit_cookies_manager import EncryptedCookieManager
import json
from datetime import datetime
import re

st.set_page_config(page_title="Tasuko", page_icon="🪨", layout = "wide", initial_sidebar_state="collapsed")

AUTH_ENDPOINT = "http://localhost:8000/auth"
TASKS_ENDPOINT = "http://localhost:8000/tasks"
TEAM_TASKS_ENDPOINT = "http://localhost:8000/team-tasks"
TEAM_ENDPOINT = "http://localhost:8000/teams"
USER_ENDPOINT = "http://localhost:8000/user"

# Initialize the encrypted cookie manager
cookies = EncryptedCookieManager(
    prefix="ktosiek/streamlit-cookies-manager/",
    password=os.environ.get("COOKIES_PASSWORD", "My secret password"),
)

if not cookies.ready():
    # Wait for the component to load and send us current cookies.
    st.stop()

@st.cache_data
def login_user(uid):
    try:
        response = requests.post(AUTH_ENDPOINT, json={"uid": uid})
        if response.status_code == 200:
            user_data = response.json()
            user_data['uid'] = uid  # Ensure 'uid' is set in user_data
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
    st.rerun()

def is_authenticated():
    return cookies.get("authenticated", "False") == "True"

def get_user_data():
    user_data_str = cookies.get("user_data", None)
    if user_data_str:
        return json.loads(user_data_str)
    return None

def get_tasks(uid):
    try:
        url = f"{TASKS_ENDPOINT}/{uid}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve tasks. Error {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return None
    
def update_task(task_id, updated_task):
    try:
        url = f"{TASKS_ENDPOINT}/{task_id}"
        response = requests.put(url, json=updated_task)
        if response.status_code == 200:
            st.success("Task updated successfully.")
            return True
        else:
            st.error(f"Failed to update task. Error {response.status_code}")
            return False
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return False

def create_task(uid):
    user_data = get_user_data()
    if user_data and 'uid' in user_data:  # Ensure 'uid' is present in user_data
        tasks = get_tasks(user_data['uid'])
        if tasks:

            # Organize tasks by status
            todo_tasks = [task for task in tasks if task['status'] == 'Todo']
            in_progress_tasks = [task for task in tasks if task['status'] == 'In Progress']
            done_tasks = [task for task in tasks if task['status'] == 'Done']
            
            # Display tasks in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Todo")
                for task in todo_tasks:
                    display_task(task)
            
            with col2:
                st.subheader("In Progress")
                for task in in_progress_tasks:
                    display_task(task)
            
            with col3:
                st.subheader("Done")
                for task in done_tasks:
                    display_task(task)
        else:
            st.warning("No tasks found.")
    else:
        st.error("User data or 'uid' not found.")
        
def display_task(task):
    with st.expander(f"{task['title']}\n\n {task['due_date']}"):
        st.write(f"{task['description']}")
        st.write(f"Status: {task['status']}")
        st.write(f"Due Date: {task['due_date']}")
        
        # Display tags
        if 'tags' in task and task['tags']:
            tag_names = [tag['name'] for tag in task['tags']]
            st.write("Tags: " + ", ".join(tag_names))

        edit_button_key = f"edit_button_{task['task_id']}"  # Unique key for each edit button
        if st.button("Edit Task", key=edit_button_key):
            st.session_state.selected_task = task  # Store selected task in session state for editing
            save_edited_task()

@st.experimental_dialog("Edit Task")  
def save_edited_task():
    selected_task = st.session_state.selected_task
    edited_title = st.text_input("Title", value=selected_task['title'])
    edited_description = st.text_area("Description", value=selected_task['description'])
    edited_status = st.selectbox("Status", options=["Todo", "In Progress", "Done"], index=["Todo", "In Progress", "Done"].index(selected_task['status']))
    edited_due_date = st.date_input("Due Date", value=datetime.strptime(selected_task['due_date'], "%Y-%m-%d").date() if selected_task['due_date'] else None)
    
    current_tags = ", ".join([tag['name'] for tag in selected_task.get('tags', [])])
    edited_tags = st.text_input("Edit Tags (comma-separated)", value=current_tags)
    
    if st.button("Update"):
                updated_task = {
                    "title": edited_title,
                    "description": edited_description,
                    "status": edited_status,
                    "due_date": edited_due_date.strftime("%Y-%m-%d") if edited_due_date else None,
                    "tags": [tag.strip() for tag in edited_tags.split(",") if tag.strip()]
                }
                
                response = requests.put(f"{TASKS_ENDPOINT}/{selected_task['task_id']}", json=updated_task)
                if response.status_code == 200:
                    st.rerun()  # Rerun the app to reflect changes
                else:
                    st.error(f"Failed to update task: {response.json().get('detail')}")     
                    
    if st.button("Delete"):
                    response = requests.delete(f"{TASKS_ENDPOINT}/{selected_task['task_id']}")
                    if response.status_code == 204:
                        st.rerun()
                    else:
                        st.error(f"Failed to delete task: {response.json().get('detail')}")              

@st.cache_data
def get_teams(uid):
    try:
        response = requests.get(f"{TEAM_ENDPOINT}/{uid}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve teams. Error {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return []
    
@st.cache_data
def get_team_members(team_id):
    try:
        response = requests.get(f"{TEAM_ENDPOINT}/{team_id}/members")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve team members. Error {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return []    

def create_team_task(team_id):
    tasks = get_team_tasks(team_id)
    if tasks:
        # Organize tasks by status
        todo_tasks = [task for task in tasks if task['status'] == 'Todo']
        in_progress_tasks = [task for task in tasks if task['status'] == 'In Progress']
        done_tasks = [task for task in tasks if task['status'] == 'Done']

        # Display tasks in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader("Todo")
            for task in todo_tasks:
                display_team_task(task)

        with col2:
            st.subheader("In Progress")
            for task in in_progress_tasks:
                display_team_task(task)

        with col3:
            st.subheader("Done")
            for task in done_tasks:
                display_team_task(task)
    else:
        st.warning("No tasks found.")
        
@st.cache_data
def get_team_tasks(team_id):
    try:
        response = requests.get(f"{TEAM_TASKS_ENDPOINT}/{team_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to retrieve team tasks. Error {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return []
    
def display_team_task(task):
    with st.expander(f"{task['title']}\n\n {task['due_date']}"):
        st.write(f"{task['description']}")
        st.write(f"Status: {task['status']}")
        st.write(f"Due Date: {task['due_date']}")

        # Display tags
        if 'tags' in task and task['tags']:
            tag_names = [tag['name'] for tag in task['tags']]
            st.write("Tags: " + ", ".join(tag_names))

        # Display assignees
        if 'assignees' in task and task['assignees']:
            assignee_names = [assignee['username'] for assignee in task['assignees']]
            st.write("Assignees: " + ", ".join(assignee_names))

        edit_button_key = f"edit_team_task_{task['task_id']}"  # Unique key for each edit button
        if st.button("Edit Task", key=edit_button_key):
            st.session_state.selected_team_task = task  # Store selected task in session state for editing
            save_edited_team_task()
            
@st.experimental_dialog("Edit Task")
def save_edited_team_task():
    selected_task = st.session_state.selected_team_task
    team_id = st.session_state.selected_team_id
    
    edited_title = st.text_input("Title", value=selected_task['title'])
    edited_description = st.text_area("Description", value=selected_task['description'])
    edited_status = st.selectbox("Status", options=["Todo", "In Progress", "Done"], index=["Todo", "In Progress", "Done"].index(selected_task['status']))
    edited_due_date = st.date_input("Due Date", value=datetime.strptime(selected_task['due_date'], "%Y-%m-%d").date() if selected_task['due_date'] else None)
    
    current_tags = ", ".join([tag['name'] for tag in selected_task.get('tags', [])])
    edited_tags = st.text_input("Edit Tags (comma-separated)", value=current_tags)

    # Get team members
    team_members = get_team_members(team_id)
    member_options = {member['username']: member['user_id'] for member in team_members}

    # Get current assignees
    current_assignees = [assignee['username'] for assignee in selected_task.get('assignees', [])]

    # Multi-select for assignees with current assignees as default
    selected_assignees = st.multiselect(
        "Assignees",
        options=list(member_options.keys()),
        default=current_assignees
    )
    if st.button("Update"):
        updated_task = {
            "title": edited_title,
            "description": edited_description,
            "status": edited_status,
            "due_date": edited_due_date.strftime("%Y-%m-%d") if edited_due_date else None,
            "tags": [tag.strip() for tag in edited_tags.split(",") if tag.strip()],
            "assignee": [member_options[username] for username in selected_assignees]
        }
        response = requests.put(f"{TASKS_ENDPOINT}/{selected_task['task_id']}", json=updated_task)
        if response.status_code == 200:
            st.success("Task updated successfully")
            st.rerun()  # Rerun the app to reflect changes
        else:
            st.error(f"Failed to update task: {response.json().get('detail')}")
            
@st.experimental_dialog("New task")
def create_new_task(uid):
    title = st.text_input("Title")
    description = st.text_area("Description")
    status = st.selectbox("Status", options=["Todo", "In Progress", "Done"])
    due_date = st.date_input("Due Date")
    tags = st.text_input("Tags (comma-separated)")
    if st.button("Update"):
        new_task = {
            "title": title,
            "description": description,
            "status": status,
            "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
            "tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
            "uid": get_user_data()['uid']
        }
        response = requests.post(f"{TASKS_ENDPOINT}/", json=new_task)
        
        if response.status_code == 200:
            st.success("Task created successfully")
            st.rerun()  # Rerun the app to reflect changes
        else:
            st.error(f"Failed to update task: {response.status_code}")
    
def create_user(username, email):
    try:
        response = requests.post(f"{USER_ENDPOINT}", json={"username": username, "email": email})
        if response.status_code == 200:
            uid = response.json()['uid']
            st.write(f"This is your uid:\n {uid}")
        else:
            st.error(f"Failed to create user. Error {response.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"Request error: {e}")
        return []    
    
@st.experimental_dialog("Enter details to create an account")
def create_user_dialog():
    username = st.text_input("Username")
    email = st.text_input("Email")
    email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    
    if(email != "" and not re.fullmatch(email_regex, email)):
        st.error("Enter valid email")
    
    if st.button("Register"):
        create_user(username, email)
    
def login_page():
    st.title("Login")
    with st.form("login_form"):
        uid = st.text_input("User ID")
        submit_button = st.form_submit_button("Login")
    if submit_button:
        if uid:
            # Attempt to authenticate
            auth_status, user_data = login_user(uid)
            if auth_status:
                st.success(f"🪨 Welcome, {user_data['username']}!")
                save_user_data(user_data)
                st.rerun()  # Rerun the app to load the welcome page
            else:
                st.error("Authentication failed. Please check your User ID.")
        else:
            st.warning("Please enter your User ID.")      
    if st.button("Create an account"):
        create_user_dialog()
        
def welcome_page():
    user_data = get_user_data()
    if user_data and 'uid' in user_data:
        if st.button("℺ Logout"):
            logout()
            
        st.title(f"🪨 Welcome, {user_data['username']}!")

        if st.button("📝 Personal Board"):
            st.session_state.page = "personal_board"
            st.rerun()

        if st.button("📋 Team Board"):
            st.session_state.page = "team_board"
            st.rerun()

    else:
        st.error("User data or 'uid' not found.")

def personal_board_page():
    if st.button("↩"):
        st.session_state.page = None
        st.rerun()
        
    st.title("📝 Personal Board")
    
    if st.button("✎ New Task"):
        create_new_task(get_user_data()['uid'])
        
    create_task(get_user_data()['uid'])
    
def team_board_page():
    st.title("Team Board")
    user_data = get_user_data()
    if user_data and 'uid' in user_data:
        teams = get_teams(user_data['uid'])
        if teams:
            team_tabs = st.tabs([team['team_name'] for team in teams])
            for idx, team in enumerate(teams):
                with team_tabs[idx]:
                    st.session_state.selected_team_id = team['team_id']
                    create_team_task(team['team_id'])
        else:
            st.warning("No teams found.")
    else:
        st.error("User data or 'uid' not found.")
        
def main():
    st.markdown(
        """
    <style>
        [data-testid="collapsedControl"] {
            display: none
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if st.session_state.get("page") == "personal_board":
        personal_board_page()
    elif st.session_state.get("page") == "team_board":
        team_board_page()
    elif is_authenticated():
        welcome_page()
    else:
        login_page()

if __name__ == "__main__":
    main()
