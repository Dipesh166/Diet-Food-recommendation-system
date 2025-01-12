import streamlit as st
import requests

# URL for the FastAPI backend
API_URL = "http://localhost:8000"

def login():
    st.title("Signin Page")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("SignIn"):
        response = requests.post(f"{API_URL}/login", data={"username": username, "password": password})
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state["token"] = token
            st.success("SignIn successful!")
            st.experimental_rerun()  # Redirect to home page after login
        else:
            st.error("Invalid credentials, please try again.")

if __name__ == "__main__":
    login()
