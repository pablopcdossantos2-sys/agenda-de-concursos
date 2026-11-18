from __future__ import annotations

import os
import sys
from pathlib import Path


def app_root() -> Path:
    """Pasta do executável ou raiz do código-fonte."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def app_data_dir() -> Path:
    """Dados graváveis do usuário, separados dos arquivos instalados."""
    if sys.platform == "win32":
        default = Path.home() / "AppData" / "Local"
        base = Path(os.environ.get("LOCALAPPDATA") or default)
    else:
        default = Path.home() / ".local" / "share"
        base = Path(os.environ.get("XDG_DATA_HOME") or default)
    folder = base / "AgendaDeConcursos"
    folder.mkdir(parents=True, exist_ok=True)
    return folder
