# app.py
import os
import streamlit as st


def load_users():
    """
    Load allowed users from Streamlit secrets or env.
    - st.secrets["users"] should be a dict of {username: password}
    - fallback: APP_USERS env like "user1:pass1,user2:pass2"
    """
    users = {}
    if "users" in st.secrets:
        users = dict(st.secrets["users"])
    elif os.getenv("APP_USERS"):
        pairs = [p.strip() for p in os.getenv("APP_USERS", "").split(",") if ":" in p]
        users = {p.split(":", 1)[0]: p.split(":", 1)[1] for p in pairs}
    return users


def login(users):
    st.title("NFL Picks Dashboard - Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state["auth"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Invalid username or password")


def main():
    users = load_users()
    if not users:
        st.error("No users configured. Add users to st.secrets['users'] or APP_USERS env (user:pass,user2:pass2).")
        return

    if "auth" not in st.session_state:
        st.session_state["auth"] = False

    if not st.session_state["auth"]:
        login(users)
        return

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Predictions", "Performance"])

    if page == "Predictions":
        import Predictions as p
        p.run()
    else:
        import Performance as perf
        perf.run()


if __name__ == "__main__":
    main()
