import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"  # FastAPI backend URL

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
    else:
        st.error("Failed to fetch profile details. Please try logging in again.")
        if st.button("Logout"):
            st.session_state["token"] = None


# Streamlit navigation
menu = st.sidebar.selectbox("Menu", ["Account Status", "Profile"])

if menu == "Account Status":
    account()
elif menu == "Profile":
    profile()
