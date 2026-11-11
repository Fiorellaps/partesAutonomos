from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Item:
    """Una fila del parte. Los nombres son los de los campos del PDF."""

    label: str
    check: str | None = None  # checkbox del PDF
    texts: tuple[tuple[str, str], ...] = ()  # (campo de texto del PDF, ayuda/unidad)
    yn: tuple[str, str] | None = None  # (checkbox SI, checkbox NO)
    multiline: bool = False


@dataclass(frozen=True)
class Section:
    title: str
    items: tuple[Item, ...]


@dataclass(frozen=True)
class Model:
    id: str
    name: str
    description: str
    sections: tuple[Section, ...]
    render: Callable[[dict], bytes] = field(repr=False)
    # Cajas de firma: (clave, título, campo del PDF donde se estampan nombre/DNI y firma)
    signatures: tuple[tuple[str, str, str], ...] = ()
    icon: str = "📋"  # icono de la tarjeta del modelo
    brand: str = ""  # marca, se muestra como etiqueta
    header: tuple[tuple[str, str], ...] = ()  # (clave, etiqueta) de los datos de cabecera
    summary: bool = True  # muestra el cuadro «Resumen / anomalías»
    custom: bool = False  # plantilla añadida por el usuario (se puede eliminar)
