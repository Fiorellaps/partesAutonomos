"""Datos de gestión: histórico de visitas, clientes actuales (visitas pendientes) y comunicaciones.

Persistencia: Google Sheets en producción (Streamlit Cloud), JSON local como fallback.
  - En Streamlit Cloud, las credenciales van en [gcp_service_account] dentro de secrets.toml.
  - En local, si no hay credenciales de GCP, se sigue usando data/gestion/<tabla>.json.
El histórico y los clientes actuales se cargan desde el Excel «CITAS PANASONIC.xlsx»:
  - pestaña «NO TOCAR»             → histórico (visitas realizadas y cerradas)
  - pestaña «PANASONIC PENDIENTES» → clientes actuales (visitas pendientes)
"""
from __future__ import annotations

import io
import json
import re
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

import streamlit as st

import storage

DIR = storage.DATA_DIR / "gestion"
EXCEL_LOCAL = Path(__file__).parent / "CITAS PANASONIC.xlsx"
TABLAS = ("historico", "pendientes", "comunicaciones")


# ───────────────────────── detección de backend ─────────────────────────────
def _use_sheets() -> bool:
    """True si hay credenciales de GCP en secrets.toml (Streamlit Cloud o local con secrets)."""
    try:
        return "gcp_service_account" in st.secrets
    except Exception:
        return False


# ───────────────────────── columnas visibles ─────────────────────────

# ───────────────────────── columnas visibles ─────────────────────────
COLS_HISTORICO = {
    "orden": "Orden", "fecha_limite": "Fecha límite", "direccion": "Dirección", "correo": "Correo",
    "cliente": "Cliente", "movil": "Móvil", "servicio": "Servicio", "descripcion": "Descripción SAT",
    "observaciones": "Observaciones", "cita": "Cita", "cerrada": "Cerrada el",
}
COLS_PENDIENTES = {
    "cliente": "Cliente", "cita": "Cita", "estado": "Estado", "orden": "Orden", "fecha_limite": "Fecha límite",
    "direccion": "Dirección", "correo": "Correo", "movil": "Móvil",
    "tipo": "Tipo de servicio", "servicio": "Servicio", "descripcion": "Descripción SAT",
    "notas": "Notas",
}
TECNICOS = ["", "Camilo", "Miguel", "Juan", "Pepe"]
TIPOS_COM = ("Cliente", "Interna")
CANALES_COM = ("WhatsApp", "Teléfono", "Correo", "Presencial", "Otro")

# ───────────────────────── colores por estado (columna D del Excel) ─────────────────────────
ESTADOS_COM = ("Pendiente", "Esperando respuesta", "Hecha")

# ───────────────────────── colores por estado (columna D del Excel) ─────────────────────────
AMARILLO, SALMON, NARANJA, ROJO, ROJO_VIVO, BLANCO = "#FFFF00", "#F1A497", "#F1A983", "#FF2F2F", "#FF0000", "#FFFFFF"


def color_estado(estado: str) -> tuple[str, str]:
    """(color de la fila, color de la celda Estado) para un estado escrito a mano.

    Reproduce el código de colores del Excel; se usa cuando el estado se cambia desde la app
    (los registros importados conservan el color exacto que tenían en el Excel).
    """
    e = (estado or "").upper()
    if "YA ESTA REALIZADO" in e or "YA ESTÁ REALIZADO" in e:
        return ROJO_VIVO, ROJO_VIVO
    if "CANCELA" in e:
        return ROJO, ROJO
    if any(w in e for w in ("MAL ESTADO", "MAL ESTAOD", "POLVO", "GARANTIA", "GARANTÍA", "AVERIA", "AVERÍA")):
        return AMARILLO, ROJO
    if "CORREO ERR" in e:
        return NARANJA, NARANJA
    if any(w in e for w in ("CORREO BLOQUEADO", "PISO VENDIDO")):
        return SALMON, SALMON
    if any(w in e for w in ("CONFIRM", "COMFIRM", "REALIZADO", "LLAMAR")):
        return AMARILLO, AMARILLO
    return BLANCO, BLANCO


# ───────────────────────── persistencia ─────────────────────────
def _file(tabla: str) -> Path:
    if tabla not in TABLAS:
        raise ValueError("Tabla no válida")
    return DIR / f"{tabla}.json"


def _json_load(tabla: str) -> list[dict]:
    p = _file(tabla)
    try:
        return json.loads(p.read_text("utf-8")) if p.exists() else []
    except (OSError, json.JSONDecodeError):
        return []


def _json_save(tabla: str, rows: list[dict]) -> None:
    p = _file(tabla)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False, default=str), "utf-8")
    tmp.replace(p)


def load(tabla: str) -> list[dict]:
    if _use_sheets():
        import sheets as _sh
        rows = _sh.load(tabla)
        if not rows:
            _auto_import_sheets()
            rows = _sh.load(tabla)
        return rows
    _auto_import()
    return _json_load(tabla)


def save(tabla: str, rows: list[dict]) -> None:
    if _use_sheets():
        import sheets as _sh
        _sh.save(tabla, rows)
    else:
        _json_save(tabla, rows)


def new_id() -> str:
    return uuid.uuid4().hex[:8]


def update(tabla: str, rid: str, **changes) -> None:
    rows = load(tabla)
    for r in rows:
        if r["id"] == rid:
            r.update(changes)
    save(tabla, rows)


def _auto_import() -> None:
    """La primera vez (sin datos en JSON local) carga el Excel de la carpeta de la app, si existe."""
    if _file("pendientes").exists() or _file("historico").exists() or not EXCEL_LOCAL.exists():
        return
    try:
        import_excel(EXCEL_LOCAL.read_bytes())
    except Exception:
        pass


def _auto_import_sheets() -> None:
    """Primera vez en Sheets: si el Excel existe en disco, lo importa."""
    if not EXCEL_LOCAL.exists():
        return
    try:
        import_excel(EXCEL_LOCAL.read_bytes())
    except Exception:
        pass
    except Exception:  # un Excel ilegible no debe tumbar la app; se puede importar a mano desde el inicio
        pass


# ───────────────────────── importación del Excel ─────────────────────────
def _txt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y") if v.time() == time(0) else v.strftime("%d/%m/%Y %H:%M")
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).replace("\xa0", " ").strip()


def _iso(v) -> str:
    return v.date().isoformat() if isinstance(v, datetime) else ""


def _fill(cell) -> str:
    f = cell.fill
    if f is None or not f.fill_type or f.fgColor is None or f.fgColor.type != "rgb":
        return BLANCO
    rgb = str(f.fgColor.rgb)
    return f"#{rgb[-6:].upper()}" if re.fullmatch(r"[0-9A-Fa-f]{8}", rgb) else BLANCO


def _blocks(ws, first_row: int, cols: dict[str, int], addr_col: int):
    """Recorre bloques de 3 filas. Devuelve (fila inicial, {campo: valor bruto}, dirección)."""
    last = ws.max_row
    for r in range(first_row, last + 1, 3):
        rows = range(r, min(r + 3, last + 1))
        vals = {}
        for field, c in cols.items():
            found = [ws.cell(i, c).value for i in rows if ws.cell(i, c).value not in (None, "")]
            vals[field] = found
        addr = ", ".join(_txt(ws.cell(i, addr_col).value) for i in rows if ws.cell(i, addr_col).value)
        yield r, vals, addr


def _first(vals: list):
    return vals[0] if vals else None


def _orden(vals: list) -> str:
    """El número de orden (SA-…); en algún bloque la fila 1 trae un resto de cabecera («Columna1»)."""
    for v in vals:
        if _txt(v).upper().startswith("SA-"):
            return _txt(v)
    return _txt(_first(vals))


def _parse_historico(ws) -> list[dict]:
    cols = {"orden": 2, "fecha_limite": 3, "correo": 5, "cliente": 6, "movil": 7, "servicio": 8,
            "descripcion": 9, "observaciones": 10, "cita": 11}
    out = []
    for _, v, addr in _blocks(ws, 2, cols, addr_col=4):
        orden = _orden(v["orden"])
        if not orden and not _first(v["cliente"]):
            continue
        cita = _first(v["cita"])
        out.append({
            "id": new_id(), "orden": orden, "fecha_limite": _iso(_first(v["fecha_limite"])), "direccion": addr,
            "correo": _txt(_first(v["correo"])), "cliente": _txt(_first(v["cliente"])),
            "movil": _txt(_first(v["movil"])), "servicio": _txt(_first(v["servicio"])),
            "descripcion": _txt(_first(v["descripcion"])), "observaciones": _txt(_first(v["observaciones"])),
            "cita": _txt(cita), "cita_fecha": _iso(cita), "cerrada": "",
        })
    return out


def _parse_pendientes(ws) -> list[dict]:
    cols = {"cita": 2, "estado": 4, "orden": 5, "fecha_limite": 6, "correo": 8, "cliente": 9, "movil": 10,
            "tipo": 11, "servicio": 12, "descripcion": 13}
    out = []
    for r, v, addr in _blocks(ws, 1, cols, addr_col=7):
        orden = _orden(v["orden"])
        if not orden and not _first(v["cliente"]):
            continue
        cita_raw = _first(v["cita"])
        dt = parse_cita(cita_raw)
        out.append({
            "id": new_id(), "cita": _txt(cita_raw), "cita_dt": dt.isoformat(timespec="minutes") if dt else "",
            "estado": _txt(_first(v["estado"])), "orden": orden, "fecha_limite": _iso(_first(v["fecha_limite"])),
            "direccion": addr, "correo": _txt(_first(v["correo"])), "cliente": _txt(_first(v["cliente"])),
            "movil": _txt(_first(v["movil"])), "tipo": _txt(_first(v["tipo"])),
            "servicio": _txt(_first(v["servicio"])), "descripcion": _txt(_first(v["descripcion"])), "notas": "",
            "color_fila": _fill(ws.cell(r, 5)), "color_estado": _fill(ws.cell(r, 4)),
        })
    return out


def import_excel(content: bytes) -> tuple[int, int]:
    """Sustituye histórico y clientes actuales por el contenido del Excel. Devuelve (nº histórico, nº pendientes)."""
    import openpyxl
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # openpyxl avisa de extensiones de Excel que no usa
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    names = {n.strip().upper(): n for n in wb.sheetnames}
    if "NO TOCAR" not in names or "PANASONIC PENDIENTES" not in names:
        raise ValueError("El Excel debe tener las pestañas «NO TOCAR» y «PANASONIC PENDIENTES».")
    hist = _parse_historico(wb[names["NO TOCAR"]])
    pend = _parse_pendientes(wb[names["PANASONIC PENDIENTES"]])
    save("historico", hist)
    save("pendientes", pend)
    return len(hist), len(pend)


# ───────────────────────── fechas ─────────────────────────
_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_TIME = re.compile(r"(\d{1,2})[,:.h](\d{2})")


def parse_cita(v) -> datetime | None:
    """Convierte la cita del Excel a fecha y hora: «21/10/2026 9,00», «04/11/2026 a las 11,30», fechas de Excel…"""
    if isinstance(v, datetime):
        return v
    if isinstance(v, date):
        return datetime.combine(v, time(0))
    m = _DATE.search(str(v or ""))
    if not m:
        return None
    d, mo, y = map(int, m.groups())
    t = _TIME.search(str(v)[m.end():])
    hh, mm = (int(t.group(1)), int(t.group(2))) if t else (0, 0)
    try:
        return datetime(y, mo, d, hh if hh < 24 else 0, mm if mm < 60 else 0)
    except ValueError:
        return None


def format_cita(dt: datetime) -> str:
    """Mismo formato que se usa en el Excel: «21/10/2026 9,30»."""
    return dt.strftime("%d/%m/%Y") if dt.time() == time(0) else f"{dt:%d/%m/%Y} {dt.hour},{dt.minute:02d}"


def cita_dt(row: dict) -> datetime | None:
    return datetime.fromisoformat(row["cita_dt"]) if row.get("cita_dt") else None


def fecha_ref_historico(row: dict) -> date | None:
    """Fecha de la visita cerrada: la de cierre en la app; si no, la de la cita; si no, la fecha límite."""
    for k in ("cerrada", "cita_fecha", "fecha_limite"):
        if row.get(k):
            return date.fromisoformat(row[k][:10])
    return None


def ultimo_mes(rows: list[dict], hoy: date | None = None) -> list[dict]:
    desde = (hoy or date.today()) - timedelta(days=30)
    return [r for r in rows if (f := fecha_ref_historico(r)) and f >= desde]


# ───────────────────────── acciones ─────────────────────────
def set_estado(rid: str, estado: str) -> None:
    fila, celda = color_estado(estado)
    update("pendientes", rid, estado=estado, color_fila=fila, color_estado=celda)


def cerrar_visita(rid: str) -> None:
    """Pasa una visita de «Clientes actuales» al histórico."""
    pend = load("pendientes")
    row = next((r for r in pend if r["id"] == rid), None)
    if row is None:
        return
    obs = " · ".join(x for x in (row.get("estado", ""), row.get("notas", "")) if x)
    servicio = " · ".join(x for x in (row.get("tipo", ""), row.get("servicio", "")) if x)
    hist = load("historico")
    hist.append({
        "id": new_id(), "orden": row["orden"], "fecha_limite": row["fecha_limite"], "direccion": row["direccion"],
        "correo": row["correo"], "cliente": row["cliente"], "movil": row["movil"], "servicio": servicio,
        "descripcion": row["descripcion"], "observaciones": obs, "cita": row["cita"],
        "cita_fecha": row["cita_dt"][:10], "cerrada": date.today().isoformat(),
    })
    save("historico", hist)
    save("pendientes", [r for r in pend if r["id"] != rid])


def add_comunicacion(**fields) -> None:
    rows = load("comunicaciones")
    base = {"id": new_id(), "fecha": date.today().isoformat(), "tipo": "Cliente", "contacto": "", "canal": "WhatsApp",
            "asunto": "", "estado": "Pendiente", "recordar": "", "notas": ""}
    rows.append({**base, **fields})
    save("comunicaciones", rows)


# ───────────────────────── WhatsApp ─────────────────────────
def whatsapp_number(raw) -> str | None:
    """Número en formato internacional sin «+» para wa.me.

    Casos que se normalizan:
    - «+34 685 278 126» → «34685278126»
    - «0034...»         → «34...»
    - «00447311451838 / Tlf España: 611197306» → primer número antes de «/»
    - «9 cifras empezando por 6/7» sin prefijo → añade «34»
    - Espacios, guiones y paréntesis se eliminan siempre
    """
    # tomar solo el primer número si hay varios separados por / ; " y " o "Tlf"
    first = re.split(r"[/;]|\s+y\s+|\s+Tlf\b", str(raw or ""), maxsplit=1)[0].strip()
    # quitar caracteres no numéricos salvo el + inicial
    has_plus = first.startswith("+")
    digits = re.sub(r"\D", "", first)
    # eliminar «00» o «+» como prefijo de código de país
    if digits.startswith("00"):
        digits = digits[2:]
    # 9 cifras empezando por 6, 7 o 9 → España
    if len(digits) == 9 and digits[0] in "679":
        digits = "34" + digits
    # 10 cifras con «34» al principio (ej. 34658437536) ya están bien
    # 971564489874 (12 dígitos, empieza por 971...) → se deja como está
    return digits if len(digits) >= 7 else None


def whatsapp_url(raw: str, text: str = "") -> str | None:
    from urllib.parse import quote

    num = whatsapp_number(raw)
    if not num:
        return None
    return f"https://wa.me/{num}" + (f"?text={quote(text)}" if text else "")
