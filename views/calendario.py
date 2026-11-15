"""Calendario: vista mensual de las citas con el color de su estado."""
from __future__ import annotations

import calendar
from datetime import date, time
from html import escape

import streamlit as st

import datos
import ui

S = st.session_state
MESES = ("Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre")

ui.hero("Calendario", "Citas de los clientes actuales por mes, con el color de su estado.", crumb="Gestión")

hoy = date.today()
S.setdefault("cal_mes", (hoy.year, hoy.month))


def mover(delta: int) -> None:
    y, m = S["cal_mes"]
    m += delta
    S["cal_mes"] = (y + (m - 1) // 12, (m - 1) % 12 + 1)


def ir_hoy() -> None:
    S["cal_mes"] = (hoy.year, hoy.month)


year, month = S["cal_mes"]
b1, b2, b3, b4 = st.columns([1, 3, 1, 1], vertical_alignment="center")
b1.button("◀", on_click=mover, args=(-1,), use_container_width=True, help="Mes anterior")
b2.markdown(f"<h3 style='text-align:center;margin:0'>{MESES[month - 1]} {year}</h3>", unsafe_allow_html=True)
b3.button("▶", on_click=mover, args=(1,), use_container_width=True, help="Mes siguiente")
b4.button("Hoy", on_click=ir_hoy, use_container_width=True)

por_dia: dict[date, list[dict]] = {}
for r in sorted(datos.load("pendientes"), key=lambda r: r.get("cita_dt") or ""):
    if dt := datos.cita_dt(r):
        por_dia.setdefault(dt.date(), []).append(r)

html = '<div class="cal">' + "".join(f'<div class="dow">{d}</div>' for d in ("L", "M", "X", "J", "V", "S", "D"))
for semana in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
    for d in semana:
        cls = "day" + (" out" if d.month != month else "") + (" today" if d == hoy else "")
        html += f'<div class="{cls}"><div class="num">{d.day}</div>'
        for r in por_dia.get(d, []):
            dt = datos.cita_dt(r)
            hora = f"{dt:%H:%M} " if dt.time() != time(0) else ""
            title = escape(f"{hora}{r['cliente']} · {r['estado'] or 'Sin estado'} · {r['direccion']}")
            html += (f'<div class="ev" style="background:{escape(r["color_estado"] or datos.BLANCO)}" '
                     f'title="{title}">{escape(hora + r["cliente"])}</div>')
        html += "</div>"
st.markdown(html + "</div>", unsafe_allow_html=True)

def hora_txt(r: dict) -> str:
    dt = datos.cita_dt(r)
    return f" {dt:%H:%M}" if dt.time() != time(0) else ""


del_mes = [(d, r) for d, rs in sorted(por_dia.items()) if (d.year, d.month) == (year, month) for r in rs]
ui.section_label(f"Citas del mes ({len(del_mes)})")
if not del_mes:
    st.caption("No hay citas este mes.")
else:
    st.markdown("".join(
        f"<div style='margin-bottom:.25rem'>{ui.chip(r['estado'], r['color_estado'])} "
        f"<b>{d:%d/%m}{hora_txt(r)}</b> · {escape(r['cliente'])} · "
        f"<span style='color:#667085'>{escape(r['direccion'])}</span></div>"
        for d, r in del_mes), unsafe_allow_html=True)
