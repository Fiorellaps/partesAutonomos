"""Persistencia en ficheros JSON: data/<modelo>/<id>.json con todas las versiones de un parte.

OJO: en Streamlit Community Cloud el disco es efímero (se pierde al reiniciar/redesplegar).
Para persistencia real, sustituir este módulo por Supabase/Google Sheets/etc.
manteniendo las mismas funciones.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.environ.get("PARTES_DATA", Path(__file__).parent / "data"))
_ID = re.compile(r"^[a-z0-9]{1,32}$")


def _path(model_id: str, doc_id: str) -> Path:
    if not _ID.match(model_id) or not _ID.match(doc_id):
        raise ValueError("Identificador no válido")
    return DATA_DIR / model_id / f"{doc_id}.json"


def list_docs(model_id: str) -> list[dict]:
    folder = DATA_DIR / model_id
    docs = []
    for f in folder.glob("*.json") if folder.exists() else []:
        try:
            docs.append(json.loads(f.read_text("utf-8")))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(docs, key=lambda d: d.get("updated", ""), reverse=True)


def load_doc(model_id: str, doc_id: str) -> dict | None:
    p = _path(model_id, doc_id)
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def save_version(model_id: str, doc_id: str | None, title: str, data: dict, note: str = "") -> dict:
    """Añade una versión nueva (nunca sobrescribe las anteriores)."""
    now = datetime.now().isoformat(timespec="seconds")
    doc = load_doc(model_id, doc_id) if doc_id else None
    if doc is None:
        doc = {"id": doc_id or uuid.uuid4().hex[:8], "model": model_id, "created": now, "versions": []}
    doc["title"] = title or "Sin título"
    doc["updated"] = now
    n = max((v["n"] for v in doc["versions"]), default=0) + 1
    doc["versions"].append({"n": n, "saved": now, "note": note, "data": data})
    _write(doc)
    return doc


def delete_doc(model_id: str, doc_id: str) -> None:
    _path(model_id, doc_id).unlink(missing_ok=True)


def _write(doc: dict) -> None:
    p = _path(doc["model"], doc["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False), "utf-8")
    tmp.replace(p)
