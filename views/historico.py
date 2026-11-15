"""Histórico: visitas realizadas y cerradas (pestaña «NO TOCAR» del Excel)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import datos
import fichas
import ui

ui.hero("Histórico de visitas", "Visitas ya realizadas y cerradas. Se pueden descargar en CSV.", crumb="Gestión")

rows = datos.load("historico")
if not rows:
    st.info("No hay visitas en el histórico. Importa el Excel desde el Menú principal.")
    st.stop()

rows = sorted(rows, key=lambda r: datos.fecha_ref_historico(r) or date.min, reverse=True)
mes = datos.ultimo_mes(rows)
cols = datos.COLS_HISTORICO

q = st.text_input("Buscar", placeholder="🔎 Cliente, orden, dirección, correo o móvil", key="hist_q",
                  label_visibility="collapsed").strip().lower()


def filtra(rs: list[dict]) -> list[dict]:
    if not q:
        return rs
    return [r for r in rs if q in " ".join(str(r.get(k, "")) for k in ("cliente", "orden", "direccion", "correo",
                                                                          "movil", "observaciones")).lower()]


def tabla(rs: list[dict], nombre: str, key: str) -> None:
    rs = filtra(rs)
    view = [{**r, "fecha_limite": fichas.fecha_es(r["fecha_limite"]), "cerrada": fichas.fecha_es(r["cerrada"])}
            for r in rs]
    df = pd.DataFrame([{label: r.get(k, "") for k, label in cols.items()} for r in view], columns=list(cols.values()))
    st.caption(f"{len(rs)} visitas")
    st.dataframe(df, hide_index=True, use_container_width=True, height=520, key=key, column_config={
        "Cliente": st.column_config.TextColumn(pinned=True),
        "Dirección": st.column_config.TextColumn(width="large"),
        "Servicio": st.column_config.TextColumn(width="medium"),
        "Observaciones": st.column_config.TextColumn(width="large"),
    })
    st.download_button(f"⬇️ Descargar CSV ({len(rs)})", fichas.csv(view, cols), file_name=f"{nombre}.csv",
                       mime="text/csv", key=f"dl_{key}")


t_mes, t_todo = st.tabs([f"📆 Último mes ({len(mes)})", f"🗂️ Historial completo ({len(rows)})"])
with t_mes:
    st.caption("Visitas cuya fecha (la de cierre, la de la cita o, si no tienen ninguna, la fecha límite de la "
               "orden) es de los últimos 30 días o posterior.")
    tabla(mes, f"historico_ultimo_mes_{date.today():%Y%m%d}", "hist_mes")
with t_todo:
    tabla(rows, f"historico_completo_{date.today():%Y%m%d}", "hist_todo")
