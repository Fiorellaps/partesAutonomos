"""Piezas compartidas por las páginas de gestión: panel de WhatsApp, tabla con colores y carga de datos."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

import datos
import ui

S = st.session_state


def _plantillas(row: dict) -> dict[str, str]:
    nombre = (row.get("cliente") or "").strip().title()
    dt = datos.cita_dt(row)
    cuando = ""
    if dt:
        cuando = f"el {dt:%d/%m/%Y}" + (f" a las {dt:%H:%M}" if dt.time() != datetime.min.time() else "")
    calle = (row.get("direccion") or "").split(",")[0]
    return {
        "Recordatorio de cita": (
            f"Hola {nombre}, le recordamos su cita de mantenimiento Panasonic {cuando or 'programada'}"
            f"{' en ' + calle if calle else ''}. Si no le viene bien, por favor avísenos. Gracias."
        ),
        "Proponer cita": (
            f"Hola {nombre}, le escribimos del servicio técnico de Panasonic por el mantenimiento de su equipo "
            f"(orden {row.get('orden', '')}). ¿Qué día y hora le vendría bien para la visita?"
        ),
        "Mensaje libre": "",
    }


def whatsapp_panel(row: dict, prefix: str) -> None:
    """Elegir plantilla, editar el texto y abrir WhatsApp con el cliente."""
    num = datos.whatsapp_number(row.get("movil", ""))
    if not num:
        st.warning("Este cliente no tiene un móvil válido para WhatsApp.")
        return
    tpls = _plantillas(row)
    default = "Recordatorio de cita" if datos.cita_dt(row) else "Proponer cita"
    tpl = st.segmented_control("Plantilla", list(tpls), default=default, key=f"{prefix}_tpl_{row['id']}") or default
    text = st.text_area("Mensaje", tpls[tpl], key=f"{prefix}_msg_{row['id']}_{tpl}", height=110)
    c1, c2 = st.columns(2)
    c1.link_button(f"💬 Abrir WhatsApp (+{num})", datos.whatsapp_url(row["movil"], text), type="primary",
                   use_container_width=True)
    if c2.button("📝 Anotar en Comunicaciones", key=f"{prefix}_log_{row['id']}", use_container_width=True,
                 help="Crea una comunicación pendiente con este cliente para hacerle seguimiento"):
        datos.add_comunicacion(tipo="Cliente", contacto=row.get("cliente", ""), canal="WhatsApp",
                               asunto=f"{tpl} · {row.get('orden', '')}", estado="Esperando respuesta",
                               notas=text)
        st.toast("Anotado en Comunicaciones", icon="✅")


def leyenda_estados(rows: list[dict]) -> None:
    """Chips con cada estado y su color, como en la columna D del Excel."""
    vistos: dict[str, str] = {}
    for r in rows:
        vistos.setdefault(r.get("estado") or "", r.get("color_estado") or datos.BLANCO)
    st.markdown("".join(ui.chip(e, c) for e, c in vistos.items()), unsafe_allow_html=True)


def tabla_coloreada(rows: list[dict], cols: dict[str, str]) -> pd.io.formats.style.Styler:
    """DataFrame con el fondo de cada fila según su estado y la celda «Estado» con su propio color."""
    df = pd.DataFrame([{label: r.get(k, "") for k, label in cols.items()} for r in rows], columns=list(cols.values()))
    fila = [r.get("color_fila") or datos.BLANCO for r in rows]
    celda = [r.get("color_estado") or datos.BLANCO for r in rows]
    estado_col = cols.get("estado")

    def estilos(d: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame("", index=d.index, columns=d.columns)
        for i in range(len(d)):
            out.iloc[i, :] = f"background-color: {fila[i]}; color: #1d2939"
            if estado_col:
                out.loc[d.index[i], estado_col] = f"background-color: {celda[i]}; color: #1d2939; font-weight: 600"
        return out

    return df.style.apply(estilos, axis=None)


def csv(rows: list[dict], cols: dict[str, str]) -> bytes:
    """CSV con los nombres de columna visibles; con BOM para que Excel respete las tildes."""
    df = pd.DataFrame([{label: r.get(k, "") for k, label in cols.items()} for r in rows], columns=list(cols.values()))
    return df.to_csv(index=False, sep=";").encode("utf-8-sig")


def fecha_es(iso: str) -> str:
    return datetime.fromisoformat(iso).strftime("%d/%m/%Y") if iso else ""
