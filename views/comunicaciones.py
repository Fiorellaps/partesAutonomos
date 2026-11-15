"""Comunicaciones: seguimiento de comunicaciones internas y con clientes."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import datos
import ui

S = st.session_state

ui.hero("Comunicaciones", "Estado de las comunicaciones internas y con clientes, para recordar las pendientes.",
        crumb="Gestión")

rows = datos.load("comunicaciones")
hoy = date.today()


def abierta(r: dict) -> bool:
    return r.get("estado") != "Hecha"


def vencida(r: dict) -> bool:
    return abierta(r) and bool(r.get("recordar")) and date.fromisoformat(r["recordar"]) <= hoy


ui.kpis([
    ui.kpi("Pendientes", sum(r.get("estado") == "Pendiente" for r in rows)),
    ui.kpi("Esperando respuesta", sum(r.get("estado") == "Esperando respuesta" for r in rows)),
    ui.kpi("Para recordar hoy o antes", sum(vencida(r) for r in rows), "sin cerrar", warn=any(map(vencida, rows))),
    ui.kpi("Hechas", sum(r.get("estado") == "Hecha" for r in rows)),
])

# ───────────── alta ─────────────
st.write("")
with st.expander("➕ Nueva comunicación", expanded=not rows):
    with st.form("nueva_com", clear_on_submit=True, border=False):
        a1, a2, a3 = st.columns(3)
        tipo = a1.selectbox("Tipo", datos.TIPOS_COM)
        canal = a2.selectbox("Canal", datos.CANALES_COM)
        estado = a3.selectbox("Estado", datos.ESTADOS_COM)
        b1, b2 = st.columns([2, 1])
        clientes = sorted({r["cliente"] for r in datos.load("pendientes") if r["cliente"]})
        contacto = b1.selectbox("Con quién", clientes, index=None, accept_new_options=True,
                                placeholder="Elige un cliente o escribe un nombre (p. ej. Oficina, Lucho…)")
        recordar = b2.date_input("Recordar el", value=None, format="DD/MM/YYYY")
        asunto = st.text_input("Asunto")
        notas = st.text_area("Notas", height=80)
        if st.form_submit_button("Añadir", type="primary"):
            if not (asunto.strip() or contacto):
                st.error("Indica al menos con quién o el asunto.")
            else:
                datos.add_comunicacion(tipo=tipo, canal=canal, estado=estado, contacto=contacto or "",
                                       asunto=asunto.strip(), notas=notas.strip(),
                                       recordar=recordar.isoformat() if recordar else "")
                S["com_ver"] = S.get("com_ver", 0) + 1
                ui.flash("Comunicación añadida")
                st.rerun()

# ───────────── tabla editable ─────────────
f1, f2 = st.columns([1, 2], vertical_alignment="center")
solo_abiertas = f1.toggle("Ocultar las hechas", value=True, key="com_abiertas")
tipo_f = f2.segmented_control("Tipo", ["Todas", *datos.TIPOS_COM], default="Todas", key="com_tipo",
                              label_visibility="collapsed") or "Todas"

shown = [r for r in rows if (not solo_abiertas or abierta(r)) and (tipo_f == "Todas" or r.get("tipo") == tipo_f)]
shown.sort(key=lambda r: (not vencida(r), r.get("recordar") or "9999", r.get("fecha") or ""))
ui.section_label(f"Comunicaciones ({len(shown)})")

COLS = ["id", "aviso", "fecha", "tipo", "contacto", "canal", "asunto", "estado", "recordar", "notas"]
df = pd.DataFrame([{**r, "aviso": "⚠️ Recordar" if vencida(r) else ""} for r in shown], columns=COLS)
for c in ("fecha", "recordar"):
    df[c] = pd.to_datetime(df[c], errors="coerce").dt.date

edited = st.data_editor(
    df, hide_index=True, use_container_width=True, num_rows="dynamic", 
    key=f"com_editor_{S.get('com_ver', 0)}_{solo_abiertas}_{tipo_f}",
    column_order=COLS[1:], disabled=("aviso",),
    column_config={
        "aviso": st.column_config.TextColumn("", width="small"),
        "fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY", default=hoy),
        "tipo": st.column_config.SelectboxColumn("Tipo", options=datos.TIPOS_COM, default="Cliente", required=True),
        "contacto": st.column_config.TextColumn("Con quién"),
        "canal": st.column_config.SelectboxColumn("Canal", options=datos.CANALES_COM, default="WhatsApp"),
        "asunto": st.column_config.TextColumn("Asunto", width="medium"),
        "estado": st.column_config.SelectboxColumn("Estado", options=datos.ESTADOS_COM, default="Pendiente",
                                                   required=True),
        "recordar": st.column_config.DateColumn("Recordar el", format="DD/MM/YYYY"),
        "notas": st.column_config.TextColumn("Notas", width="large"),
    },
)


def _row(rec: dict) -> dict:
    out = {}
    for c in COLS:
        if c == "aviso":
            continue
        v = rec.get(c)
        if v is None or (not isinstance(v, str) and pd.isna(v)):
            v = ""
        out[c] = v.isoformat() if isinstance(v, date) else str(v)
    out["id"] = out["id"] or datos.new_id()
    return out


if st.button("💾 Guardar cambios de la tabla", type="primary"):
    nuevos = [_row(r) for r in edited.to_dict("records")]
    visibles = {r["id"] for r in shown}
    datos.save("comunicaciones", [r for r in rows if r["id"] not in visibles] + nuevos)
    S["com_ver"] = S.get("com_ver", 0) + 1
    ui.flash("Comunicaciones guardadas")
    st.rerun()
st.caption("Edita las celdas directamente, añade filas al final o selecciona filas y pulsa la papelera para "
           "borrarlas. Después pulsa «Guardar cambios de la tabla».")
