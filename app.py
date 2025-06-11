import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Page config
st.set_page_config(
    page_title="Ayalguu Beauty Salon",
    page_icon="💅",
    layout="wide"
)

name, authentication_status, username = authenticator.login("Login", location="sidebar")

# Initialize DB with enhanced schema
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    customer_phone TEXT,
                    service_type TEXT,
                    service_duration INTEGER,
                    service_price REAL,
                    appointment_date TEXT,
                    appointment_time TEXT,
                    employee_name TEXT,
                    status TEXT,
                    notes TEXT,
                    created_by TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )''')
    conn.commit()

init_db()

# Service configurations
SERVICES = {
    "Facial Treatment": {"duration": 60, "price": 50000},
    "Full Body Massage": {"duration": 90, "price": 80000},
    "Manicure": {"duration": 45, "price": 25000},
    "Pedicure": {"duration": 60, "price": 30000},
    "Hair Cut & Style": {"duration": 120, "price": 45000},
    "Hair Coloring": {"duration": 180, "price": 70000},
    "Eyebrow Shaping": {"duration": 30, "price": 15000},
    "Eyelash Extension": {"duration": 120, "price": 60000}
}

EMPLOYEES = ["Khaliun", "Amarlin", "Tuul", "Dul"]

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    role = config['credentials']['usernames'][username]['role']
    
    # Sidebar info
    st.sidebar.title(f"Welcome {name}!")
    st.sidebar.info(f"Role: {role.title()}")
    
    # Main header
    st.title("💅 Ayalguu Beauty Salon - Appointment Management")
    
    # Role-based navigation
    if role == 'manager':
        tab1, tab2, tab3, tab4 = st.tabs(["📅 Appointments", "➕ New Booking", "📊 Manager Dashboard", "👥 Employee Performance"])
    else:
        tab1, tab2 = st.tabs(["📅 My Appointments", "➕ New Booking"])
    
    # Tab 1: Appointments List
    with tab1:
        st.subheader("📋 Appointments Overview")
        
        # Fetch appointments based on role
        if role == 'manager':
            df = pd.read_sql("SELECT * FROM appointments ORDER BY appointment_date, appointment_time", conn)
            st.info("👨‍💼 Manager View: All appointments")
        else:
            employee_name = config['credentials']['usernames'][username]['name']
            df = pd.read_sql("SELECT * FROM appointments WHERE employee_name=? ORDER BY appointment_date, appointment_time", 
                           conn, params=(employee_name,))
            st.info(f"👩‍💼 Employee View: {employee_name}'s appointments")
        
        if not df.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All"] + df['status'].unique().tolist())
            with col2:
                if role == 'manager':
                    employee_filter = st.selectbox("Filter by Employee", ["All"] + df['employee_name'].unique().tolist())
                else:
                    employee_filter = "All"
            with col3:
                date_filter = st.date_input("Filter by Date", value=None)
            
            # Apply filters
            filtered_df = df.copy()
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            if employee_filter != "All" and role == 'manager':
                filtered_df = filtered_df[filtered_df['employee_name'] == employee_filter]
            if date_filter:
                filtered_df = filtered_df[filtered_df['appointment_date'] == str(date_filter)]
            
            # Display appointments with action buttons
            for _, row in filtered_df.iterrows():
                with st.expander(f"🕐 {row['appointment_date']} {row['appointment_time']} - {row['customer_name']} ({row['status']})"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Customer:** {row['customer_name']}")
                        st.write(f"**Phone:** {row['customer_phone']}")
                        st.write(f"**Service:** {row['service_type']}")
                        st.write(f"**Duration:** {row['service_duration']} min")
                        st.write(f"**Price:** ₮{row['service_price']:,.0f}")
                    with col2:
                        st.write(f"**Employee:** {row['employee_name']}")
                        st.write(f"**Status:** {row['status']}")
                        st.write(f"**Created by:** {row['created_by']}")
                        if row['notes']:
                            st.write(f"**Notes:** {row['notes']}")
                    
                    # Action buttons based on role and status
                    col1, col2, col3, col4 = st.columns(4)
                    if row['status'] == 'Scheduled':
                        with col1:
                            if st.button(f"✅ Complete", key=f"complete_{row['id']}"):
                                c.execute("UPDATE appointments SET status='Completed', updated_at=? WHERE id=?", 
                                        (datetime.now().isoformat(), row['id']))
                                conn.commit()
                                st.success("Appointment completed!")
                                st.rerun()
                        
                        with col2:
                            if st.button(f"❌ Cancel", key=f"cancel_{row['id']}"):
                                c.execute("UPDATE appointments SET status='Cancelled', updated_at=? WHERE id=?", 
                                        (datetime.now().isoformat(), row['id']))
                                conn.commit()
                                st.success("Appointment cancelled!")
                                st.rerun()
                        
                        if role == 'manager':
                            with col3:
                                if st.button(f"🔄 Reschedule", key=f"reschedule_{row['id']}"):
                                    st.session_state[f'reschedule_{row["id"]}'] = True
                            
                            with col4:
                                if st.button(f"🗑️ Delete", key=f"delete_{row['id']}"):
                                    c.execute("DELETE FROM appointments WHERE id=?", (row['id'],))
                                    conn.commit()
                                    st.success("Appointment deleted!")
                                    st.rerun()
        else:
            st.info("No appointments found.")
    
    # Tab 2: New Booking
    with tab2:
        st.subheader("➕ Create New Appointment")
        
        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                customer_name = st.text_input("Customer Name *", placeholder="Enter customer name")
                customer_phone = st.text_input("Customer Phone *", placeholder="+976 XXXXXXXX")
                service_type = st.selectbox("Service Type *", list(SERVICES.keys()))
                appointment_date = st.date_input("Appointment Date *", min_value=datetime.now().date())
            
            with col2:
                appointment_time = st.time_input("Appointment Time *")
                employee_name = st.selectbox("Assigned Employee *", EMPLOYEES)
                notes = st.text_area("Additional Notes", placeholder="Any special requirements...")
                
                # Show service details
                if service_type:
                    st.info(f"Duration: {SERVICES[service_type]['duration']} min | Price: ₮{SERVICES[service_type]['price']:,.0f}")
            
            submitted = st.form_submit_button("📅 Book Appointment", use_container_width=True)
            
            if submitted:
                if not customer_name or not customer_phone:
                    st.error("Please fill in all required fields!")
                else:
                    # Check for conflicts
                    appointment_datetime = datetime.combine(appointment_date, appointment_time)
                    service_end_time = appointment_datetime + timedelta(minutes=SERVICES[service_type]['duration'])
                    
                    c.execute("""SELECT * FROM appointments 
                               WHERE employee_name=? AND appointment_date=? AND status='Scheduled'""",
                            (employee_name, str(appointment_date)))
                    existing_appointments = c.fetchall()
                    
                    conflict = False
                    for existing in existing_appointments:
                        existing_start = datetime.fromisoformat(f"{existing[6]} {existing[7]}")
                        existing_end = existing_start + timedelta(minutes=existing[4])
                        
                        if (appointment_datetime < existing_end and service_end_time > existing_start):
                            conflict = True
                            st.error(f"⚠️ Time conflict with existing appointment at {existing[7]}")
                            break
                    
                    if not conflict:
                        c.execute("""INSERT INTO appointments 
                                   (customer_name, customer_phone, service_type, service_duration, service_price,
                                    appointment_date, appointment_time, employee_name, status, notes, created_by, created_at) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (customer_name, customer_phone, service_type, SERVICES[service_type]['duration'],
                                 SERVICES[service_type]['price'], str(appointment_date), str(appointment_time),
                                 employee_name, "Scheduled", notes, username, datetime.now().isoformat()))
                        conn.commit()
                        st.success("✅ Appointment booked successfully!")
                        st.balloons()
    
    # Manager-only tabs
    if role == 'manager':
        # Tab 3: Manager Dashboard
        with tab3:
            st.subheader("📊 Business Analytics Dashboard")
            
            # Key metrics
            today = datetime.now().date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            col1, col2, col3, col4 = st.columns(4)
            
            # Today's stats
            today_appointments = pd.read_sql(
                "SELECT * FROM appointments WHERE appointment_date=?", 
                conn, params=(str(today),)
            )
            with col1:
                st.metric("Today's Appointments", len(today_appointments))
            
            # This week's stats
            week_appointments = pd.read_sql(
                "SELECT * FROM appointments WHERE appointment_date>=?", 
                conn, params=(str(week_start),)
            )
            with col2:
                st.metric("This Week", len(week_appointments))
            
            # This month's revenue
            month_completed = pd.read_sql(
                "SELECT * FROM appointments WHERE appointment_date>=? AND status='Completed'", 
                conn, params=(str(month_start),)
            )
            month_revenue = month_completed['service_price'].sum() if not month_completed.empty else 0
            with col3:
                st.metric("Monthly Revenue", f"₮{month_revenue:,.0f}")
            
            # Completion rate
            total_scheduled = len(pd.read_sql("SELECT * FROM appointments WHERE status IN ('Scheduled', 'Completed', 'Cancelled')", conn))
            completed = len(pd.read_sql("SELECT * FROM appointments WHERE status='Completed'", conn))
            completion_rate = (completed / total_scheduled * 100) if total_scheduled > 0 else 0
            with col4:
                st.metric("Completion Rate", f"{completion_rate:.1f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Appointments by status
                if not df.empty:
                    status_counts = df['status'].value_counts()
                    fig_status = px.pie(values=status_counts.values, names=status_counts.index, 
                                      title="Appointments by Status")
                    st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Revenue by service
                completed_df = df[df['status'] == 'Completed']
                if not completed_df.empty:
                    service_revenue = completed_df.groupby('service_type')['service_price'].sum().sort_values(ascending=False)
                    fig_revenue = px.bar(x=service_revenue.index, y=service_revenue.values, 
                                       title="Revenue by Service Type")
                    fig_revenue.update_xaxes(title="Service")
                    fig_revenue.update_yaxes(title="Revenue (₮)")
                    st.plotly_chart(fig_revenue, use_container_width=True)
            
            # Weekly trend
            if not df.empty:
                df['appointment_date'] = pd.to_datetime(df['appointment_date'])
                weekly_trend = df.groupby(df['appointment_date'].dt.to_period('D')).size().reset_index()
                weekly_trend['appointment_date'] = weekly_trend['appointment_date'].astype(str)
                
                fig_trend = px.line(weekly_trend, x='appointment_date', y=0, 
                                  title="Daily Appointments Trend")
                fig_trend.update_xaxes(title="Date")
                fig_trend.update_yaxes(title="Number of Appointments")
                st.plotly_chart(fig_trend, use_container_width=True)
        
        # Tab 4: Employee Performance
        with tab4:
            st.subheader("👥 Employee Performance Analysis")
            
            if not df.empty:
                # Employee metrics
                employee_stats = df.groupby('employee_name').agg({
                    'id': 'count',
                    'service_price': 'sum',
                    'status': lambda x: (x == 'Completed').sum()
                }).reset_index()
                employee_stats.columns = ['Employee', 'Total Appointments', 'Total Revenue', 'Completed']
                employee_stats['Completion Rate %'] = (employee_stats['Completed'] / employee_stats['Total Appointments'] * 100).round(1)
                
                st.dataframe(employee_stats, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Appointments per employee
                    fig_emp_apt = px.bar(employee_stats, x='Employee', y='Total Appointments',
                                       title="Total Appointments by Employee")
                    st.plotly_chart(fig_emp_apt, use_container_width=True)
                
                with col2:
                    # Revenue per employee
                    fig_emp_rev = px.bar(employee_stats, x='Employee', y='Total Revenue',
                                       title="Revenue Generated by Employee")
                    st.plotly_chart(fig_emp_rev, use_container_width=True)
                
                # Top performers
                st.subheader("🏆 Top Performers")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    top_appointments = employee_stats.loc[employee_stats['Total Appointments'].idxmax()]
                    st.success(f"**Most Appointments:** {top_appointments['Employee']} ({top_appointments['Total Appointments']})")
                
                with col2:
                    top_revenue = employee_stats.loc[employee_stats['Total Revenue'].idxmax()]
                    st.success(f"**Highest Revenue:** {top_revenue['Employee']} (₮{top_revenue['Total Revenue']:,.0f})")
                
                with col3:
                    top_completion = employee_stats.loc[employee_stats['Completion Rate %'].idxmax()]
                    st.success(f"**Best Completion Rate:** {top_completion['Employee']} ({top_completion['Completion Rate %']}%)")
            
            else:
                st.info("No appointment data available for analysis.")
            
            # Export functionality
            st.subheader("📥 Export Data")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Export All Appointments"):
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"appointments_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("Export Employee Performance"):
                    if not df.empty:
                        csv = employee_stats.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="Download Performance CSV",
                            data=csv,
                            file_name=f"employee_performance_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )

elif authentication_status is False:
    st.error("❌ Username/password is incorrect")
elif authentication_status is None:
    st.warning("⚠️ Please enter your username and password")
    st.info("""
    **Demo Credentials:**
    - Manager: username=`manager1`, password=`Ayalguu2025`
    - Employee: username=`Tuul`, password=`Tuul2025`
    """)
