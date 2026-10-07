"""auth.py – Password hashing and session helpers using bcrypt."""
import bcrypt
import streamlit as st


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def get_session_user():
    return st.session_state.get("user")


def set_session_user(user: dict):
    st.session_state["user"] = user


def clear_session():
    st.session_state["user"] = None


def require_role(*roles):
    """Return True if logged-in user has one of the given roles."""
    user = get_session_user()
    return user is not None and user.get("role") in roles
