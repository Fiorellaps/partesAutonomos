"""Página «Generación de Partes»: modelos → partes guardados → editor con versiones, firma y PDF."""
from __future__ import annotations

import re
from datetime import date, datetime
from functools import partial

import streamlit as st

import storage
import ui
from partes import all_models, custom
from partes.base import Item, Model
from signature import signature_pad

S = st.session_state
P = "d::"  # prefijo de las claves de session_state que forman los datos del parte


def K(name: str) -> str:
    return P + name


# ───────────────────────── datos ↔ session_state ─────────────────────────
def defaults(model: Model) -> dict:
    d: dict = {"RESUMEN": "", "m_fecha": date.today().strftime("%d/%m/%Y")}
    for key, _ in model.header:
        d.setdefault(f"m_{key}", "")
    for sec in model.sections:
        for it in sec.items:
            if it.check:
                d[it.check] = False
            if it.yn:
                d[f"yn_{it.texts[0][0]}"] = ""
            for field, _ in it.texts:
                d[field] = ""
    for role, _, _ in model.signatures:
        d.update({f"nom_{role}": "", f"dni_{role}": "", f"sig_{role}": ""})
    return d


def load_data(model: Model, data: dict) -> None:
    for k, v in {**defaults(model), **data}.items():
        S[K(k)] = v
    S["padver"] = S.get("padver", 0) + 1  # reinicia los lienzos de firma
    S.pop("pdf", None)


def collect(model: Model) -> dict:
    data = {k: S.get(K(k), v) for k, v in defaults(model).items()}
    for role, _, _ in model.signatures:  # el lienzo, si se ha firmado, sustituye a la firma guardada
        pad = S.get(f"pad::{role}::{S.get('padver', 0)}")
        if pad and len(pad) > 200:  # descarta lienzos vacíos («data:,»)
            data[f"sig_{role}"] = pad
    return data


# ───────────────────────── navegación ─────────────────────────
def go(view: str, model_id: str | None = None) -> None:
    S["view"] = view
    if model_id:
        S["model_id"] = model_id


def open_doc(model: Model, doc_id: str | None) -> None:
    S["view"] = "edit"
    S["doc_id"] = doc_id
    S.pop("ver_sel", None)
    S.pop("pdf", None)
    doc = storage.load_doc(model.id, doc_id) if doc_id else None
    if doc:
        S["doc_title"] = doc["title"]
        S["ver_sel"] = doc["versions"][-1]["n"]
        load_data(model, doc["versions"][-1]["data"])
    else:
        S["doc_id"] = None
        S["doc_title"] = ""
        load_data(model, {})


def on_version_change(model: Model) -> None:
    doc = storage.load_doc(model.id, S["doc_id"])
    ver = next(v for v in doc["versions"] if v["n"] == S["ver_sel"])
    load_data(model, ver["data"])


def do_save(model: Model) -> None:
    data = collect(model)
    title = (S.get("doc_title") or "").strip() or data.get("m_cliente") or "Parte sin título"
    doc = storage.save_version(model.id, S.get("doc_id"), title, data, (S.get("ver_note") or "").strip())
    S["doc_id"], S["doc_title"] = doc["id"], doc["title"]
    S["ver_sel"] = doc["versions"][-1]["n"]
    S["ver_note"] = ""
    for role, _, _ in model.signatures:
        S[K(f"sig_{role}")] = data[f"sig_{role}"]
    S["padver"] = S.get("padver", 0) + 1
    S["flash"] = f"Guardada la versión {S['ver_sel']}"


def delete_template(tid: str) -> None:
    custom.delete_template(tid)
    S["view"] = "models"


def do_delete(model: Model, doc_id: str) -> None:
    storage.delete_doc(model.id, doc_id)
    S["view"] = "model"


# ───────────────────────── vistas ─────────────────────────
def plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def view_models() -> None:
    ui.hero("Generación de Partes", "Elige el modelo de parte con el que quieres trabajar.", crumb="Inicio")
    ui.section_label("Modelos disponibles")
    models = list(all_models().values())
    cols = st.columns(2)
    for i, m in enumerate(models):
        n = len(storage.list_docs(m.id))
        badges = [ui.badge(m.brand)] if m.brand else []
        if m.custom:
            badges.append(ui.badge("Plantilla propia"))
        badges.append(ui.badge(plural(n, "parte guardado", "partes guardados"), "ok" if n else "muted"))
        with cols[i % 2].container(border=True, key=f"cardlink_model_{m.id}"):
            ui.card_head(m.icon, m.name, m.description, tuple(badges))
            st.button("Abrir modelo →", key=f"open_{m.id}", on_click=go, args=("model", m.id),
                      type="primary", use_container_width=True)
    # Tarjeta «añadir» en la siguiente celda libre de la cuadrícula
    with cols[len(models) % 2].container(border=True, key="card_add_template"):
        ui.card_head("➕", "Añadir plantilla", "Sube un PDF rellenable y se genera su formulario.")
        st.button("Añadir plantilla (PDF)", on_click=go, args=("new_template",), use_container_width=True)


def finish_template(name: str, pdf: bytes, rows) -> None:
    fields = [
        {"name": r["name"], "kind": r["kind"], "label": (r["label"] or r["name"]).strip(),
         "page": int(r["page"]), "multiline": bool(r["multiline"])}
        for r in rows.to_dict("records") if r["use"]
    ]
    tid = custom.save_template(name.strip(), pdf, fields)
    for k in ("tpl_file", "tpl_name"):
        S.pop(k, None)
    go("model", tid)


def view_new_template() -> None:
    import pandas as pd  # dependencia de streamlit

    st.button("← Modelos", on_click=go, args=("models",), type="tertiary")
    ui.hero("Nueva plantilla", "Sube un PDF con campos de formulario rellenables. Se detectan los campos "
            "y se genera el formulario.", crumb="Plantillas")
    up = st.file_uploader("PDF de la plantilla", type="pdf", key="tpl_file")
    if up is None:
        return
    pdf = up.getvalue()
    try:
        fields, skipped = custom.analyze(pdf)
    except ValueError as e:
        st.error(str(e))
        return
    if not fields:
        st.error("Este PDF no tiene campos de formulario rellenables, no se puede generar el formulario.")
        return
    if skipped:
        st.warning(f"{skipped} campo(s) de tipo botón u opción única no son compatibles y se han ignorado.")

    st.text_input("Nombre de la plantilla", key="tpl_name", value=up.name.removesuffix(".pdf").removesuffix(".PDF"))
    st.markdown(f"**{len(fields)} campos detectados.** Revisa las etiquetas y el tipo; desmarca los que no quieras.")
    df = pd.DataFrame(fields)
    df.insert(0, "use", True)
    edited = st.data_editor(
        df, hide_index=True, use_container_width=True, key=f"tpl_edit_{up.file_id}",
        column_order=("use", "label", "kind", "page"),
        column_config={
            "use": st.column_config.CheckboxColumn("Usar"),
            "label": st.column_config.TextColumn("Etiqueta"),
            "kind": st.column_config.SelectboxColumn("Tipo", options=list(custom.KINDS), required=True),
            "page": st.column_config.NumberColumn("Pág."),
        },
        disabled=("page",),
    )
    name = S.get("tpl_name", "").strip()
    st.button(
        "Crear plantilla", type="primary", use_container_width=True, disabled=not name or not edited["use"].any(),
        on_click=finish_template, args=(name, pdf, edited),
    )


def view_model(model: Model) -> None:
    st.button("← Modelos", on_click=go, args=("models",), type="tertiary")
    ui.hero(model.name, model.description, crumb="Modelo")
    st.button("➕ Nuevo parte", type="primary", use_container_width=True, on_click=open_doc, args=(model, None))

    docs = storage.list_docs(model.id)
    ui.section_label(f"Partes guardados ({len(docs)})")
    if not docs:
        with st.container(border=True, key="card_empty"):
            st.caption("Todavía no hay partes guardados. Crea uno con «Nuevo parte».")
    for d in docs:
        last = d["versions"][-1]
        when = datetime.fromisoformat(d["updated"]).strftime("%d/%m/%Y %H:%M")
        badges = [ui.badge(f"v{last['n']}"), ui.badge(when, "muted")]
        if last.get("note"):
            badges.append(ui.badge(last["note"], "muted"))
        with st.container(border=True, key=f"cardlink_doc_{d['id']}"):
            ui.card_head("📄", d["title"], plural(len(d["versions"]), "versión", "versiones"), tuple(badges))
            st.button("Abrir", key=f"doc_{d['id']}", on_click=open_doc, args=(model, d["id"]), use_container_width=True)

    if model.custom:
        st.write("")
        with st.popover("🗑️ Eliminar plantilla", use_container_width=True):
            st.warning("Se borrará la plantilla y todos los partes creados con ella.")
            st.button("Sí, eliminar plantilla", on_click=delete_template, args=(model.id,))


def item_widget(it: Item) -> None:
    with st.container(border=True):
        if it.yn:
            n = it.texts[0][0]
            st.radio(it.label, ["", "SI", "NO"], key=K(f"yn_{n}"), horizontal=True, format_func=lambda v: v or "—")
        elif it.check:
            st.checkbox(it.label, key=K(it.check))
        else:
            st.markdown(it.label)
        if len(it.texts) == 2:
            for col, (field, hint) in zip(st.columns(2), it.texts):
                col.text_input(hint, key=K(field), placeholder=hint, label_visibility="collapsed")
        else:
            for field, hint in it.texts:
                if it.multiline:
                    st.text_area(hint, key=K(field), placeholder=hint, label_visibility="collapsed", height=80)
                else:
                    st.text_input(hint, key=K(field), placeholder=hint, label_visibility="collapsed")


def signature_widget(role: str, title: str) -> None:
    st.markdown(f"**{title}**")
    st.text_input("Nombre y apellidos", key=K(f"nom_{role}"))
    st.text_input("DNI", key=K(f"dni_{role}"))
    saved = S.get(K(f"sig_{role}"))
    if saved:
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.image(saved, caption="Firma guardada", width=200)
        c2.button("Quitar", key=f"rm_{role}", on_click=lambda: S.__setitem__(K(f"sig_{role}"), ""))
        st.caption("Si firmas de nuevo abajo, sustituye a la firma guardada.")
    signature_pad(key=f"pad::{role}::{S.get('padver', 0)}")


def pdf_filename(data: dict) -> str:
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", S.get("doc_title") or data.get("m_cliente") or "parte").strip("_")
    return f"{base or 'parte'}_{date.today():%Y%m%d}.pdf"


def view_edit(model: Model) -> None:
    if S.get("flash"):
        st.toast(S.pop("flash"), icon="✅")
    st.button("← Partes", on_click=go, args=("model",), type="tertiary")
    doc = storage.load_doc(model.id, S["doc_id"]) if S.get("doc_id") else None
    ui.hero(doc["title"] if doc else "Parte nuevo", "" if doc else "Aún sin guardar.", crumb=model.name)

    with st.container(border=True, key="card_doc_meta"):
        st.text_input("Nombre del parte", key="doc_title", placeholder="p. ej. Revisión Juan Pérez")
        if doc:
            nums = [v["n"] for v in reversed(doc["versions"])]
            info = {v["n"]: v for v in doc["versions"]}
            st.selectbox(
                "Versión", nums, key="ver_sel", on_change=on_version_change, args=(model,),
                format_func=lambda n: f"v{n} · {datetime.fromisoformat(info[n]['saved']):%d/%m %H:%M}"
                + (f" · {info[n]['note']}" if info[n]["note"] else ""),
            )

    ui.section_label("Formulario")
    if model.header:
        with st.expander("🧾 Datos del parte", expanded=True):
            cols = st.columns(2)
            for i, (key, label) in enumerate(model.header):
                cols[i % 2].text_input(label, key=K(f"m_{key}"))

    for sec in model.sections:
        with st.expander(f"🔧 {sec.title} · {len(sec.items)}", expanded=False):
            for it in sec.items:
                item_widget(it)

    if model.summary or model.signatures:
        ui.section_label("Resumen y firmas" if model.summary else "Firmas")
    if model.summary:
        with st.container(border=True, key="card_resumen"):
            st.text_area("Resumen / anomalías detectadas", key=K("RESUMEN"), height=140)
    for role, title, _ in model.signatures:
        with st.container(border=True, key=f"card_sig_{role}"):
            signature_widget(role, title)

    ui.section_label("Guardar y exportar")
    with st.container(border=True, key="card_actions"):
        st.text_input("Nota de la versión (opcional)", key="ver_note", placeholder="p. ej. Pendiente firma cliente")
        # El PDF se genera al pulsar «Descargar», con los datos actuales del formulario.
        snapshot = collect(model)
        b_save, b_pdf, b_home = st.columns(3)
        b_save.button("💾 Guardar", type="primary", use_container_width=True, on_click=do_save, args=(model,))
        b_pdf.download_button(
            "⬇️ Descargar PDF", partial(model.render, snapshot), file_name=pdf_filename(snapshot),
            mime="application/pdf", type="primary", use_container_width=True,
        )
        b_home.button("🏠 Inicio", use_container_width=True, on_click=go, args=("models",))

    if doc:
        st.write("")
        with st.popover("🗑️ Eliminar parte", use_container_width=True):
            st.warning("Se borrarán todas sus versiones.")
            st.button("Sí, eliminar", on_click=do_delete, args=(model, doc["id"]))


# ───────────────────────── entrada ─────────────────────────
S.setdefault("view", "models")
current = all_models().get(S.get("model_id", ""))
if S["view"] == "new_template":
    view_new_template()
elif S["view"] == "models" or current is None:
    view_models()
elif S["view"] == "model":
    view_model(current)
else:
    view_edit(current)
