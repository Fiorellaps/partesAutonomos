"""Modelo Panasonic Aquarea Service+ (Hoja de comprobación, mantenimiento preventivo).

Los nombres de campo (CHECK n / n) son los del formulario del PDF original.
Claves de datos: nombre de campo del PDF, más:
  yn_<n>              "SI" / "NO" / "" para las filas con SI/NO
  m_<x>               cabecera (cliente, instalacion, equipo, fecha)
  nom_/dni_/sig_<rol> nombre, DNI y firma (data-URL PNG) de cliente y técnico
"""
from __future__ import annotations

import base64
from pathlib import Path

import pymupdf

from .base import Item, Model, Section

TEMPLATE = Path(__file__).parent / "templates" / "panasonic.pdf"
OBS = "Observaciones"


def _chk(n: int) -> str:
    return "CHECK0" if n == 0 else f"CHECK {n}"


def row(label: str, n: int, hint: str = OBS, multiline: bool = False) -> Item:
    return Item(label, check=_chk(n), texts=((str(n), hint),), multiline=multiline)


def yesno(label: str, n: int) -> Item:
    return Item(label, yn=(f"CHECK {n} si", f"CHECK {n} no"), texts=((str(n), OBS),))


SECTIONS = (
    Section("Comprobaciones generales", (
        row("Revisión general de la instalación", 0),
        row("Dimensión tubería primario", 1, "mm"),
        row("Revisión de la configuración de la unidad", 2),
        row("Horas de funcionamiento", 3, "horas"),
        row("Horas de arranque/parada del compresor", 4, "horas"),
        row("Rendimiento adecuado en base al SCOP frío, calor y ACS", 5),
        row("Control de la corrosión de la unidad exterior", 6),
        row("Control de las tuberías hidráulicas y frigoríficas, incluido el aislamiento", 7),
        row("Control del ventilador y del motor del ventilador", 8),
    )),
    Section("Comprobaciones hidráulicas", (
        row("Circuito primario · Dureza del agua", 9, "ºf (ref. 13 a 23 ºf)"),
        row("Circuito primario · Conductividad (Tª < 60 ºC)", 10, "μS/cm (ref. ≤500)"),
        row("Circuito primario · pH", 11, "pH (ref. 7 a 9)"),
        row("Circuito primario · Cloruros", 12, "mg/L (ref. ≤150)"),
        row("Circuito secundario · Dureza del agua", 13, "ºf (ref. 13 a 23 ºf)"),
        row("Circuito secundario · Conductividad (Tª < 60 ºC)", 14, "μS/cm (ref. ≤1200)"),
        row("Circuito secundario · pH", 15, "pH (ref. 6,5 a 8,5)"),
        row("Circuito secundario · Cloruros", 16, "mg/L (ref. ≤200)"),
        row("Comprobación del ánodo de sacrificio Zinc o Magnesio", 17, "mm (ref. ≤6 mm)"),
        yesno("Dispone ánodo", 18),
        yesno("Instalar ánodo", 19),
        yesno("Sustituir ánodo", 20),
        row("Limpieza del filtro de agua", 21),
        row("Verificación del purgador de la unidad", 22),
        row("Control anual del caudal de agua mín/máx.", 23, "Ltrs/min"),
        row("Control de la válvula de seguridad del equipo, circuito cerrado y abierto (si existe)", 24),
        row("Verificar evacuación de condensados y válvulas de seguridad de la instalación", 25),
        row("Control válvula de seguridad del depósito de ACS, externa", 26),
        row("Control válvula de seguridad del circuito cerrado, externo a la unidad", 27),
        row("Comprobación del vaso de expansión interno y externo", 50),
        row("Comprobación válvula de 3 vías (climatización y ACS)", 51),
        row("Comprobación de válvula de 2 o 3 vías (refrigeración y calefacción)", 52),
        row("Presión del agua", 53, "Bares"),
    )),
    Section("Comprobaciones frigoríficas", (
        row("Control de fugas frigoríficas (visuales)", 28),
        row("Limpieza anual del intercambiador de la unidad exterior", 29),
        row("Verificación del funcionamiento del ciclo de desescarche", 30),
        row("Presión de la bomba de calor en modo climatización y ACS", 31, "Bares"),
        row("Comprobación de saltos térmicos de temperatura", 32, "ºC"),
    )),
    Section("Comprobaciones eléctricas", (
        row("Verificación de los sensores y calibración si fuese necesario", 33),
        row("Control de todas las conexiones eléctricas", 34),
        Item("Comprobación acometida eléctrica", check=_chk(35), texts=(("35", "Tensión (V)"), ("35 A", "Consumo (A)"))),
        row("Comprobación de las protecciones térmicas del backup heater", 36),
        row("Comprobación del funcionamiento del backup heater", 37),
        row("Comprobación de la resistencia eléctrica externa de ACS (si la hay)", 38),
    )),
    Section("Emisores y sistemas auxiliares", (
        row("Fancoils (filtro, bandeja, desagües, saltos térmicos, velocidades, termostato)", 39, multiline=True),
        row("Radiadores (funcionamiento de emisores y aire en la instalación)", 40, multiline=True),
        row("Suelo radiante (colectores, válvulas termoeléctricas y de equilibrado)", 41, multiline=True),
        row("Smart Cloud CZ-TAW1 (emparejamiento con la app Comfort Cloud)", 42, "ID del dispositivo"),
    )),
)

# (clave, título, campo del PDF que ocupa la caja)
SIGNATURES = (
    ("cliente", "Conforme cliente", "CONFORME CLIENTE PAG 2"),
    ("tecnico", "Firma técnico asignado", "FIRMA TECNICO PAG 2"),
)

HEADER = (("cliente", "Cliente"), ("instalacion", "Instalación"), ("equipo", "Equipo / nº serie"), ("fecha", "Fecha"))


def _decode_png(url: str | None) -> bytes | None:
    """data-URL → bytes PNG; None si está vacía o es inválida (p. ej. «data:,»)."""
    if not url or "," not in url:
        return None
    try:
        raw = base64.b64decode(url.split(",", 1)[1])
        pymupdf.Pixmap(raw)  # valida que sea una imagen legible
        return raw
    except Exception:
        return None


def render(data: dict) -> bytes:
    doc = pymupdf.open(TEMPLATE)
    sig_rects: dict[str, pymupdf.Rect] = {}
    sig_fields = {f: key for key, _, f in SIGNATURES}

    yn_boxes: dict[str, str] = {}  # checkbox -> "SI"/"NO" requerido
    for sec in SECTIONS:
        for it in sec.items:
            if it.yn:
                n = it.texts[0][0]
                yn_boxes[it.yn[0]] = ("SI", n)
                yn_boxes[it.yn[1]] = ("NO", n)

    for page in doc:
        for w in page.widgets():
            name = w.field_name
            if name in sig_fields:
                key = sig_fields[name]
                sig_rects[key] = (page.number, pymupdf.Rect(w.rect))
                w.field_value = ""  # nombre/DNI se estampan arriba de la caja (el campo centra el texto)
                w.update()
            elif w.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                if name in yn_boxes:
                    want, n = yn_boxes[name]
                    on = data.get(f"yn_{n}") == want
                else:
                    on = bool(data.get(name))
                w.field_value = w.on_state() if on else "Off"
                w.update()
            elif w.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
                w.field_value = str(data.get(name, "") or "")
                if w.text_fontsize == 0:
                    w.text_fontsize = 8
                w.update()

    # Aplana el formulario: se ve igual en cualquier visor móvil y no se puede alterar
    doc.bake(annots=False, widgets=True)

    # Cabecera (zona libre bajo el logo en la primera página)
    p0 = doc[0]
    parts = [f"{label}: {data.get('m_' + key, '')}" for key, label in HEADER if data.get("m_" + key)]
    if parts:
        p0.insert_textbox(pymupdf.Rect(31, 90, 565, 122), "  |  ".join(parts), fontsize=8, fontname="helv")

    # Nombre/DNI y firmas
    for key, (pno, rect) in sig_rects.items():
        ident = "   ".join(x for x in (data.get(f"nom_{key}", ""), data.get(f"dni_{key}", "")) if x)
        if ident:
            doc[pno].insert_textbox(
                pymupdf.Rect(rect.x0 + 8, rect.y0 + 4, rect.x1 - 8, rect.y0 + 28), ident, fontsize=9, fontname="helv"
            )
        url = data.get(f"sig_{key}")
        png = _decode_png(url)
        if png:
            target = pymupdf.Rect(rect.x0 + 8, rect.y0 + 30, rect.x1 - 8, rect.y1 - 6)
            doc[pno].insert_image(target, stream=png, keep_proportion=True)

    out = doc.tobytes(garbage=3, deflate=True)
    doc.close()
    return out


MODEL = Model(
    id="panasonic",
    name="Panasonic Aquarea Service+",
    description="Hoja de comprobación · Mantenimiento preventivo oficial (2 páginas)",
    sections=SECTIONS,
    render=render,
    signatures=SIGNATURES,
    icon="🌡️",
    brand="Panasonic",
    header=HEADER,
)
