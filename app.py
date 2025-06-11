
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from streamlit_calendar import calendar

# Load config
with open("users.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

# Initialize DB
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    service_type TEXT,
                    appointment_time TEXT,
                    employee_name TEXT,
                    status TEXT,
                    created_by TEXT
                )''')
    conn.commit()

init_db()

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}!")
    role = config['credentials']['usernames'][username]['role']
    st.title("📅 Ayalguu Beauty/Spa Appointments")

    # Calendar using streamlit-calendar
    st.subheader("📆 Calendar View")
    df = pd.read_sql("SELECT * FROM appointments", conn)
    if not df.empty:
        df['start'] = pd.to_datetime(df['appointment_time'])
        df['end'] = df['start'] + pd.Timedelta(hours=1)
        df['title'] = df['customer_name'] + " - " + df['service_type']
        events = df[['title', 'start', 'end', 'status']].to_dict('records')
        calendar(events=events, options={'editable': False})
    else:
        st.info("No appointments to show.")

elif authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
