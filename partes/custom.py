"""Plantillas PDF añadidas por el usuario.

Flujo: `analyze(pdf)` detecta los campos del formulario del PDF → el usuario revisa etiquetas y tipos →
`save_template(...)` guarda PDF + metadatos en data/_templates/<id>/ → `load_all()` construye un `Model`
por plantilla, con el mismo formato que los modelos integrados (secciones, firmas, render).
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
from datetime import datetime
from functools import partial
from pathlib import Path

import pymupdf

import storage

from .base import Item, Model, Section
from .panasonic import _decode_png

TEMPLATES_DIR = storage.DATA_DIR / "_templates"
KINDS = {"text": "Texto", "check": "Casilla", "sign": "Firma"}
_SIGN_NAME = re.compile(r"firma|signature|sign\b|conforme", re.I)
_T = pymupdf.PDF_WIDGET_TYPE_TEXT
_TEXTLIKE = (_T, pymupdf.PDF_WIDGET_TYPE_COMBOBOX, pymupdf.PDF_WIDGET_TYPE_LISTBOX)


# ───────────────────────── análisis del PDF ─────────────────────────
def _chain(words: list, rect: pymupdf.Rect, from_right: bool) -> str:
    """Palabras contiguas a un lado del campo (más cercanas primero), unidas en una etiqueta."""
    ws = words[::-1] if from_right else words
    out, prev = [], (rect.x0, 0, rect.x1, 0)
    for w in ws:
        gap = (prev[0] - w[2]) if from_right else (w[0] - prev[2])
        if gap > (30 if prev[1] == 0 else 12) or len(out) >= 10:
            break
        out.append(w)
        prev = (w[0], 1, w[2], 1)
    if from_right:
        out.reverse()
    return " ".join(w[4] for w in out)


def _guess_label(words: list, rect: pymupdf.Rect, prefer_right: bool) -> str:
    cy = (rect.y0 + rect.y1) / 2
    tol = max(6, rect.height / 2)
    line = [w for w in words if abs((w[1] + w[3]) / 2 - cy) <= tol]
    left = sorted((w for w in line if w[2] <= rect.x0 + 2), key=lambda w: w[0])
    right = sorted((w for w in line if w[0] >= rect.x1 - 2), key=lambda w: w[0])
    tries = [_chain(right, rect, False), _chain(left, rect, True)]
    if not prefer_right:
        tries.reverse()
    for t in tries:
        if t:
            return t
    above = sorted(
        (w for w in words if w[3] <= rect.y0 + 2 and rect.y0 - w[3] <= 14 and w[2] > rect.x0 and w[0] < rect.x1),
        key=lambda w: w[0],
    )
    return " ".join(w[4] for w in above)


def analyze(pdf: bytes) -> tuple[list[dict], int]:
    """Devuelve (campos detectados, nº de campos no soportados: radios y botones).

    Cada campo: {name, kind: text|check|sign, label, page, multiline}. Lanza ValueError si el PDF no es legible.
    """
    try:
        doc = pymupdf.open(stream=pdf, filetype="pdf")
    except Exception as e:  # pymupdf lanza varios tipos según el fallo
        raise ValueError("No se pudo leer el PDF") from e
    fields: list[dict] = []
    seen: set[str] = set()
    skipped = 0
    for page in doc:
        words = page.get_text("words")
        widgets = sorted(page.widgets(), key=lambda w: (round(w.rect.y0 / 4), w.rect.x0))
        for w in widgets:
            name = w.field_name
            if not name or name in seen:
                continue
            if w.field_type == pymupdf.PDF_WIDGET_TYPE_SIGNATURE:
                kind = "sign"
            elif w.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                kind = "check"
            elif w.field_type in _TEXTLIKE:
                kind = "sign" if _SIGN_NAME.search(name) else "text"
            else:
                skipped += 1
                continue
            seen.add(name)
            label = _guess_label(words, w.rect, prefer_right=kind == "check")
            label = re.sub(r"\s+", " ", label).strip(" :.-") or name
            fields.append({
                "name": name, "kind": kind, "label": label, "page": page.number + 1,
                "multiline": bool(w.field_type == _T and w.field_flags & pymupdf.PDF_TX_FIELD_IS_MULTILINE),
            })
    doc.close()
    return fields, skipped


# ───────────────────────── almacenamiento ─────────────────────────
def save_template(name: str, pdf: bytes, fields: list[dict]) -> str:
    tid = "t" + uuid.uuid4().hex[:8]
    folder = TEMPLATES_DIR / tid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "template.pdf").write_bytes(pdf)
    meta = {"id": tid, "name": name, "created": datetime.now().isoformat(timespec="seconds"), "fields": fields}
    (folder / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), "utf-8")
    return tid


def delete_template(tid: str) -> None:
    if not re.fullmatch(r"t[a-f0-9]{8}", tid):
        raise ValueError("Identificador no válido")
    shutil.rmtree(TEMPLATES_DIR / tid, ignore_errors=True)
    shutil.rmtree(storage.DATA_DIR / tid, ignore_errors=True)  # y los partes creados con ella


def load_all() -> dict[str, Model]:
    models: dict[str, Model] = {}
    for meta_file in sorted(TEMPLATES_DIR.glob("*/meta.json")) if TEMPLATES_DIR.exists() else []:
        try:
            meta = json.loads(meta_file.read_text("utf-8"))
            models[meta["id"]] = _build_model(meta, meta_file.parent / "template.pdf")
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return models


# ───────────────────────── modelo y render ─────────────────────────
def _build_model(meta: dict, pdf_path: Path) -> Model:
    pages: dict[int, list[Item]] = {}
    signatures = []
    fields = []
    for f in meta["fields"]:
        f = dict(f)
        if f["kind"] == "sign":
            f["role"] = f"s{len(signatures) + 1}"
            signatures.append((f["role"], f["label"], f["name"]))
        elif f["kind"] == "check":
            pages.setdefault(f["page"], []).append(Item(f["label"], check=f["name"]))
        else:
            pages.setdefault(f["page"], []).append(
                Item(f["label"], texts=((f["name"], "Valor"),), multiline=f.get("multiline", False))
            )
        fields.append(f)
    sections = tuple(Section(f"Página {p}", tuple(items)) for p, items in sorted(pages.items()))
    n = sum(len(s.items) for s in sections)
    return Model(
        id=meta["id"], name=meta["name"], description=f"Plantilla propia · {n} campos, {len(signatures)} firma(s)",
        sections=sections, render=partial(_render, pdf_path, fields), signatures=tuple(signatures),
        summary=False, custom=True,
    )


def _render(pdf_path: Path, fields: list[dict], data: dict) -> bytes:
    by_name = {f["name"]: f for f in fields}
    doc = pymupdf.open(pdf_path)
    sig_rects: dict[str, tuple[int, pymupdf.Rect]] = {}
    for page in doc:
        for w in page.widgets():
            f = by_name.get(w.field_name)
            if not f:
                continue
            if f["kind"] == "sign":
                sig_rects.setdefault(f["role"], (page.number, pymupdf.Rect(w.rect)))
                if w.field_type in _TEXTLIKE:
                    w.field_value = ""
                    w.update()
            elif f["kind"] == "check" and w.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                w.field_value = w.on_state() if data.get(w.field_name) else "Off"
                w.update()
            elif f["kind"] == "text" and w.field_type in _TEXTLIKE:
                w.field_value = str(data.get(w.field_name, "") or "")
                if w.field_type == _T and w.text_fontsize == 0:
                    w.text_fontsize = 8
                w.update()

    doc.bake(annots=False, widgets=True)  # aplana el formulario

    for role, (pno, rect) in sig_rects.items():
        ident = "   ".join(x for x in (data.get(f"nom_{role}", ""), data.get(f"dni_{role}", "")) if x)
        if ident:
            doc[pno].insert_textbox(
                pymupdf.Rect(rect.x0 + 4, rect.y0 + 2, rect.x1 - 4, rect.y0 + 16), ident, fontsize=8, fontname="helv"
            )
        png = _decode_png(data.get(f"sig_{role}"))
        if png:
            top = rect.y0 + (16 if ident else 2)
            doc[pno].insert_image(pymupdf.Rect(rect.x0 + 4, top, rect.x1 - 4, rect.y1 - 2), stream=png, keep_proportion=True)

    out = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return out
