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
/* Rejilla de tarjetas (ui.card_grid): todas las tarjetas del grupo con el mismo ancho y alto.
   grid-auto-rows: 1fr iguala todas las filas a la tarjeta más alta; el botón o enlace queda abajo. */
[class*="st-key-grid_"] {
  display: grid !important; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  grid-auto-rows: 1fr; gap: 1rem;
}
[class*="st-key-grid_"] > * {height: 100%; width: auto !important;}
[class*="st-key-grid_"] [class*="st-key-card"] {height: 100%; justify-content: space-between;}
/* Indicadores (métricas) */
/* Rejilla: todas las tarjetas de la fila con el mismo ancho y alto; la etiqueta reserva 2 líneas
   para que las cifras queden alineadas aunque unas etiquetas sean más largas que otras */
.kpi-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); grid-auto-rows: 1fr; gap: 1rem;}
.kpi {
  background: #fff; border: 1px solid #e3e8ef; border-radius: 14px; padding: .85rem 1rem;
  box-shadow: 0 1px 3px rgba(16, 24, 40, .06); display: flex; flex-direction: column;
}
.kpi .k-label {
  font-size: .78rem; font-weight: 600; color: #667085; text-transform: uppercase; letter-spacing: .05em;
  line-height: 1.3; min-height: 2.6em;
}
.kpi .k-sub:empty::before {content: "\\00a0";}
.kpi .k-value {font-size: 1.9rem; font-weight: 700; color: #1d2939; line-height: 1.2; margin-top: .15rem;}
.kpi .k-sub {font-size: .8rem; color: #667085;}
.kpi.warn .k-value {color: #b42318;}
/* Etiqueta de estado con el color del Excel */
.chip {
  display: inline-block; padding: .12rem .55rem; border-radius: 6px; font-size: .78rem; font-weight: 600;
  color: #1d2939; border: 1px solid rgba(16, 24, 40, .15); margin: 0 .3rem .3rem 0;
}
/* Tarjeta de cita (ui.cita_head): hora grande a la izquierda y datos del cliente.
   La dirección reserva siempre 2 líneas para que todas las tarjetas midan lo mismo. */
[class*="st-key-card_cita_"] {min-height: 172px; justify-content: center; padding: 1rem 1.1rem;}
.cita {display: flex; gap: 1.1rem; align-items: stretch; min-width: 0;}
.cita-hora {
  flex: 0 0 104px; border-radius: 14px; background: #e8f1fb; color: #0b5cab;
  display: flex; flex-direction: column; align-items: center; justify-content: center; padding: .6rem .4rem;
}
.cita-hora .h {font-size: 1.75rem; font-weight: 700; line-height: 1.1;}
.cita-hora .h.sin {font-size: 1.05rem;}
.cita-hora .d {font-size: .8rem; font-weight: 600; opacity: .85; margin-top: .2rem; text-align: center;}
.cita-body {flex: 1 1 auto; min-width: 0;}
.cita-body .nombre {font-size: 1.3rem; font-weight: 700; color: #1d2939; line-height: 1.25;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
.cita-body .dir {
  font-size: 1rem; color: #475467; margin-top: .25rem; line-height: 1.35; min-height: 2.7em;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.cita-body .meta {display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .45rem; align-items: center;}
.cita-body .meta .chip, .cita-body .meta .badge {font-size: .85rem; margin: 0;}
@media (max-width: 640px) {
  [class*="st-key-card_cita_"] {min-height: 0;}
  .cita-hora {flex-basis: 80px;}
  .cita-hora .h {font-size: 1.4rem;}
  .cita-body .nombre {font-size: 1.1rem;}
  /* En el móvil la dirección reserva 3 líneas y las etiquetas van en una sola, para igualar el alto */
  .cita-body .dir {-webkit-line-clamp: 3; min-height: 4.05em; font-size: .95rem;}
  /* etiquetas en 2 filas fijas: caben enteras y todas las tarjetas miden lo mismo */
  .cita-body .meta {height: 3.6rem; overflow: hidden; align-content: flex-start;}
  .cita-body .meta .chip, .cita-body .meta .badge {
    max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.35;
  }
}
/* Calendario mensual */
.cal {display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px;}
.cal .dow {font-size: .75rem; font-weight: 700; color: #667085; text-align: center; padding: .2rem 0;}
.cal .day {
  background: #fff; border: 1px solid #e3e8ef; border-radius: 10px; min-height: 96px; padding: .3rem .35rem;
  overflow: hidden;
}
.cal .day.out {background: #f2f4f7; opacity: .55;}
.cal .day.today {border: 2px solid #0b5cab;}
.cal .num {font-size: .8rem; font-weight: 700; color: #475467;}
.cal .ev {
  font-size: .72rem; line-height: 1.25; border-radius: 5px; padding: .1rem .3rem; margin-top: 3px; color: #1d2939;
  border: 1px solid rgba(16, 24, 40, .12); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
@media (max-width: 640px) {
  .cal .day {min-height: 64px; padding: .2rem;}
  .cal .ev {font-size: .62rem; padding: 0 .15rem;}
}
</style>
"""


class Modulo:
    def __init__(self, url: str, path: str, title: str, icon: str, desc: str):
        self.url, self.path, self.title, self.icon, self.desc = url, path, title, icon, desc


MODULOS = [
    Modulo("inicio", "views/inicio.py", "Menú principal", "🏠",
           "Resumen de todos los módulos y métricas del día a día."),
    Modulo("partes", "views/generar.py", "Partes", "📝",
           "Gestión de partes de trabajo: rellenar el formulario, firmar, adjuntar fotos y descargar el PDF. "
           "Cada parte guarda todas sus versiones."),
    Modulo("historico", "views/historico.py", "Histórico", "🗂️",
           "Repositorio de las visitas ya realizadas y cerradas. Muestra las del último mes y el historial "
           "completo, y se puede descargar en CSV."),
    Modulo("citas", "views/citas.py", "Citas", "📅",
           "Próximas citas de los clientes actuales ordenadas por día, con aviso por WhatsApp."),
    Modulo("calendario", "views/calendario.py", "Calendario", "🗓️",
           "Vista mensual de las citas con el color de su estado."),
    Modulo("clientes", "views/clientes.py", "Clientes actuales", "👥",
           "Visitas pendientes con el color de su estado. Pulsa en un cliente para ver su ficha, "
           "cambiar el estado o la cita, enviarle un WhatsApp o cerrar la visita."),
    Modulo("comunicaciones", "views/comunicaciones.py", "Comunicaciones", "💬",
           "Seguimiento de las comunicaciones internas y con clientes, para no olvidar las pendientes."),
]


def card_grid(name: str):
    """Contenedor para un grupo de tarjetas del mismo tamaño. Uso: `with ui.card_grid("x"): ...`.

    Cada tarjeta dentro debe ser un st.container(border=True, key="card_…" o "cardlink_…").
    """
    return st.container(key=f"grid_{name}")


# ───────────── gráficos (Plotly) ─────────────
AZUL, AZUL_CLARO, GRIS = "#0b5cab", "#9cc3ee", "#475467"


def plotly_style(fig, alto: int = 340):
    """Aspecto común: fondo transparente, sin rejilla vertical, tipografía de la app y tooltip limpio.

    Los gráficos que van en la misma fila deben usar el mismo `alto`.
    """
    fig.update_layout(
        height=alto, margin=dict(l=8, r=16, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans Pro, sans-serif", size=13, color=GRIS), showlegend=False, bargap=0.3,
        hoverlabel=dict(bgcolor="#fff", bordercolor="#e3e8ef", font=dict(color="#1d2939")),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="#e3e8ef", fixedrange=True)
    fig.update_yaxes(gridcolor="#eef1f6", zeroline=False, fixedrange=True)
    return fig


def plotly_chart(fig) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def flash(msg: str) -> None:
    """Aviso que se muestra tras el siguiente st.rerun() (un st.toast justo antes del rerun se pierde)."""
    st.session_state["_flash"] = msg


def show_flash() -> None:
    if msg := st.session_state.pop("_flash", None):
        st.toast(msg, icon="✅")


def kpi(label: str, value, sub: str = "", warn: bool = False) -> str:
    html = f'<div class="kpi{" warn" if warn else ""}"><div class="k-label">{escape(label)}</div>'
    html += f'<div class="k-value">{escape(str(value))}</div>'
    html += f'<div class="k-sub">{escape(sub)}</div>'  # siempre presente (vacía) para igualar la altura
    return html + "</div>"


def kpis(items: list[str]) -> None:
    st.markdown(f'<div class="kpi-grid">{"".join(items)}</div>', unsafe_allow_html=True)


def chip(text: str, color: str) -> str:
    return f'<span class="chip" style="background:{escape(color)}">{escape(text or "Sin estado")}</span>'


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


def cita_head(hora: str, dia: str, nombre: str, direccion: str, badges: tuple[str, ...] = ()) -> None:
    """Cabecera de una tarjeta de cita: bloque con la hora y el día, nombre, dirección y etiquetas (HTML ya escapado)."""
    sin = " sin" if not hora[:1].isdigit() else ""
    html = (f'<div class="cita"><div class="cita-hora"><div class="h{sin}">{escape(hora)}</div>'
            f'<div class="d">{escape(dia)}</div></div><div class="cita-body">'
            f'<div class="nombre" title="{escape(nombre)}">{escape(nombre)}</div>'
            f'<div class="dir" title="{escape(direccion)}">📍 {escape(direccion or "Sin dirección")}</div>'
            f'<div class="meta">{"".join(badges)}</div></div></div>')
    st.markdown(html, unsafe_allow_html=True)


def section_label(text: str) -> None:
    st.markdown(f'<div class="section-label">{escape(text)}</div>', unsafe_allow_html=True)
