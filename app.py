import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load config
with open("users.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", location="sidebar")

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

    with st.expander("➕ Add New Appointment"):
        with st.form("appointment_form"):
            customer_name = st.text_input("Customer Name")
            service_type = st.selectbox("Service Type", ["Facial", "Massage", "Nails", "Hair", "Other"])
            appointment_time = st.datetime_input("Appointment Time", min_value=datetime.now())
            employee_name = st.selectbox("Employee", ["Khaliun", "Amarlin", "Tuul", "Dul"])
            submitted = st.form_submit_button("Add Appointment")

            if submitted:
                c.execute("SELECT * FROM appointments WHERE appointment_time=? AND employee_name=? AND status='Scheduled'",
                          (appointment_time.isoformat(), employee_name))
                conflict = c.fetchone()
                if conflict:
                    st.warning("❗ This employee already has an appointment at this time.")
                else:
                    c.execute("INSERT INTO appointments (customer_name, service_type, appointment_time, employee_name, status, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                              (customer_name, service_type, appointment_time.isoformat(), employee_name, "Scheduled", username))
                    conn.commit()
                    st.success("✅ Appointment added!")

    st.subheader("📋 Appointments List")
    df = pd.read_sql("SELECT * FROM appointments", conn)
    if role == 'employee':
        df = df[df['employee_name'] == config['credentials']['usernames'][username]['name']]

    with st.expander("📆 Calendar View"):
        if not df.empty:
            df['appointment_time'] = pd.to_datetime(df['appointment_time'])
            df['hour'] = df['appointment_time'].dt.hour
            df['date'] = df['appointment_time'].dt.date.astype(str)
            cal = px.timeline(df, x_start='appointment_time', x_end=df['appointment_time'] + pd.to_timedelta(1, unit='h'),
                              y='employee_name', color='status', hover_data=['customer_name', 'service_type'])
            cal.update_yaxes(autorange="reversed")
            st.plotly_chart(cal, use_container_width=True)
        else:
            st.info("No appointments yet.")

    status_filter = st.selectbox("Filter by Status", ["All"] + df['status'].unique().tolist())
    if status_filter != "All":
        df = df[df['status'] == status_filter]
    st.dataframe(df.sort_values(by='appointment_time'))

    if role == 'employee':
        st.subheader("✅ Update Appointment Status")
        my_appointments = df[df['status'] == 'Scheduled']
        for _, row in my_appointments.iterrows():
            if st.button(f"Mark {row['id']} as Completed"):
                c.execute("UPDATE appointments SET status='Completed' WHERE id=?", (row['id'],))
                conn.commit()
                st.success(f"Appointment {row['id']} marked as completed.")

    if role == 'manager':
        st.subheader("📊 Manager Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Appointments", len(df))
        with col2:
            st.metric("Completed", len(df[df['status'] == 'Completed']))
        fig = px.histogram(df, x='employee_name', color='status', barmode='group')
        st.plotly_chart(fig)
        st.download_button("📥 Export to Excel", data=df.to_csv(index=False).encode(), file_name="appointments.csv", mime="text/csv")

elif authentication_status is False:
    st.error("Username/password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")