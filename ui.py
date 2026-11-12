"""Estilos y pequeñas piezas visuales reutilizables (cabecera, tarjetas, etiquetas)."""
from __future__ import annotations

from html import escape

import streamlit as st

# Las tarjetas son st.container(border=True, key="card_…"); Streamlit añade la clase «st-key-card_…».
_CSS = """
<style>
.block-container {padding-top: 2rem; padding-bottom: 4rem;}

/* Cabecera */
.hero {
  background: linear-gradient(135deg, #0b5cab 0%, #2d8ae6 100%);
  color: #fff; padding: 1.3rem 1.5rem; border-radius: 16px; margin-bottom: .75rem;
  box-shadow: 0 8px 24px rgba(11, 92, 171, .22);
}
.hero .crumb {font-size: .75rem; letter-spacing: .08em; text-transform: uppercase; opacity: .8;}
.hero .title {font-size: 1.5rem; font-weight: 700; line-height: 1.25; margin-top: .15rem;}
.hero .sub {font-size: .92rem; opacity: .9; margin-top: .3rem;}

/* Tarjetas */
[class*="st-key-card_"] {
  background: #fff; border-radius: 14px !important; border-color: #e3e8ef !important;
  box-shadow: 0 1px 3px rgba(16, 24, 40, .06);
  transition: box-shadow .15s ease, transform .15s ease, border-color .15s ease;
}
[class*="st-key-card_"]:hover {
  box-shadow: 0 10px 26px rgba(16, 24, 40, .10); border-color: #9cc3ee !important;
}
[class*="st-key-cardlink_"]:hover {transform: translateY(-2px);}

.card-head {display: flex; align-items: center; gap: .85rem; min-width: 0;}
.card-head > div:last-child {flex: 1 1 auto; min-width: 0; overflow-wrap: anywhere;}
.card-icon {
  flex: 0 0 52px; height: 52px; border-radius: 14px; background: #e8f1fb;
  display: flex; align-items: center; justify-content: center; font-size: 1.7rem;
}
.card-title {font-weight: 700; font-size: 1.08rem; color: #1d2939; line-height: 1.3;}
.card-desc {font-size: .86rem; color: #667085; margin-top: .15rem;}
.card-meta {display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .2rem;}

/* Etiquetas */
.badge {
  display: inline-block; padding: .14rem .6rem; border-radius: 999px;
  background: #e8f1fb; color: #0b5cab; font-size: .76rem; font-weight: 600;
  max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.badge.muted {background: #f2f4f7; color: #475467;}
.badge.ok {background: #e7f6ec; color: #1a7f37;}

/* Títulos de bloque */
.section-label {
  font-size: .78rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase;
  color: #667085; margin: 1.1rem 0 .2rem;
}

/* Desplegables con aspecto de tarjeta */
[data-testid="stExpander"] details {
  background: #fff; border-radius: 12px; border-color: #e3e8ef;
  box-shadow: 0 1px 2px rgba(16, 24, 40, .04);
}
[data-testid="stExpander"] summary {font-weight: 600;}

/* Barra de acciones fija (pantalla de edición) */
/* Streamlit envuelve el contenedor en un div de su mismo alto: el sticky debe ir en ese envoltorio
   (cuyo padre es el bloque principal, que sí ocupa toda la página). */
[data-testid="stLayoutWrapper"]:has(> .st-key-stickybar) {
  position: sticky; top: 3.75rem; z-index: 999;
}
.st-key-stickybar {
  background: rgba(255, 255, 255, .96); backdrop-filter: blur(6px); padding: .5rem .6rem;
  border: 1px solid #e3e8ef; border-radius: 14px; box-shadow: 0 6px 18px rgba(16, 24, 40, .10);
}
/* En móvil Streamlit apila las columnas: aquí las mantenemos en una sola fila */
.st-key-stickybar [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: .4rem;}
.st-key-stickybar [data-testid="stColumn"] {min-width: 0 !important; width: auto !important; flex: 1 1 0 !important;}
.st-key-stickybar button {padding-left: .4rem; padding-right: .4rem; white-space: nowrap;}

/* Botones */
.stButton button, .stDownloadButton button {border-radius: 10px; font-weight: 600;}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, sub: str = "", crumb: str = "") -> None:
    html = '<div class="hero">'
    if crumb:
        html += f'<div class="crumb">{escape(crumb)}</div>'
    html += f'<div class="title">{escape(title)}</div>'
    if sub:
        html += f'<div class="sub">{escape(sub)}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def badge(text: str, kind: str = "") -> str:
    return f'<span class="badge {kind}">{escape(text)}</span>'


def card_head(icon: str, title: str, desc: str = "", badges: tuple[str, ...] = ()) -> None:
    """Cabecera de tarjeta: icono + título + descripción + etiquetas (HTML ya escapado en badges)."""
    html = f'<div class="card-head"><div class="card-icon">{escape(icon)}</div><div>'
    html += f'<div class="card-title">{escape(title)}</div>'
    if desc:
        html += f'<div class="card-desc">{escape(desc)}</div>'
    if badges:
        html += f'<div class="card-meta">{"".join(badges)}</div>'
    st.markdown(html + "</div></div>", unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(f'<div class="section-label">{escape(text)}</div>', unsafe_allow_html=True)
