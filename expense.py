import streamlit as st
import login
import dashboard
from db import get_user_by_token
from datetime import datetime

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

st.set_page_config(
    page_title="Expense Tracker",
    layout="wide"
)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# RESTORE SESSION AFTER A FULL PAGE RELOAD
# expense.py is the main script, so this block is guaranteed to run on
# every rerun (unlike code inside imported modules, which can be cached).
# If the browser still has a valid ?token=... in the URL, log the user
# back in automatically instead of dropping them to the login page.
if not st.session_state.logged_in:
    token = st.query_params.get("token")
    if token:
        user = get_user_by_token(token)
        if user:
            st.session_state.logged_in = True
            st.session_state.full_name = user[1]
            st.session_state.email = user[2]
            st.session_state.username = user[3]
            st.session_state.password = user[4]
            st.session_state.session_token = token
            st.session_state.login_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        else:
            st.query_params.pop("token", None)

if st.session_state.logged_in:
    dashboard.show_dashboard()
else:
    login.show_login()

    
