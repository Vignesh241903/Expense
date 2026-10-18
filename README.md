# 💸 Expense Analytics Dashboard

An AI-powered personal expense tracker and analytics dashboard built with **Streamlit**, **PostgreSQL**, and **Google Gemini AI**.

---

## ✨ Features

- **🔐 Authentication & Session Persistence**: Secure user registration and login with session management backed by PostgreSQL.
- **📊 Interactive Analytics**: Visualizations of spending patterns, category distributions, monthly trends, and expense metrics using **Plotly**.
- **📄 AI-Powered PDF Statement Parsing**: Automatically extract and categorize transactions from bank statement PDFs using **Google Gemini 2.5/3.6 Flash**.
- **💬 Finance AI Assistant**: In-dashboard conversational assistant to ask natural-language questions about your spending habits.
- **✉️ Feedback System**: Built-in user feedback reporting with automated SMTP email delivery.

---

## 📁 Project Structure

```text
Expense/
├── .streamlit/
│   ├── config.toml               # Streamlit UI theme configuration
│   └── secrets.toml.example      # Template for API keys and credentials
├── Data/
│   └── .gitkeep                  # Local storage folder for user CSVs (ignored in Git)
├── .gitignore                    # Prevents secrets, cache, and user data from being committed
├── dashboard.py                  # Main analytics dashboard & AI chat logic
├── db.py                         # PostgreSQL database connection and session models
├── expense.py                    # Main Streamlit application entrypoint
├── login.py                      # Login and user registration UI
├── test.py                       # Test script for Gemini API connectivity
├── requirements.txt              # Required Python packages
└── README.md                     # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.10+**
- **PostgreSQL** installed and running locally or in the cloud.

### 2. Clone the Repository

```bash
git clone https://github.com/Vignesh241903/Expense.git
cd Expense
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Database Setup

Ensure PostgreSQL is running and create the `expense_01` database:

```sql
CREATE DATABASE expense_01;
```

The application automatically creates the required tables (`users`, `sessions`) on its first run.

If you are using custom PostgreSQL credentials, you can set the following environment variables:
- `DB_HOST` (default: `localhost`)
- `DB_PORT` (default: `5432`)
- `DB_NAME` (default: `expense_01`)
- `DB_USER` (default: `postgres`)
- `DB_PASSWORD` (default: `postgres`)

### 6. Configure Secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` to add your credentials:

```toml
GEMINI_API_KEY = "your_google_gemini_api_key_here"

# Optional: Feedback Email Configuration
SMTP_EMAIL = "your_gmail_address@gmail.com"
SMTP_APP_PASSWORD = "your_16_char_google_app_password"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
```

> ⚠️ **Note**: `.streamlit/secrets.toml` is listed in `.gitignore` and must never be committed to GitHub.

---

## ▶️ Running the App

Start the Streamlit application:

```bash
streamlit run expense.py
```

Open your browser at `http://localhost:8501`.

---

## 🔒 Security Best Practices

- **Never commit `.env` or `secrets.toml` files**: Always keep credentials in local configuration files or environment variables.
- **User Data Isolation**: User expense data stored in `Data/*.csv` and `Data/*.xlsx` is strictly excluded from version control via `.gitignore`.