from __future__ import annotations

import sys
from pathlib import Path


def asset_path(name: str) -> Path:
    """Resolve recursos tanto no código-fonte quanto na distribuição PyInstaller."""
    if not name or Path(name).name != name:
        raise ValueError("Nome de recurso inválido.")
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / "assets" / name
