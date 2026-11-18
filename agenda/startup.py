from __future__ import annotations

import os
import sys
from pathlib import Path

from agenda.paths import entry_command


STARTUP_FILENAME = "Agenda de Concursos.vbs"


def startup_folder() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("A pasta APPDATA do usuário não foi encontrada.")
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _vbs_quote(value: str) -> str:
    return value.replace('"', '""')


def enable_startup() -> Path:
    if sys.platform != "win32":
        raise OSError("A inicialização automática está disponível apenas no Windows.")
    folder = startup_folder()
    folder.mkdir(parents=True, exist_ok=True)
    command = entry_command()
    full_command = " ".join(f'"{part}"' for part in command)
    script = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run "{_vbs_quote(full_command)}", 0, False\n'
    )
    destination = folder / STARTUP_FILENAME
    contents = script.replace("\n", "\r\n").encode("utf-16")
    if not destination.exists() or destination.read_bytes() != contents:
        destination.write_bytes(contents)
    return destination


def disable_startup() -> None:
    if sys.platform != "win32":
        raise OSError("A inicialização automática está disponível apenas no Windows.")
    target = startup_folder() / STARTUP_FILENAME
    if target.exists():
        target.unlink()


def startup_enabled() -> bool:
    if sys.platform != "win32" or not os.environ.get("APPDATA"):
        return False
    return (startup_folder() / STARTUP_FILENAME).exists()
