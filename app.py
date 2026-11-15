import streamlit as st

st.set_page_config(page_title="Gestión", page_icon="🛠️", layout="centered", initial_sidebar_state="auto")

import auth
import ui

ui.inject_css()
auth.require_login()

pages = [st.Page(m.path, title=m.title, icon=m.icon, url_path=m.url, default=m.url == "inicio") for m in ui.MODULOS]
pg = st.navigation(pages, position="sidebar")
# «Partes» está pensado para el móvil (formulario estrecho); el resto son tablas y van a ancho completo.
st.set_page_config(layout="centered" if pg.url_path == "partes" else "wide")

with st.sidebar:
    st.button("🚪 Cerrar sesión", on_click=auth.logout, use_container_width=True, type="tertiary")

ui.show_flash()
pg.run()
