"""Citas: lista de citas con edición inline de fecha, estado, notas, técnico y WhatsApp."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import streamlit as st

import datos
import fichas
import ui

S = st.session_state
DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")

ui.show_flash()
ui.hero("Citas", "Pulsa en una cita para editarla.", crumb="Gestión")

rows = datos.load("pendientes")
con_cita = sorted((r for r in rows if r.get("cita_dt")), key=lambda r: r["cita_dt"])
sin_cita = sorted((r for r in rows if not r.get("cita_dt")), key=lambda r: r.get("cliente", ""))
hoy = date.today()

rango = st.segmented_control("Mostrar", ["Hoy", "Próximos 7 días", "Próximas", "Pasadas", "Todas", "Sin cita"],
                             default="Próximos 7 días", key="citas_rango") or "Próximos 7 días"


def en_rango(d: date) -> bool:
    return {"Hoy": d == hoy, "Próximos 7 días": hoy <= d <= hoy + timedelta(days=7),
            "Próximas": d >= hoy, "Pasadas": d < hoy, "Todas": True}[rango]


if rango == "Sin cita":
    citas_vista = []
else:
    citas_vista = [r for r in con_cita if en_rango(datos.cita_dt(r).date())]
    if rango == "Pasadas":
        citas_vista.reverse()

ui.kpis([
    ui.kpi("Hoy", sum(datos.cita_dt(r).date() == hoy for r in con_cita)),
    ui.kpi("Próximos 7 días", sum(hoy <= datos.cita_dt(r).date() <= hoy + timedelta(days=7) for r in con_cita)),
    ui.kpi("Sin cita", len(sin_cita), "pendientes de asignar"),
])


def _form_cita(r: dict, prefix: str) -> None:
    """Formulario de edición de una cita (estado, fecha, técnico, notas, WhatsApp)."""
    with st.form(f"form_{prefix}_{r['id']}", border=False):
        opciones_estado = sorted({x["estado"] for x in rows if x["estado"]})
        idx_estado = (["", *opciones_estado].index(r["estado"])
                      if r["estado"] in opciones_estado else 0)
        a1, a2 = st.columns(2)
        estado_sel = a1.selectbox("Estado actual", ["", *opciones_estado], index=idx_estado,
                                  format_func=lambda v: v or "Sin estado")
        estado_nuevo = a2.text_input("…o escribe uno nuevo", placeholder="p. ej. CONFIRMADO")

        b1, b2, b3 = st.columns([2, 2, 1], vertical_alignment="bottom")
        dt = datos.cita_dt(r)
        f_cita = b1.date_input("Fecha de la cita", value=dt.date() if dt else None, format="DD/MM/YYYY")
        h_cita = b2.time_input("Hora", value=dt.time() if dt and dt.time() != time(0) else None, step=900)
        borrar = b3.checkbox("Quitar cita")

        c1, c2 = st.columns(2)
        idx_tec = datos.TECNICOS.index(r.get("tecnico", "") or "") if r.get("tecnico") in datos.TECNICOS else 0
        tecnico = c1.selectbox("Asignar a", datos.TECNICOS, index=idx_tec,
                               format_func=lambda v: v or "Sin asignar")
        notas = c2.text_input("Notas rápidas", r.get("notas", ""), placeholder="p. ej. llamar antes")

        if st.form_submit_button("💾 Guardar", type="primary", use_container_width=True):
            estado = estado_nuevo.strip().upper() or estado_sel
            if estado != r["estado"]:
                datos.set_estado(r["id"], estado)
            cambios: dict = {"notas": notas.strip(), "tecnico": tecnico}
            if borrar:
                cambios.update(cita="", cita_dt="")
            elif f_cita:
                nuevo = datetime.combine(f_cita, h_cita or time(0))
                if nuevo != dt:
                    cambios.update(cita=datos.format_cita(nuevo), cita_dt=nuevo.isoformat(timespec="minutes"))
            datos.update("pendientes", r["id"], **cambios)
            ui.flash("Guardado")
            st.rerun()


def _cita_card(r: dict, dt, prefix: str) -> None:
    hora = f"{dt:%H:%M}" if dt.time() != time(0) else "Sin hora"
    tec = r.get("tecnico")
    _tec_b = (ui.badge(f"👤 {tec}", "ok"),) if tec else ()
    badges = (ui.chip(r["estado"], r["color_estado"]), ui.badge(f"🧾 {r['orden']}"),
              ui.badge(f"📱 {r['movil']}" if r["movil"] else "Sin móvil", "muted")) + _tec_b
    with st.container(border=True, key=f"card_cita_{r['id']}"):
        c_info, c_edit, c_wa = st.columns([4, 2, 1], vertical_alignment="center")
        with c_info:
            ui.cita_head(hora, f"{DIAS[dt.weekday()][:3]} {dt:%d/%m}", r["cliente"] or "Sin nombre",
                         r["direccion"], badges)
        with c_edit.popover("✏️ Editar", use_container_width=True):
            _form_cita(r, prefix)
        with c_wa.popover("💬", use_container_width=True, help="WhatsApp"):
            fichas.whatsapp_panel(r, f"cita_{prefix}")


# ── lista con cita ────────────────────────────────────────────────────────────
if not citas_vista and rango != "Sin cita":
    if rango in ("Hoy", "Próximos 7 días", "Próximas"):
        st.info("No hay citas en este periodo.")
    else:
        st.info("No hay citas pasadas.")

dia_actual = None
for r in citas_vista:
    dt = datos.cita_dt(r)
    if dt.date() != dia_actual:
        dia_actual = dt.date()
        etiqueta = "Hoy · " if dia_actual == hoy else ("Mañana · " if dia_actual == hoy + timedelta(1) else "")
        ui.section_label(f"{etiqueta}{DIAS[dia_actual.weekday()]} {dia_actual:%d/%m/%Y}")
    _cita_card(r, dt, "c")

# ── sin cita ─────────────────────────────────────────────────────────────────
if rango == "Sin cita":
    if not sin_cita:
        st.success("Todos los clientes tienen cita asignada.")
    else:
        ui.section_label(f"Clientes sin cita ({len(sin_cita)})")
        for r in sin_cita:
            tec = r.get("tecnico")
            _tec_b = (ui.badge(f"👤 {tec}", "ok"),) if tec else ()
            badges = (ui.chip(r["estado"], r["color_estado"]), ui.badge(f"🧾 {r['orden']}"),
                      ui.badge(f"📱 {r['movil']}" if r["movil"] else "Sin móvil", "muted")) + _tec_b
            with st.container(border=True, key=f"card_sincita_{r['id']}"):
                c_info, c_edit, c_wa = st.columns([4, 2, 1], vertical_alignment="center")
                with c_info:
                    ui.cita_head("Sin cita", "", r["cliente"] or "Sin nombre", r["direccion"], badges)
                with c_edit.popover("✏️ Asignar cita", use_container_width=True):
                    _form_cita(r, "sc")
                with c_wa.popover("💬", use_container_width=True, help="WhatsApp"):
                    fichas.whatsapp_panel(r, f"sc_{r['id']}")
elif sin_cita:
    with st.expander(f"Clientes sin cita ({len(sin_cita)}) · pulsa para asignar"):
        for r in sin_cita:
            tec = r.get("tecnico")
            _tec_b = (ui.badge(f"👤 {tec}", "ok"),) if tec else ()
            badges = (ui.chip(r["estado"], r["color_estado"]), ui.badge(f"🧾 {r['orden']}")) + _tec_b
            with st.container(border=True, key=f"card_syncita2_{r['id']}"):
                c_i, c_e = st.columns([4, 2], vertical_alignment="center")
                with c_i:
                    ui.cita_head("Sin cita", "", r["cliente"] or "Sin nombre", r["direccion"], badges)
                with c_e.popover("✏️ Asignar cita", use_container_width=True):
                    _form_cita(r, "sc2")
