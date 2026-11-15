"""Clientes actuales: visitas pendientes (pestaña «PANASONIC PENDIENTES» del Excel)."""
from __future__ import annotations

from datetime import datetime, time

import streamlit as st

import datos
import fichas
import ui

S = st.session_state
SIN_ESTADO = "(Sin estado)"

ui.hero("Clientes actuales", "Visitas pendientes. Pulsa en una fila para abrir la ficha del cliente.",
        crumb="Gestión")

rows = datos.load("pendientes")
if not rows:
    st.info("No hay clientes cargados. Importa el Excel desde el Menú principal.")
    st.stop()

# ───────────── filtros ─────────────
c_q, c_e = st.columns([2, 3])
q = c_q.text_input("Buscar", placeholder="🔎 Cliente, orden, dirección, correo o móvil", key="cli_q",
                   label_visibility="collapsed").strip().lower()
estados = sorted({r["estado"] or SIN_ESTADO for r in rows})
sel_estados = c_e.multiselect("Estado", estados, key="cli_estados", placeholder="Filtrar por estado",
                              label_visibility="collapsed")


def visible(r: dict) -> bool:
    if sel_estados and (r["estado"] or SIN_ESTADO) not in sel_estados:
        return False
    if q:
        hay = " ".join(str(r.get(k, "")) for k in ("cliente", "orden", "direccion", "correo", "movil")).lower()
        return q in hay
    return True


shown = [r for r in rows if visible(r)]
fichas.leyenda_estados(rows)
ui.section_label(f"Visitas pendientes ({len(shown)} de {len(rows)})" if len(shown) != len(rows)
                 else f"Visitas pendientes ({len(rows)})")

cols = datos.COLS_PENDIENTES
view = [{**r, "fecha_limite": fichas.fecha_es(r["fecha_limite"])} for r in shown]
event = st.dataframe(
    fichas.tabla_coloreada(view, cols), hide_index=True, use_container_width=True, height=520,
    on_select="rerun", selection_mode="single-row", key=f"cli_tabla_{len(shown)}_{hash((q, tuple(sel_estados)))}",
    column_config={
        "Dirección": st.column_config.TextColumn(width="large"),
        "Servicio": st.column_config.TextColumn(width="medium"),
        "Descripción SAT": st.column_config.TextColumn(width="medium"),
    },
)
st.download_button("⬇️ Descargar CSV", fichas.csv(view, cols), file_name="clientes_actuales.csv", mime="text/csv")

sel = event.selection.rows if event and event.selection else []
if not sel:
    st.caption("👆 Selecciona un cliente en la tabla para ver su ficha y enviarle un WhatsApp.")
    st.stop()

row = shown[sel[0]]
rid = row["id"]

# ───────────── ficha del cliente ─────────────
ui.section_label("Ficha del cliente")
with st.container(border=True, key=f"card_cliente_{rid}"):
    tec = row.get("tecnico")
    ui.card_head("👤", row["cliente"] or "Sin nombre", row["direccion"],
                 (ui.chip(row["estado"], row["color_estado"]), ui.badge(row["orden"]),
                  ui.badge(f"Cita: {row['cita']}" if row["cita"] else "Sin cita", "muted"))
                 + ((ui.badge(f"👤 {tec}", "ok"),) if tec else ()))
    i1, i2, i3 = st.columns(3)
    i1.markdown(f"**📱 Móvil**  \n{row['movil'] or '—'}")
    i2.markdown(f"**✉️ Correo**  \n{row['correo'] or '—'}")
    i3.markdown(f"**⏳ Fecha límite**  \n{fichas.fecha_es(row['fecha_limite']) or '—'}")
    if row["servicio"] or row["descripcion"]:
        st.caption(" · ".join(x for x in (row["tipo"], row["servicio"], row["descripcion"]) if x))

    t_wa, t_edit, t_close = st.tabs(["💬 WhatsApp", "✏️ Editar", "✅ Cerrar visita"])
    with t_wa:
        fichas.whatsapp_panel(row, "cli")

    with t_edit:
        with st.form(f"edit_{rid}", border=False):
            opciones = sorted({r["estado"] for r in rows if r["estado"]})
            e1, e2 = st.columns(2)
            estado_sel = e1.selectbox("Estado", ["", *opciones], index=(["", *opciones].index(row["estado"])),
                                      format_func=lambda v: v or SIN_ESTADO)
            estado_nuevo = e2.text_input("…o escribe un estado nuevo", placeholder="p. ej. PENDIENTE DE PIEZA")
            dt = datos.cita_dt(row)
            d1, d2, d3 = st.columns([2, 2, 1], vertical_alignment="bottom")
            f_cita = d1.date_input("Fecha de la cita", value=dt.date() if dt else None, format="DD/MM/YYYY")
            h_cita = d2.time_input("Hora", value=dt.time() if dt and dt.time() != time(0) else None, step=900)
            borrar = d3.checkbox("Sin cita")
            t1, t2 = st.columns(2)
            idx_tec = datos.TECNICOS.index(row.get("tecnico", "") or "") if row.get("tecnico") in datos.TECNICOS else 0
            tecnico = t1.selectbox("Asignar a", datos.TECNICOS, index=idx_tec,
                                   format_func=lambda v: v or "Sin asignar")
            notas = t2.text_input("Notas", row.get("notas", ""))
            if st.form_submit_button("💾 Guardar cambios", type="primary"):
                estado = estado_nuevo.strip().upper() or estado_sel
                if estado != row["estado"]:
                    datos.set_estado(rid, estado)
                cambios = {"notas": notas.strip(), "tecnico": tecnico}
                if borrar:
                    cambios.update(cita="", cita_dt="")
                elif f_cita:
                    nuevo = datetime.combine(f_cita, h_cita or time(0))
                    if nuevo != dt:
                        cambios.update(cita=datos.format_cita(nuevo), cita_dt=nuevo.isoformat(timespec="minutes"))
                datos.update("pendientes", rid, **cambios)
                ui.flash("Cambios guardados")
                st.rerun()
        st.caption("Al cambiar el estado se aplica el color correspondiente del Excel "
                   "(amarillo confirmado, rojo avería o cancelación, naranja/salmón problemas de correo…).")

    with t_close:
        st.write("La visita pasa al **Histórico** con la fecha de hoy como fecha de cierre y "
                 "desaparece de Clientes actuales.")
        with st.popover("✅ Cerrar visita y pasar al histórico", use_container_width=True):
            st.warning(f"¿Cerrar la visita de «{row['cliente']}» ({row['orden']})?")
            if st.button("Sí, cerrar visita", type="primary", key=f"close_{rid}"):
                datos.cerrar_visita(rid)
                ui.flash("Visita cerrada y movida al histórico")
                st.rerun()
