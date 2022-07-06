import streamlit as st

st.set_page_config(page_title="Moodika",
                   page_icon=":notes:")

from predict_page2 import show_predict_page
from explore_page import show_explore_page

page = st.sidebar.selectbox("Welcome to Moodika", ("Moodika", "More about Us"))

if page == "Moodika":
    show_predict_page()
else:
    show_explore_page()
