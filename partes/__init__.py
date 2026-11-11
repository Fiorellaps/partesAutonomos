"""Registro de modelos de parte. Para añadir uno integrado: crear su módulo y registrarlo aquí.
Las plantillas que sube el usuario se cargan de disco con `all_models()`."""
from . import custom
from .base import Model
from .panasonic import MODEL as PANASONIC

MODELS: dict[str, Model] = {m.id: m for m in (PANASONIC,)}


def all_models() -> dict[str, Model]:
    return {**MODELS, **custom.load_all()}
