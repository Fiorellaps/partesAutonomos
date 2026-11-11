"""Componente de firma táctil (canvas HTML, sin dependencias externas)."""
from pathlib import Path

import streamlit.components.v1 as components

_pad = components.declare_component(
    "signature_pad", path=str(Path(__file__).parent / "components" / "signature")
)


def signature_pad(key: str) -> str | None:
    """Devuelve un data-URL PNG (fondo transparente), "" si se borró, None si no se ha tocado."""
    return _pad(key=key, default=None)
