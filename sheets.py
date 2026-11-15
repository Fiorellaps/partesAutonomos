"""Capa de persistencia: Google Sheets como base de datos para las tablas de gestión.

Una pestaña por tabla (historico, pendientes, comunicaciones).
Cada fila es un registro; la primera fila son los nombres de los campos.

La función `load(tabla)` y `save(tabla, rows)` tienen la misma firma que el módulo
`datos.py` usaba con JSON, así que el resto de la app no cambia.

En local también funciona: si Streamlit Secrets no tiene la clave `gcp_service_account`,
cae al fichero JSON en `secrets/` (si existe).
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import gspread
import streamlit as st
from gspread.utils import rowcol_to_a1

SHEET_NAME = "gestion-partes"
TABLAS = ("historico", "pendientes", "comunicaciones")

# ───────────── conexión (cacheada en la sesión) ─────────────────────────────
_lock = threading.Lock()
_client: gspread.Client | None = None
_book: gspread.Spreadsheet | None = None


def _connect() -> gspread.Spreadsheet:
    global _client, _book
    with _lock:
        if _book is not None:
            return _book
        try:
            creds = dict(st.secrets["gcp_service_account"])
            # gspread espera la clave con saltos de línea reales
            if "\\n" in creds.get("private_key", ""):
                creds["private_key"] = creds["private_key"].replace("\\n", "\n")
            gc = gspread.service_account_from_dict(creds)
        except (KeyError, AttributeError):
            # fallback a fichero local (desarrollo sin despliegue)
            candidates = list(Path("secrets").glob("*.json")) if Path("secrets").exists() else []
            if not candidates:
                raise RuntimeError("No hay credenciales de Google configuradas.")
            gc = gspread.service_account(filename=str(candidates[0]))
        try:
            name = st.secrets.get("sheets", {}).get("sheet_name", SHEET_NAME)
        except Exception:
            name = SHEET_NAME
        _book = gc.open(name)
        return _book


def _ws(tabla: str) -> gspread.Worksheet:
    if tabla not in TABLAS:
        raise ValueError(f"Tabla desconocida: {tabla}")
    book = _connect()
    try:
        return book.worksheet(tabla)
    except gspread.WorksheetNotFound:
        ws = book.add_worksheet(title=tabla, rows=2, cols=1)
        return ws


# ───────────── serialización ────────────────────────────────────────────────
def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _from_str(s: str) -> Any:
    return s  # todos los valores se quedan como str; los campos de fecha ya son ISO


# ───────────── lectura / escritura ──────────────────────────────────────────
def load(tabla: str) -> list[dict]:
    ws = _ws(tabla)
    rows = ws.get_all_records(default_blank="", head=1, numericise_ignore=["all"])
    return [dict(r) for r in rows]


def save(tabla: str, rows: list[dict]) -> None:
    ws = _ws(tabla)
    if not rows:
        # deja solo la cabecera (si existe) y borra el resto
        ws.clear()
        return
    # columnas = unión de todas las claves (preserva orden de la primera fila)
    all_keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in all_keys:
                all_keys.append(k)
    matrix = [[k for k in all_keys]] + [[_to_str(r.get(k, "")) for k in all_keys] for r in rows]
    ws.clear()
    ws.update(range_name="A1", values=matrix)
