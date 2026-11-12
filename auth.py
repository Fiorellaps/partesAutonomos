"""Login simple. Las credenciales se leen de st.secrets (.streamlit/secrets.toml, fuera de git)."""
from __future__ import annotations

import hmac

import streamlit as st

S = st.session_state


def _credentials() -> tuple[str, str] | None:
    try:
        return str(st.secrets["auth"]["username"]), str(st.secrets["auth"]["password"])
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def _check(user: str, pwd: str) -> bool:
    cred = _credentials()
    if cred is None:
        return False
    ok_user = hmac.compare_digest(user.encode(), cred[0].encode())
    ok_pwd = hmac.compare_digest(pwd.encode(), cred[1].encode())
    return ok_user and ok_pwd


def _submit() -> None:
    if _check(S.get("login_user", ""), S.get("login_pwd", "")):
        S["authenticated"] = True
        S["login_failed"] = False
    else:
        S["login_failed"] = True
    S.pop("login_pwd", None)


def logout() -> None:
    S["authenticated"] = False


def require_login() -> None:
    """Muestra el formulario de acceso y detiene la app si no hay sesión iniciada."""
    if S.get("authenticated"):
        return
    st.title("🔒 Acceso")
    if _credentials() is None:
        st.error("Faltan las credenciales. Crea .streamlit/secrets.toml (ver secrets.toml.example).")
        st.stop()
    with st.form("login"):
        st.text_input("Usuario", key="login_user")
        st.text_input("Contraseña", type="password", key="login_pwd")
        st.form_submit_button("Entrar", type="primary", use_container_width=True, on_click=_submit)
    if S.get("login_failed"):
        st.error("Usuario o contraseña incorrectos.")
    st.stop()
