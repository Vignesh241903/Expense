import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pdfplumber
import re
import textwrap
import os
from datetime import datetime
from db import delete_session
import json
import smtplib
from email.mime.text import MIMEText
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Expense Tracker",
    layout="wide"
)

try:
    FEEDBACK_TO_ADDRESS = st.secrets.get("FEEDBACK_TO_EMAIL", "support@example.com")
except Exception:
    FEEDBACK_TO_ADDRESS = os.environ.get("FEEDBACK_TO_EMAIL", "support@example.com")


def render_light_table(df, max_rows=None):
    """Renders a DataFrame as our own styled HTML table instead of st.dataframe.
    st.dataframe draws on a <canvas> that reads Streamlit's theme config directly -
    it ignores page CSS and can still render dark even after theme changes.
    A plain HTML table is real DOM we fully control, so it can never show black."""

    show_df = df.head(max_rows) if max_rows else df

    html = """
    <div style="overflow-x:auto;border:1px solid #E2E8F0;border-radius:12px;">
    <table style="width:100%;border-collapse:collapse;font-family:Arial, sans-serif;font-size:14px;">
        <thead>
            <tr style="background:#F8FAFC;">
    """
    for col in show_df.columns:
        html += f'<th style="text-align:left;padding:10px 14px;color:#0F172A;font-weight:700;border-bottom:1px solid #E2E8F0;white-space:nowrap;">{col}</th>'
    html += "</tr></thead><tbody>"

    for i, (_, row) in enumerate(show_df.iterrows()):
        bg = "#FFFFFF" if i % 2 == 0 else "#F8FAFC"
        html += f'<tr style="background:{bg};">'
        for val in row:
            html += f'<td style="padding:9px 14px;color:#334155;border-bottom:1px solid #E2E8F0;white-space:nowrap;">{val}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    st.markdown(html, unsafe_allow_html=True)


def send_feedback_email(sender_name, sender_username, sender_email, message_body):
    """Sends the feedback text area contents to FEEDBACK_TO_ADDRESS via SMTP.
    Reads SMTP_HOST / SMTP_PORT / SMTP_EMAIL / SMTP_APP_PASSWORD (or SMTP_KEY)
    from .streamlit/secrets.toml. Defaults to Gmail if SMTP_HOST isn't set,
    but this works with any SMTP relay (e.g. Brevo, SendGrid) by just
    changing those values - no code changes needed."""

    def _get(key, default=None):
        try:
            return st.secrets[key]
        except Exception:
            return os.environ.get(key, default)

    smtp_host = _get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(_get("SMTP_PORT", 465))
    smtp_login = _get("SMTP_EMAIL")
    smtp_pass = _get("SMTP_APP_PASSWORD") or _get("SMTP_KEY")
    smtp_from = _get("SMTP_FROM", smtp_login)

    if not smtp_login or not smtp_pass or "your_" in str(smtp_login):
        return False, "Email sending isn't configured yet - fill in the SMTP_* values in .streamlit/secrets.toml"

    msg = MIMEText(
        f"From: {sender_name} (@{sender_username})\nUser email: {sender_email}\n\n{message_body}"
    )
    msg["Subject"] = f"Expense Tracker Feedback - {sender_name}"
    msg["From"] = smtp_from
    msg["To"] = FEEDBACK_TO_ADDRESS

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_login, smtp_pass)
                server.sendmail(smtp_from, [FEEDBACK_TO_ADDRESS], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_login, smtp_pass)
                server.sendmail(smtp_from, [FEEDBACK_TO_ADDRESS], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def show_dashboard():
    st.sidebar.title("Navigation")

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

.stApp{
    background:#F8FAFC;
}

/* Hide Streamlit's default top toolbar (Deploy button, menu) and footer */
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }
header{ visibility:hidden; }
[data-testid="stToolbar"]{ display:none; }
[data-testid="stDecoration"]{ display:none; }
[data-testid="stStatusWidget"]{ display:none; }

/* Sidebar background */
[data-testid="stSidebar"]{
    background:#FFFFFF;
    border-right: 1px solid #E2E8F0;
    box-shadow: 2px 0 12px rgba(15,23,42,0.03);
}

/* Sidebar title */
.sidebar-title{
    text-align:center;
    color:#0F172A;
    font-size:24px;
    font-weight:800;
    margin-bottom:22px;
    padding-top:6px;
    letter-spacing:0.3px;
}

/* Radio buttons container */
.stRadio > div {
    gap: 10px;
}

/* Each menu item */
[data-testid="stSidebar"] .stRadio label{
    background:#F8FAFC;
    padding: 13px 18px;
    border-radius: 12px;
    border: 1px solid #E2E8F0;
    margin-bottom: 8px;
    transition: 0.2s ease;
    font-size: 16px;
    font-weight: 600;
    color:#334155;
}

/* Hover effect */
[data-testid="stSidebar"] .stRadio label:hover{
    background: rgba(37,99,235,0.08);
    border: 1px solid #2563EB;
    color:#2563EB;
}

/* Selected radio */
[data-testid="stSidebar"] .stRadio label[data-selected="true"]{
    background:#2563EB;
    border: 1px solid #2563EB;
    color: #FFFFFF;
    font-weight: 700;
    box-shadow: 0 4px 10px rgba(37,99,235,0.25);
}

/* Hide radio circle */
.stRadio input[type="radio"]{
    display: none;
}

/* Headings inside main content */
h1, h2, h3{
    color:#0F172A !important;
}
p, span, label, .stMarkdown{
    color:#334155;
}

/* Filter Cards */
div.stButton > button{
    width:100%;
    height:56px;
    border-radius:12px;
    border:1px solid #E2E8F0;
    background:#FFFFFF;
    color:#334155;
    font-size:16px;
    font-weight:600;
    transition:all 0.2s ease;
}

/* Hover Effect */
div.stButton > button:hover{
    border:1px solid #2563EB;
    color:#2563EB;
    transform:translateY(-2px);
    box-shadow:0px 6px 14px rgba(37,99,235,0.15);
}

/* Click Effect */
div.stButton > button:active{
    transform:scale(0.98);
}

/* Cards used across dashboard (charts, tables) */
[data-testid="stVerticalBlockBorderWrapper"]{
    background:#FFFFFF;
    border:1px solid #E2E8F0;
    border-radius:16px;
}

/* Dataframe / table container */
[data-testid="stDataFrame"]{
    border:1px solid #E2E8F0;
    border-radius:12px;
}

/* AI chat assistant bubbles - match the light palette instead of
   Streamlit's default dark-contrast bubble colors. !important on every
   rule here since Streamlit's own theme classes can otherwise win on
   specificity and silently keep the dark background. */
[data-testid="stChatMessage"],
[data-testid="stChatMessage"] > div,
.stChatMessage{
    background:#FFFFFF !important;
    border:1px solid #E2E8F0 !important;
    border-radius:14px !important;
    padding:10px 14px !important;
    margin-bottom:10px !important;
    box-shadow:0 2px 8px rgba(15,23,42,0.03);
}
[data-testid="stChatMessage"] *{
    color:#334155 !important;
}
[data-testid="stChatMessage"] h1,
[data-testid="stChatMessage"] h2,
[data-testid="stChatMessage"] h3{
    color:#0F172A !important;
}
[data-testid="stChatMessageAvatarUser"],
[data-testid^="stChatMessageAvatar"][data-testid*="User"]{
    background:#2563EB !important;
}
[data-testid="stChatMessageAvatarAssistant"],
[data-testid^="stChatMessageAvatar"][data-testid*="Assistant"]{
    background:#10B981 !important;
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stBottomBlockContainer"]{
    background:#FFFFFF !important;
    border:1px solid #E2E8F0 !important;
    border-radius:12px !important;
}
[data-testid="stChatInput"] textarea{
    background:#FFFFFF !important;
    color:#0F172A !important;
}
</style>
""", unsafe_allow_html=True)

    # SIDEBAR TITLE
    st.sidebar.markdown(
        "<div class='sidebar-title'>📊 Dashboard</div>",
        unsafe_allow_html=True
    )

    # SIDEBAR MENU
    menu = st.sidebar.radio(
        " ",
        [
            "📈 Charts",
            "📂 Upload CSV File",
            "🕒 History",
            "👤 Profile"
        ]
    )
    
    if "username" not in st.session_state:
        st.session_state.username = "guest"
        
    csv_path = f"Data/{st.session_state.username}_expense.csv"
       
    #Charts
    if menu == "📈 Charts":
        st.markdown(
            "<h1 style='color:#0F172A;font-weight:800;'>📊 Analytics Charts of Expense</h1>",
            unsafe_allow_html=True
        )

        try:
            if not os.path.exists(csv_path):
                st.warning("⚠️ No data file found. Please go to 'Upload CSV File' tab to process a statement first!")
                return

            b = pd.read_csv(csv_path)
            b = b.drop_duplicates()
            b.columns = b.columns.str.strip()

            b["Date"] = pd.to_datetime(b["Date"], format="%d.%m.%Y", errors="coerce")

            b = b[b["Date"].notna()].copy()

            if b.empty:
                st.info("No valid dated transactions found yet. Upload a statement to see your charts.")
                return

            b['month'] = b['Date'].dt.month
            b['month_name'] = b['Date'].dt.month_name()
            
            b["Amount"] = b["Amount"].astype(str).str.replace(",", "").str.replace("₹", "")
            b["Amount"] = pd.to_numeric(b["Amount"], errors="coerce").fillna(0)
            
            b["Description"] = b["Description"].fillna("Unknown").astype(str).str.strip().str.lower()
            b['Transaction Type'] = b['Transaction Type'].fillna("Unknown").astype(str).str.strip().str.lower()
            
            colf1, colf2, colf3 = st.columns(3) 

            if "view" not in st.session_state:
                st.session_state.view = "All"

            with colf1:
                if st.button("📅 All Data", use_container_width=True):
                    st.session_state.view = "All"
            with colf2:
                if st.button("📆 Monthly", use_container_width=True):
                    st.session_state.view = "Monthly"
            with colf3:
                if st.button("📈 Yearly", use_container_width=True):
                    st.session_state.view = "Yearly"

            view = st.session_state.view
            filtered_df = b.copy()

            if view == "Monthly":
                available_months = sorted(b["Date"].dt.month_name().dropna().unique())
                if available_months:
                    month = st.selectbox("Select Month", available_months)
                    filtered_df = b[b["Date"].dt.month_name() == month]
            elif view == "Yearly":
                available_years = sorted(b["Date"].dt.year.dropna().unique())
                if available_years:
                    year = st.selectbox("Select Year", [int(y) for y in available_years])
                    filtered_df = b[b["Date"].dt.year == year]

            if filtered_df.empty:
                st.info("No logs matched the timeline frame filter selected.")
                return

            col1, col2 = st.columns(2)

            CHART_FONT = dict(family="Arial, sans-serif", color="#0F172A")
            CHART_PALETTE = ["#2563EB", "#0EA5E9", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#14B8A6", "#64748B"]

            def style_chart(fig, title):
                wrapped_title = "<br>".join(textwrap.wrap(title, width=28)) or title
                fig.update_layout(
                    title=dict(
                        text=wrapped_title,
                        x=0.03,
                        xanchor="left",
                        font=dict(size=15, color="#0F172A", family="Arial, sans-serif")
                    ),
                    plot_bgcolor="#FFFFFF",
                    paper_bgcolor="#FFFFFF",
                    font=CHART_FONT,
                    legend=dict(font=dict(color="#334155")),
                    margin=dict(t=70, b=40, l=40, r=20),
                )
                fig.update_xaxes(showgrid=True, gridcolor="#E2E8F0", linecolor="#E2E8F0", tickfont=dict(color="#64748B"))
                fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0", linecolor="#E2E8F0", tickfont=dict(color="#64748B"))
                return fig

            a = filtered_df.groupby(['month', 'month_name'])['Amount'].sum().reset_index().sort_values('month')
            fig = px.line(
                a, x="month_name", y="Amount",
                title="Expense Distribution Over Month", markers=True,
                color_discrete_sequence=["#2563EB"]
            )
            fig.update_traces(line=dict(width=3), marker=dict(size=9, color="#2563EB", line=dict(width=2, color="#FFFFFF")))
            fig.update_layout(xaxis_title="Month", yaxis_title="Total Amount (₹)")
            style_chart(fig, "📈 Expense Distribution Over Month")

            c = filtered_df.groupby(['Description'])['Amount'].sum().reset_index()
            c = c.sort_values(by="Amount", ascending=False)

            if len(c) > 8:
             top_8 = c.head(8)
             others_amount = c.iloc[8:]['Amount'].sum()
             others_row = pd.DataFrame([{"Description": "Others", "Amount": others_amount}])
             c = pd.concat([top_8, others_row], ignore_index=True)

            fig2 = px.bar(
                c,
                x="Description",
                y="Amount",
                title="Expense by Merchant (Top Categories)",
                color="Amount",
                color_continuous_scale=["#BFDBFE", "#2563EB"]  
            )

            fig2.update_layout(
                xaxis_title="Merchant / Description",
                yaxis_title="Total Amount (₹)",
                coloraxis_showscale=False,       
                uniformtext_minsize=8,           
                uniformtext_mode='hide'         
            )
            style_chart(fig2, "🏬 Expense by Merchant (Top Categories)")

            fig2.update_traces(
                texttemplate='₹%{y:,.2f}',      
                textposition='outside',         
                textfont=dict(color="#334155", size=11)
            )

            fig2.update_xaxes(tickangle=45)
 
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)

            col3, col4 = st.columns(2)
             
            d = filtered_df.groupby(['Transaction Type'])['Amount'].sum().reset_index()
            fig3 = px.pie(
                d, names='Transaction Type', values='Amount',
                title='Credit vs Debit', color_discrete_sequence=["#2563EB", "#F59E0B", "#10B981"]
            )
            fig3.update_traces(
                textposition="inside", textinfo="percent+label", hole=0.45,
                textfont=dict(color="#FFFFFF", size=13),
                marker=dict(line=dict(color="#FFFFFF", width=2))
            )
            style_chart(fig3, "💳 Credit vs Debit")

            daily = filtered_df.groupby(['Date'])['Amount'].sum().reset_index()
            fig4 = px.line(
                daily, x='Date', y='Amount', markers=True,
                title="Daily Spending Profile Flow", color_discrete_sequence=["#10B981"]
            )
            fig4.update_traces(line=dict(width=3), marker=dict(size=7, color="#10B981", line=dict(width=2, color="#FFFFFF")))
            fig4.update_layout(xaxis_title="Date", yaxis_title="Amount (₹)")
            style_chart(fig4, "🗓️ Daily Spending Profile Flow")
            
            with col3:
                st.plotly_chart(fig3, use_container_width=True)
            with col4:
                st.plotly_chart(fig4, use_container_width=True)

           

            st.write("")

            b_hist = b.copy()
            b_hist['year_month'] = b_hist['Date'].dt.to_period('M')
            monthly_totals = (
                b_hist.groupby('year_month')['Amount'].sum()
                .reset_index()
                .sort_values('year_month')
            )

            _, fc_center, _ = st.columns([1, 6, 1])
            with fc_center:
                if len(monthly_totals) >= 2:
                    x = np.arange(len(monthly_totals))
                    y = monthly_totals['Amount'].values
                    slope, intercept = np.polyfit(x, y, 1)

                    n_future = 3
                    future_x = np.arange(len(monthly_totals), len(monthly_totals) + n_future)
                    future_y = np.clip(slope * future_x + intercept, 0, None)
                    future_periods = pd.period_range(
                        monthly_totals['year_month'].iloc[-1] + 1, periods=n_future, freq='M'
                    )

                    forecast_df = pd.DataFrame({
                        "Month": [str(p) for p in monthly_totals['year_month']] + [str(p) for p in future_periods],
                        "Amount": list(y) + list(future_y),
                        "Type": ["Actual"] * len(y) + ["Forecast"] * n_future
                    })

                    fig5 = px.line(
                        forecast_df, x="Month", y="Amount", color="Type", markers=True,
                        title="Spending Forecast (Next 3 Months)",
                        color_discrete_map={"Actual": "#2563EB", "Forecast": "#F59E0B"}
                    )
                    fig5.update_traces(line=dict(width=3), marker=dict(size=8))
                    fig5.update_layout(xaxis_title="Month", yaxis_title="Amount (₹)")
                    style_chart(fig5, "🔮 Spending Forecast (Next 3 Months)")

                    st.plotly_chart(fig5, use_container_width=True)
                    st.caption(
                        "Forecast is a simple linear trend over your full transaction history "
                        "(not just the current filter) — treat it as a rough projection, not a guarantee."
                    )
                else:
                    st.info("📉 Need at least 2 months of transaction history to generate a spending forecast.")

            #AI
            st.write("")
            st.markdown(
                "<h3 style='color:#0F172A;font-weight:800;'>🤖 Ask AI About This Data</h3>",
                unsafe_allow_html=True
            )
            st.caption(f"Answers are based on the **{view}** view currently selected above.")

            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            summary_by_type = filtered_df.groupby('Transaction Type')['Amount'].sum()
            summary_by_desc = filtered_df.groupby('Description')['Amount'].sum().sort_values(ascending=False)
            summary_by_month = filtered_df.groupby('month_name')['Amount'].sum()

            data_summary = f"""
Filter applied: {view}
Date range: {filtered_df['Date'].min().date()} to {filtered_df['Date'].max().date()}
Total transactions: {len(filtered_df)}
Total amount: ₹{filtered_df['Amount'].sum():,.2f}

Spending by Transaction Type:
{summary_by_type.to_string()}

Spending by Month:
{summary_by_month.to_string()}

Top merchants/descriptions by total spend:
{summary_by_desc.head(15).to_string()}
""".strip()

            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            question = st.chat_input("e.g. How much did I spend on food this month?")

            if question:
                st.session_state.chat_history.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)

                try:
                    chat_api_key = st.secrets["GEMINI_API_KEY"]
                except Exception:
                    chat_api_key = os.environ.get("GEMINI_API_KEY", "")

                prompt = f"""You are a helpful personal finance assistant embedded in an expense tracker app.
Answer the user's question using ONLY the transaction summary below - do not invent numbers.
Be concise (2-4 sentences), use ₹ for amounts, and if the summary doesn't have enough detail
to answer precisely, say so instead of guessing.

TRANSACTION SUMMARY:
{data_summary}

QUESTION: {question}
"""
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            chat_client = genai.Client(api_key=chat_api_key)
                            response = chat_client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=prompt
                            )
                            answer = response.text.strip()
                        except Exception as e:
                            answer = f"Sorry, I couldn't process that right now. ({e})"
                        st.markdown(answer)

                st.session_state.chat_history.append({"role": "assistant", "content": answer})

        except Exception as e:
            st.error(f"Error rendering dashboard analytics metrics: {e}")
    elif menu == "📂 Upload CSV File":
        st.title("📂 Universal Bank Statement PDF Parser")

        csv_path = f"Data/{st.session_state.username}_expense.csv"
        file = st.file_uploader("Upload Bank PDF Statement", type=["pdf"])

        # --- Modern API Client Initialization ---
        try:
            api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            api_key = os.environ.get("GEMINI_API_KEY", "YOUR_FALLBACK_API_KEY")

        client = genai.Client(api_key=api_key)

        if file is not None:
            final_transactions = [] 
            os.makedirs("Data", exist_ok=True)
            
            with st.spinner("🤖 AI is reading, extracting, and categorizing your statement... Please wait."):
                try:
                    full_text_content = ""
                    with pdfplumber.open(file) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text: 
                                full_text_content += text + "\n"

                    if not full_text_content.strip():
                        st.error("❌ Could not read text from this PDF.")
                    else:
                        # Advanced Prompt with explicit rules for varied, messy descriptions
                        prompt = f"""
                        You are an expert financial analyst and data parser. Extract the full transaction history from the bank statement text below.
                        
                        Return the output STRICTLY as a JSON array of objects. 
                        Do not wrap it in markdown code blocks like ```json. Just raw valid JSON.
                        
                        Each object must have exactly these keys:
                        - "Date": The exact date of transaction formatted as DD.MM.YYYY (If year is missing, append 2026).
                        - "Description": Cleaned merchant name or transaction purpose (e.g., convert "UPI-STORE-1234@okaxis" to "Store", "FLIPKART INTERNET" to "Flipkart").
                        - "Category": Categorize the transaction into EXACTLY one of these standard buckets based on these rules:
                          * "Groceries & Dining": For local supermarkets, vegetable vendors, grocery stores, restaurants, Swiggy, Zomato, food courts.
                          * "Shopping & Electronics": For Flipkart, Amazon, Haier, home appliances, clothing, retail stores, Myntra.
                          * "Utilities & Bills": For mobile recharge (Jio, Airtel), electricity boards, Wi-Fi, rent, gas, DTH, insurance premium.
                          * "Entertainment & Leisure": For movie theatres, Netflix, stories, books, hotels, travel tickets, Spotify.
                          * "Salary & Income": For salary credits, bank interest payments, cash deposits, dividends, cashbacks.
                          * "Transfer & Others": For generic UPI transactions to friends/family, bank fees, ATM withdrawals, or uncategorized items.
                        - "Transaction Type": Must be exactly either "Debit" or "Credit".
                        - "Amount": The transaction cost as a floating-point number.
                        - "Balance": The running account balance right after that transaction as a floating-point number.

                        Bank Statement Text:
                        {full_text_content}
                        """

                        # Using gemini-3.1-flash-lite 
                        response = client.models.generate_content(
                            model="gemini-3.1-flash-lite",
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json"
                            ),
                        )

                        final_transactions = json.loads(response.text)

                except Exception as e:
                    st.error(f"❌ An error occurred during AI extraction: {e}")

            if final_transactions:
                new_df = pd.DataFrame(final_transactions)
            
                new_df["Amount"] = pd.to_numeric(new_df["Amount"], errors='coerce').fillna(0.0)
                new_df["Balance"] = pd.to_numeric(new_df["Balance"], errors='coerce').fillna(0.0)
                
                if "Category" not in new_df.columns:
                    new_df["Category"] = "Transfer & Others"

                if os.path.exists(csv_path):
                    try:
                        existing_df = pd.read_csv(csv_path)
                        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    except Exception:
                        combined_df = new_df
                else:
                    combined_df = new_df

                combined_df = combined_df.drop_duplicates(subset=["Date", "Description", "Amount", "Balance"])

                combined_df.to_csv(csv_path, index=False)
                
                st.success(f"Successfully processed and synced transactions! Total history records: {len(combined_df)} 🚀")
                
                st.subheader("📊 Expense Distribution by Category")
                
                debit_df = combined_df[combined_df["Transaction Type"] == "Debit"]
                
                if not debit_df.empty:
                    category_data = debit_df.groupby("Category")["Amount"].sum().reset_index()
                    
                    category_data = category_data.sort_values(by="Amount", ascending=False)
                    
                    col1, col2 = st.columns([2, 1])
                    
                   # with col1:
                        # Display clean bar chart without description clutter
                       # st.bar_chart(
                         #   data=category_data, 
                          #  x="Category", 
                           # y="Amount", 
                            #use_container_width=True
                        #)
                        
                   # with col2:
                        # Numerical breakdowns next to the chart
                       # st.write("### 💰 Total Spent")
                        #for idx, row in category_data.iterrows():
                          #  st.metric(label=row["Category"], value=f"₹{row['Amount']:,.2f}")
                else:
                    st.info("No debit transactions found to plot.")
                
                st.divider()
                st.write("### 📝 Full Transaction History")
                render_light_table(combined_df, max_rows=200)
                
                # Download File Button
                csv_data = combined_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Updated Historical CSV",
                    data=csv_data,
                    file_name=f"{st.session_state.username}_expense.csv",
                    mime="text/csv"
                )
            else:
                st.error("Could not parse transactions automatically.")
    elif menu == "🕒 History":
        st.title("📜 Expense History")
        
        if os.path.exists(csv_path):
            try:
                file_mod_time = os.path.getmtime(csv_path)
                formatted_time = datetime.fromtimestamp(file_mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                st.info(f"🕒 History last updated on: {formatted_time}")
                data = pd.read_csv(csv_path)
                render_light_table(data, max_rows=200)

                st.write("")
                if st.button("🗑️ Clear History", type="primary", use_container_width=True):
                    os.remove(csv_path)
                    excel_path = "Data/expense.xlsx"
                    if os.path.exists(excel_path):
                        os.remove(excel_path)
                        
                    st.success("History cleared successfully! 🧹")
                    st.rerun()
            except Exception as e:
                st.error(f"Error loading history data: {e}")
        else:
            st.warning("No Expense History Found")

   
    #Profile
    elif menu == "👤 Profile":

        st.markdown("""
        <style>
        .profile-hero{
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            border-radius:20px;
            padding:32px;
            margin-bottom:24px;
            display:flex;
            align-items:center;
            gap:22px;
            box-shadow:0 4px 14px rgba(15,23,42,0.04);
        }
        .profile-avatar{
            width:72px;
            height:72px;
            min-width:72px;
            border-radius:50%;
            background:#2563EB;
            color:#FFFFFF;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:28px;
            font-weight:800;
            letter-spacing:1px;
        }
        .profile-name{
            font-size:24px;
            font-weight:800;
            color:#0F172A;
            margin:0;
        }
        .profile-username{
            font-size:15px;
            color:#64748B;
            margin:2px 0 0 0;
        }
        .profile-card{
            background:#FFFFFF;
            border:1px solid #E2E8F0;
            border-radius:16px;
            padding:26px;
            margin-bottom:20px;
            box-shadow:0 4px 14px rgba(15,23,42,0.03);
        }
        .profile-section-title{
            font-size:16px;
            font-weight:700;
            color:#0F172A;
            margin-bottom:16px;
            text-transform:uppercase;
            letter-spacing:0.5px;
        }
        .info-row{
            display:flex;
            justify-content:space-between;
            align-items:center;
            background:#F8FAFC;
            border:1px solid #E2E8F0;
            padding:14px 18px;
            border-radius:12px;
            margin-bottom:10px;
        }
        .info-label{
            font-size:14px;
            color:#64748B;
            font-weight:600;
        }
        .info-value{
            font-size:15px;
            color:#0F172A;
            font-weight:600;
            text-align:right;
        }
        </style>
        """, unsafe_allow_html=True)

        initials = "".join([w[0] for w in str(st.session_state.full_name).split()[:2]]).upper() or "U"

        st.markdown(
            f"""
            <div class="profile-hero">
                <div class="profile-avatar">{initials}</div>
                <div>
                    <p class="profile-name">{st.session_state.full_name}</p>
                    <p class="profile-username">@{st.session_state.username} · {st.session_state.email}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        hidden_password = "•" * len(st.session_state.password)

        st.markdown(
            f"""
            <div class="profile-card">
                <div class="profile-section-title">Account Information</div>
                <div class="info-row">
                    <span class="info-label">👨 Full Name</span>
                    <span class="info-value">{st.session_state.full_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">📧 Email</span>
                    <span class="info-value">{st.session_state.email}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🪪 Username</span>
                    <span class="info-value">{st.session_state.username}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🔒 Password</span>
                    <span class="info-value">{hidden_password}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">🕒 Login Time</span>
                    <span class="info-value">{st.session_state.login_time}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="profile-section-title">💬 Feedback</div>', unsafe_allow_html=True)

        feedback = st.text_area(
            "Write your feedback here...",
            height=120,
            label_visibility="collapsed",
            placeholder="Tell us what you think or what you'd like to see improved..."
        )

        if st.button("📩 Send Feedback", use_container_width=True):
            if not feedback.strip():
                st.warning("Please write some feedback before sending.")
            else:
                ok, err = send_feedback_email(
                    st.session_state.full_name,
                    st.session_state.username,
                    st.session_state.email,
                    feedback
                )
                if ok:
                    st.success("Feedback Sent Successfully ✅")
                else:
                    st.error(f"Couldn't send feedback: {err}")

        st.markdown('</div>', unsafe_allow_html=True)

        contact_email = "support@example.com"
        contact_phone = "+91 00000 00000"
        try:
            contact_email = st.secrets.get("CONTACT_EMAIL", contact_email)
            contact_phone = st.secrets.get("CONTACT_PHONE", contact_phone)
        except Exception:
            pass

        st.markdown(
            f"""
            <div class="profile-card" style="text-align:center;">
                <div class="profile-section-title">📞 Contact Us</div>
                <p style="color:#334155;font-size:15px;margin:6px 0;">📧 {contact_email}</p>
                <p style="color:#334155;font-size:15px;margin:6px 0;">📱 {contact_phone}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write("")

    # LOGOUT
        if st.button(
        "🚪 Logout",
        use_container_width=True
    ):
          token = st.session_state.get("session_token")
          if token:
              delete_session(token)
              st.query_params.pop("token", None)
          st.session_state.logged_in = False
          st.rerun()