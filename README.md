# Ayalguu Beauty/Spa Appointment Scheduler

A complete Streamlit app to manage appointments with role-based login.

## 🚀 Deploy Instructions (Streamlit Cloud)

1. Create a new GitHub repository (e.g., `appointment-scheduler`)
2. Upload these files to your GitHub repo:
   - `app.py`
   - `users.yaml`
   - `requirements.txt`
   - `README.md`
3. Visit [https://streamlit.io/cloud](https://streamlit.io/cloud)
4. Click **New app**, connect your GitHub, select this repo, then click **Deploy**.
5. App will auto-run. Login with one of the usernames in `users.yaml`.

> 💡 Use the `streamlit-authenticator` hasher to generate secure passwords:
> ```python
> from streamlit_authenticator import Hasher
> Hasher(['yourpassword']).generate()
> ```

---

## 📂 App Features

- Login system with roles (Manager/Employee)
- Add, view, filter appointments
- Interactive calendar timeline
- Manager dashboard with charts
- Export to Excel/CSV

Built for Ayalguu Beauty/Spa ✨
