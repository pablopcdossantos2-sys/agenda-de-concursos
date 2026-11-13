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
    executable = _vbs_quote(command[0])
    arguments = " ".join('"' + _vbs_quote(part) + '"' for part in command[1:])
    full_command = f'"{executable}"' + (f" {arguments}" if arguments else "")
    script = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run "{_vbs_quote(full_command)}", 0, False\n'
    )
    destination = folder / STARTUP_FILENAME
    destination.write_text(script, encoding="utf-8")
    return destination


def disable_startup() -> None:
    if sys.platform != "win32":
        raise OSError("A inicialização automática está disponível apenas no Windows.")
    target = startup_folder() / STARTUP_FILENAME
    if target.exists():
        target.unlink()


def startup_enabled() -> bool:
    if sys.platform != "win32":
        return False
    return (startup_folder() / STARTUP_FILENAME).exists()
