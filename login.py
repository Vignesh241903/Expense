import streamlit as st
from PIL import Image
import base64
from db import add_user, login_user, create_session
from datetime import datetime

st.set_page_config(
    page_title="Monthly Expenses Of Personal",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>

/* ================= COLOR SYSTEM =================
   Background   #F8FAFC
   Card         #FFFFFF
   Heading      #0F172A
   Normal text  #334155
   Secondary    #64748B
   Primary      #2563EB
   Border       #E2E8F0
================================================= */

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

.stApp {
    background: #F8FAFC;
    color: #334155;
}

.hero-title {
    text-align: center;
    font-size: 60px;
    font-weight: 900;
    color: #0F172A;
    margin-top: 30px;
    letter-spacing: 1px;
}

.hero-sub {
    text-align: center;
    font-size: 20px;
    color: #64748B;
    margin-bottom: 40px;
}

.glass-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 35px;
    border-radius: 20px;
    box-shadow: 0 4px 16px rgba(15,23,42,0.05);
}

.section-title {
    font-size: 30px;
    font-weight: 800;
    color: #0F172A;
    margin-bottom: 25px;
}

.feature-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 20px;
    transition: 0.3s;
    box-shadow: 0 2px 10px rgba(15,23,42,0.03);
}

.feature-box:hover {
    transform: scale(1.02);
    border: 1px solid #2563EB;
    box-shadow: 0 6px 18px rgba(37,99,235,0.12);
}

.feature-title {
    font-size: 22px;
    font-weight: 700;
    color: #2563EB;
}

.feature-text {
    font-size: 16px;
    color: #334155;
}

.about-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 5px solid #2563EB;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 12px;
    color: #334155;
}

.login-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 40px;
    border-radius: 24px;
    box-shadow: 0 8px 30px rgba(15,23,42,0.06);
}

.stTextInput > div > div > input {
    background-color: #F8FAFC;
    color: #0F172A;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    height: 50px;
}

.stTextInput > label {
    color: #334155 !important;
}

.stButton > button {
    width: 100%;
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    height: 52px;
    font-size: 17px;
    font-weight: 700;
    transition: 0.3s;
}

.stButton > button:hover {
    transform: scale(1.02);
    background: #1D4ED8;
    box-shadow: 0 6px 14px rgba(37,99,235,0.25);
}

.small-text {
    text-align: center;
    color: #64748B;
    margin-top: 15px;
}

.analytics-img {
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid #E2E8F0;
    box-shadow: 0 8px 24px rgba(15,23,42,0.08);
}

/* Real login card — targets Streamlit's native bordered container
   so the background/border actually wraps the fields inside it,
   instead of the old empty <div class="login-card"> that never
   contained anything in the real DOM. */
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.login-card-marker) {
    background: #FFFFFF;
    border: 1px solid #E2E8F0 !important;
    border-radius: 24px !important;
    padding: 10px 20px;
    box-shadow: 0 8px 30px rgba(15,23,42,0.06);
}

</style>
""", unsafe_allow_html=True)

if "show_login" not in st.session_state:
    st.session_state.show_login = False

if "create_account" not in st.session_state:
    st.session_state.create_account = False


st.markdown(
    """
    <div class='hero-title'>
        Monthly Expenses Of Personal
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='hero-sub'>
        Smart Financial Analytics Dashboard For Personal Expense Management
    </div>
    """,
    unsafe_allow_html=True
)


#image
col1, col2, col3 = st.columns([1,5,1])
with col2:
    st.markdown("<div class='analytics-img'>", unsafe_allow_html=True)

    st.image(
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1200&auto=format&fit=crop",
         width='stretch'
    )

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.write("")


st.markdown(
    """
    <div class='section-title'>
        Why Use This Website?
    </div>
    """,
    unsafe_allow_html=True
)

feature_col1, feature_col2 = st.columns(2)
with feature_col1:

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>📊 Smart Expense Analytics</div>
            <div class='feature-text'>
                Visualize your spending patterns with modern charts and dashboards.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>💳 Bank Statement Upload</div>
            <div class='feature-text'>
                Upload CSV or Excel bank statements for automatic expense tracking.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>📅 Monthly Tracking</div>
            <div class='feature-text'>
                Analyze your expenses from January to December with yearly filters.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature_col2:

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>🤖 Auto Expense Categorization</div>
            <div class='feature-text'>
                AI-powered categorization for food, shopping, fuel, utilities and more.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>📈 Advanced Reports</div>
            <div class='feature-text'>
                Generate monthly reports, trend analysis and downloadable summaries.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class='feature-box'>
            <div class='feature-title'>🔐 Secure Personal Dashboard</div>
            <div class='feature-text'>
                Personal login system with protected financial analytics dashboard.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")
st.write("")



st.markdown(
    """
    <div class='section-title'>
        About This Web Application
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='about-box'>
        ✅ Designed for modern personal finance management.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='about-box'>
        ✅ Helps users understand spending behavior and savings trends.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='about-box'>
        ✅ Provides premium UI experience with responsive dashboard analytics.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='about-box'>
        ✅ Built using Streamlit, Pandas, Plotly and postgreSQL technologies.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class='about-box'>
        ✅ Perfect for students, professionals and families managing monthly expenses.
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")
st.write("")






def show_login():
    # HIDE SIDEBAR
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
    display:none;
    }
    </style>
    """, unsafe_allow_html=True)

    # SESSION STATES
    if "show_login" not in st.session_state:
        st.session_state.show_login = False

    if "create_account" not in st.session_state:
        st.session_state.create_account = False

    # LOGIN BUTTON
    center1, center2, center3 = st.columns([2,2,2])

    with center2:

        if st.button("🚀 Login To Dashboard"):
            st.session_state.show_login = True

    # LOGIN AREA
    if st.session_state.show_login:

        st.write("")
        st.write("")

        login_col1, login_col2, login_col3 = st.columns([1,2,1])

        with login_col2:

            card = st.container(border=True)
            with card:

                st.markdown("<div class='login-card-marker'></div>", unsafe_allow_html=True)

                # LOGIN PAGE
                if not st.session_state.create_account:

                    st.markdown(
                        """
                        <div class='section-title' style='text-align:center;'>
                            Welcome Back
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    username = st.text_input("Username")

                    password = st.text_input(
                        "Password",
                        type="password"
                    )

                    st.write("")

                    # LOGIN BUTTON
                    if st.button("Login"):

                        # CHECK USER FROM POSTGRESQL
                        result = login_user(
                            username,
                            password
                        )

                        if result:

                          st.success(
                            "Login Successful"
                             )

                          st.balloons()

    # SAVE USER SESSION
                          st.session_state.logged_in = True

    # SAVE USER DETAILS FROM DATABASE
                          st.session_state.full_name = result[1]

                          st.session_state.email = result[2]

                          st.session_state.username = result[3]

                          st.session_state.password = result[4]

    # LOGIN TIME
                          st.session_state.login_time = datetime.now().strftime(
                          "%d-%m-%Y %H:%M:%S"
                           )

    # PERSIST LOGIN ACROSS A FULL PAGE RELOAD
    # A random token (not the password) goes in the URL; expense.py
    # looks it up on every rerun to restore the session automatically.
                          token = create_session(result[0])
                          st.session_state.session_token = token
                          st.query_params["token"] = token

    # GO TO DASHBOARD
                          st.rerun()

                        else:

                            st.error(
                                "Invalid Username Or Password"
                            )

                    st.markdown(
                        """
                        <div class='small-text'>
                            Don't have an account?
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # CREATE ACCOUNT BUTTON
                    if st.button("Create Account"):

                        st.session_state.create_account = True

                        st.rerun()

                # CREATE ACCOUNT PAGE
                else:

                    st.markdown(
                        """
                        <div class='section-title' style='text-align:center;'>
                            Create New Account
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    new_name = st.text_input(
                        "Full Name"
                    )

                    new_email = st.text_input(
                        "Email Address"
                    )

                    new_user = st.text_input(
                        "Create Username"
                    )

                    new_pass = st.text_input(
                        "Create Password",
                        type="password"
                    )

                    confirm_pass = st.text_input(
                        "Confirm Password",
                        type="password"
                    )

                    st.write("")

                    # CREATE ACCOUNT BUTTON
                    if st.button("Create My Account"):

                        if new_pass != confirm_pass:

                            st.error(
                                "Passwords Do Not Match"
                            )

                        elif len(new_pass) < 4:

                            st.warning(
                                "Password Must Be At Least 4 Characters"
                            )

                        else:

                            # SAVE USER TO POSTGRESQL
                            success = add_user(
                                new_name,
                                new_email,
                                new_user,
                                new_pass
                            )

                            if success:

                                st.success(
                                    "Account Created Successfully"
                                )

                                st.balloons()

                                # GO BACK TO LOGIN
                                st.session_state.create_account = False

                                st.rerun()

                            else:

                                st.error(
                                    "Username Already Exists"
                                )

                    st.markdown(
                        """
                        <div class='small-text'>
                            Already have an account?
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # BACK TO LOGIN
                    if st.button("Back To Login"):

                        st.session_state.create_account = False

                        st.rerun()

st.markdown(
    """
    <div style='text-align:center;color:#64748B;padding:30px;'>
        © 2026 Monthly Expenses Of Personal • Premium Financial Analytics Platform
    </div>
    """,
    unsafe_allow_html=True
)


