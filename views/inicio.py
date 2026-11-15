"""Menú principal: accesos a todos los módulos con su explicación y panel de métricas."""
from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

import plotly.graph_objects as go
import streamlit as st

import datos
import storage
import ui
from partes import all_models

ui.hero("Menú principal", "Métricas del día a día y acceso a todos los módulos.", crumb="Inicio")

pend = datos.load("pendientes")
hist = datos.load("historico")
coms = datos.load("comunicaciones")
hoy = date.today()
citas = [d for r in pend if (d := datos.cita_dt(r))]
n_partes = sum(len(storage.list_docs(m)) for m in all_models())
com_abiertas = [r for r in coms if r.get("estado") != "Hecha"]
com_vencidas = [r for r in com_abiertas if r.get("recordar") and date.fromisoformat(r["recordar"]) <= hoy]

resumen = {
    "partes": f"{n_partes} partes guardados",
    "historico": f"{len(hist)} visitas · {len(datos.ultimo_mes(hist))} en el último mes",
    "citas": f"{sum(d.date() == hoy for d in citas)} hoy · "
             f"{sum(hoy <= d.date() <= hoy + timedelta(days=7) for d in citas)} en 7 días",
    "calendario": f"{sum((d.year, d.month) == (hoy.year, hoy.month) for d in citas)} citas este mes",
    "clientes": f"{len(pend)} visitas pendientes",
    "comunicaciones": f"{len(com_abiertas)} abiertas · {len(com_vencidas)} para recordar",
}

# ───────────── métricas ─────────────
ui.section_label("Métricas")
ui.kpis([
    ui.kpi("Visitas pendientes", len(pend), f"{sum(not r.get('cita_dt') for r in pend)} sin cita"),
    ui.kpi("Citas hoy", sum(d.date() == hoy for d in citas)),
    ui.kpi("Citas próximos 7 días", sum(hoy <= d.date() <= hoy + timedelta(days=7) for d in citas)),
    ui.kpi("Cerradas último mes", len(datos.ultimo_mes(hist)), f"{len(hist)} en total"),
    ui.kpi("Comunicaciones por recordar", len(com_vencidas), f"{len(com_abiertas)} abiertas",
           warn=bool(com_vencidas)),
    ui.kpi("Partes guardados", n_partes),
])
st.write("")

MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
AZUL, AZUL_CLARO = ui.AZUL, ui.AZUL_CLARO

# Barras verticales con muchos estados de nombre largo: el gráfico ocupa todo el ancho.
with st.container(border=True, key="card_g_estado"):
    st.markdown("**Clientes actuales por estado**")
    if pend:
        cnt = Counter(r["estado"] or "Sin estado" for r in pend)
        color: dict[str, str] = {}
        for r in pend:
            color.setdefault(r["estado"] or "Sin estado", r["color_estado"] or datos.BLANCO)
        orden = sorted(cnt, key=cnt.get, reverse=True)  # el más frecuente a la izquierda
        corto = [e if len(e) <= 22 else e[:21] + "…" for e in orden]
        fig = go.Figure(go.Bar(
            x=corto, y=[cnt[e] for e in orden], text=[cnt[e] for e in orden], textposition="outside",
            cliponaxis=False, customdata=orden,
            marker=dict(color=[color[e] for e in orden], line=dict(color="rgba(16,24,40,.25)", width=1),
                        cornerradius=4),
            hovertemplate="%{customdata}<br><b>%{y}</b> visitas<extra></extra>",
        ))
        ui.plotly_style(fig, 420).update_layout(bargap=0.2)
        fig.update_xaxes(tickangle=-40, tickfont=dict(size=11), type="category")
        fig.update_yaxes(rangemode="tozero", range=[0, max(cnt.values()) * 1.15])
        ui.plotly_chart(fig)
        st.caption("Cada barra lleva el color del estado en el Excel. Pasa el ratón para ver el nombre completo.")
    else:
        st.caption("Sin datos.")

g1, g2 = st.columns(2)
with g1.container(border=True, key="card_g_citas"):
    st.markdown("**Citas de los próximos 14 días**")
    dias = [hoy + timedelta(days=i) for i in range(14)]
    cnt = Counter(d.date() for d in citas)
    valores = [cnt.get(d, 0) for d in dias]
    fig = go.Figure(go.Bar(
        x=[f"{'LMXJVSD'[d.weekday()]}<br>{d:%d/%m}" for d in dias], y=valores,
        text=[v or "" for v in valores], textposition="outside", cliponaxis=False,
        marker=dict(color=[AZUL_CLARO if d.weekday() >= 5 else AZUL for d in dias], cornerradius=6),
        hovertemplate="%{x}<br><b>%{y}</b> citas<extra></extra>",
    ))
    ui.plotly_style(fig)
    fig.update_yaxes(dtick=1, rangemode="tozero", range=[0, max(valores + [1]) * 1.25])
    ui.plotly_chart(fig)
    st.caption("Sábados y domingos en azul claro.")

with g2.container(border=True, key="card_g_hist"):
    st.markdown("**Visitas cerradas por mes**")
    meses = Counter((f.year, f.month) for r in hist if (f := datos.fecha_ref_historico(r)))
    if meses:
        orden = sorted(meses)
        fig = go.Figure(go.Bar(
            x=[f"{MESES[m - 1]} {y % 100:02d}" for y, m in orden], y=[meses[k] for k in orden],
            text=[meses[k] for k in orden], textposition="outside", cliponaxis=False,
            marker=dict(color=AZUL, cornerradius=6), hovertemplate="%{x}<br><b>%{y}</b> visitas<extra></extra>",
        ))
        ui.plotly_style(fig)
        fig.update_yaxes(rangemode="tozero", range=[0, max(meses.values()) * 1.2])
        fig.update_xaxes(type="category")
        ui.plotly_chart(fig)
        st.caption("Por fecha de cierre, de cita o límite.")  # una línea, como la del gráfico de al lado
    else:
        st.caption("Sin datos.")

# ───────────── módulos ─────────────
ui.section_label("Módulos")
mods = [m for m in ui.MODULOS if m.url != "inicio"]
with ui.card_grid("modulos"):
    for m in mods:
        with st.container(border=True, key=f"cardlink_mod_{m.url}"):
            ui.card_head(m.icon, m.title, m.desc, (ui.badge(resumen[m.url], "muted"),))
            st.page_link(m.path, label=f"Abrir {m.title}", icon="➡️", use_container_width=True)

# ───────────── importación ─────────────
st.write("")
with st.expander("📥 Actualizar datos desde el Excel"):
    st.write("Sube «CITAS PANASONIC.xlsx». Se leen las pestañas **NO TOCAR** (Histórico) y "
             "**PANASONIC PENDIENTES** (Clientes actuales).")
    st.warning("Sustituye todo el Histórico y los Clientes actuales, incluidos los cambios hechos en la app "
               "(estados, citas, notas y visitas cerradas). Las Comunicaciones y los Partes no se tocan.")
    up = st.file_uploader("Excel", type=["xlsx"], label_visibility="collapsed", key="xlsx_up")
    if up and st.button("Importar y sustituir", type="primary"):
        try:
            n_h, n_p = datos.import_excel(up.getvalue())
        except Exception as e:  # noqa: BLE001 - se muestra al usuario
            st.error(f"No se pudo leer el Excel: {e}")
        else:
            ui.flash(f"Importadas {n_h} visitas al histórico y {n_p} clientes actuales")
            st.rerun()
