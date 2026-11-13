from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Diretório da distribuição; no modo fonte, raiz do repositório."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def app_data_dir() -> Path:
    """Dados portáteis ao lado do aplicativo."""
    folder = app_root() / "data"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def entry_command() -> tuple[str, ...]:
    """Comando de inicialização compatível com fonte e PyInstaller."""
    if getattr(sys, "frozen", False):
        return (str(Path(sys.executable).resolve()),)
    script = app_root() / "main.py"
    return (str(Path(sys.executable).resolve()), str(script))
