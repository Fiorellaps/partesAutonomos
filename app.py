import streamlit as st

st.set_page_config(page_title="Partes", page_icon="📝", layout="centered", initial_sidebar_state="collapsed")

import ui

ui.inject_css()

pages = [st.Page("views/generar.py", title="Generación de Partes", icon="📝", default=True)]
st.navigation(pages).run()
