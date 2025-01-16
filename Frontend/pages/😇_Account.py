import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8001"  # FastAPI backend URL

# Initialize session state for token
if "token" not in st.session_state:
    st.session_state["token"] = None


def account():
    st.markdown('<h1 style="color:violet;">Welcome to Diet-Food Recommendation 😎</h1>', unsafe_allow_html=True)

    # Check if the user is logged in
    if st.session_state["token"]:
        st.success("You are logged in!")
        if st.button("Logout"):
            st.session_state["token"] = None
            st.info("You have logged out.")
        return

    # Login/Signup options
    choice = st.selectbox('Login/Signup', ['Login', 'Sign Up'])

    if choice == 'Login':
        email = st.text_input('Email Address')
        password = st.text_input("Password", type='password')

        if st.button('Login'):
            response = requests.post(f"{BASE_URL}/login", data={"username": email, "password": password})
            if response.status_code == 200:
                st.session_state["token"] = response.json().get("access_token")
                st.success("Login successful!")
            else:
                st.error(response.json().get("detail", "Login failed."))
    else:
        email = st.text_input('Email Address')
        username = st.text_input('Enter the Unique User Name')
        password = st.text_input("Password", type='password')

        if st.button('Create an Account'):
            response = requests.post(f"{BASE_URL}/signup", json={"email": email, "username": username, "password": password})
            if response.status_code == 200:
                st.success(response.json().get("message"))
            else:
                st.error(response.json().get("detail", "Signup failed."))


def profile():
    st.markdown('<h1 style="color:violet;">Your Profile</h1>', unsafe_allow_html=True)

    if not st.session_state["token"]:
        st.warning("Please log in to view your profile.")
        return

    # Fetch profile details from the backend
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.get(f"{BASE_URL}/profile", headers=headers)

    if response.status_code == 200:
        profile_data = response.json()
        st.write(f"**Email:** {profile_data['email']}")
        st.write(f"**Username:** {profile_data['username']}")
        st.write(f"**Role:** {profile_data['role']}")
    else:
        st.error("Failed to fetch profile details. Please try logging in again.")
        if st.button("Logout"):
            st.session_state["token"] = None





# Initialize session state for token
if "token" not in st.session_state:
    st.session_state["token"] = None


def admin_page():
    st.markdown('<h1 style="color:violet;">Admin Dashboard</h1>', unsafe_allow_html=True)

    # Check if the user is logged in and is an admin
    if not st.session_state["token"]:
        st.warning("Please log in to access the admin page.")
        return

    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    response = requests.get(f"{BASE_URL}/profile", headers=headers)

    if response.status_code != 200:
        st.error("Failed to fetch profile. Please try logging in again.")
        return

    user_data = response.json()

    if user_data.get("role") != "admin":
        st.error("You do not have admin privileges to access this page.")
        return

    # Fetch all data (e.g., all users) for admin
    admin_data_response = requests.get(f"{BASE_URL}/admin/data", headers=headers)

    if admin_data_response.status_code == 200:
        users = admin_data_response.json()

        # Convert data into a pandas dataframe
        users_df = pd.DataFrame(users)

        # Display user data in a table
        st.write("### All Users Data")
        st.dataframe(users_df)

        # Create a new user
        st.subheader("Create a New User")
        with st.form("create_user_form"):
            new_email = st.text_input("Email")
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])

            submit_button = st.form_submit_button("Create User")

            if submit_button:
                new_user_data = {
                    "email": new_email,
                    "username": new_username,
                    "password": new_password,
                    "role": new_role,
                }
                create_response = requests.post(f"{BASE_URL}/signup", json=new_user_data)

                if create_response.status_code == 200:
                    st.success("User created successfully!")
                    # Refresh the data
                    admin_data_response = requests.get(f"{BASE_URL}/admin/data", headers=headers)
                    users = admin_data_response.json()
                    users_df = pd.DataFrame(users)
                    st.dataframe(users_df)
                else:
                    st.error(f"Failed to create user: {create_response.json().get('detail', 'Unknown error')}")

        # Update user role
        st.subheader("Update User Role")
        with st.form("update_role_form"):
            user_id = st.selectbox("Select User to Update", users_df["email"].tolist())
            new_role = st.selectbox("New Role", ["user", "admin"])
            update_button = st.form_submit_button("Update Role")

            if update_button:
                user_to_update = next((user for user in users if user["email"] == user_id), None)
                if user_to_update:
                    update_response = requests.put(
                        f"{BASE_URL}/admin/update_role/{user_to_update['_id']}",
                        json={"role": new_role},
                        headers=headers,
                    )
                    if update_response.status_code == 200:
                        st.success("User role updated successfully!")
                        # Refresh the data
                        admin_data_response = requests.get(f"{BASE_URL}/admin/data", headers=headers)
                        users = admin_data_response.json()
                        users_df = pd.DataFrame(users)
                        st.dataframe(users_df)
                    else:
                        st.error(f"Failed to update role: {update_response.json().get('detail', 'Unknown error')}")
                else:
                    st.error("User not found.")

        # Delete user
        st.subheader("Delete User")
        with st.form("delete_user_form"):
            delete_user_email = st.selectbox("Select User to Delete", users_df["email"].tolist())
            delete_button = st.form_submit_button("Delete User")

            if delete_button:
                user_to_delete = next((user for user in users if user["email"] == delete_user_email), None)
                if user_to_delete:
                    delete_response = requests.delete(
                        f"{BASE_URL}/admin/delete_user/{user_to_delete['_id']}",
                        headers=headers,
                    )
                    if delete_response.status_code == 200:
                        st.success("User deleted successfully!")
                        # Refresh the data
                        admin_data_response = requests.get(f"{BASE_URL}/admin/data", headers=headers)
                        users = admin_data_response.json()
                        users_df = pd.DataFrame(users)
                        st.dataframe(users_df)
                    else:
                        st.error(f"Failed to delete user: {delete_response.json().get('detail', 'Unknown error')}")
                else:
                    st.error("User not found.")
    else:
        st.error("Failed to fetch admin data. Please check your credentials and try again.")

# Streamlit navigation (update the menu)
menu = st.sidebar.selectbox("Menu", ["Account Status", "Profile", "Admin Dashboard"])

if menu == "Account Status":
    account()
elif menu == "Profile":
    profile()
elif menu == "Admin Dashboard":
    admin_page()


