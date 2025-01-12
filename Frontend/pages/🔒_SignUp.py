import streamlit as st
import requests

# URL for the FastAPI backend
API_URL = "http://localhost:8000"

def signup():
    st.title("Signup Page")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("SignUp"):
        response = requests.post(f"{API_URL}/signup", json={"username": username, "password": password})
        
        if response.status_code == 200:
            st.success("Signup successful! You can now log in.")
        else:
            st.error("Error: User might already exist.")

if __name__ == "__main__":
    signup()
