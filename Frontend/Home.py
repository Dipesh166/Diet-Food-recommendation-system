import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to Diet Recommendation System! 👋")

st.sidebar.success("Select a recommendation app.")

st.markdown(
    """
    A diet recommendation web application using content-based approach with Scikit-Learn, FastAPI and Streamlit.
    You can find more details and the whole project on my 
    """
)


# Check if user is logged in
if "token" in st.session_state:
    st.write("### Welcome to the Diet Recommendation System!")
    st.write("You are logged in!")
else:
    st.write("### Welcome to the Diet Recommendation System!")
    st.write("Please log in or sign up.")
   
