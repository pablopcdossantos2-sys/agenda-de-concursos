from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
APP_NAME = "AgendaDeConcursos"
PACKAGE_VERSION = "1.0.0.0"
MANIFEST = Path(__file__).with_name("AppxManifest.xml")


def render_manifest(name: str, publisher: str, display_name: str, version: str) -> str:
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", version):
        raise ValueError("Informe uma versão MSIX com quatro números, como 1.0.0.0.")
    version_parts = [int(part) for part in version.split(".")]
    if version_parts[0] == 0 or version_parts[3] != 0 or max(version_parts) > 65535:
        raise ValueError("Use versão com primeiro número positivo, último zero e campos até 65535.")
    values = {
        "PACKAGE_NAME": name,
        "PUBLISHER": publisher,
        "PUBLISHER_DISPLAY_NAME": display_name,
        "VERSION": ".".join(map(str, version_parts)),
    }
    return re.sub(
        r"@([A-Z_]+)@",
        lambda token: escape(values[token.group(1)], {'"': "&quot;"}),
        MANIFEST.read_text(encoding="utf-8"),
    )


def makeappx_path() -> str:
    command = shutil.which("makeappx.exe")
    if command:
        return command
    sdk_bin = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits" / "10" / "bin"
    candidates = [path for path in sdk_bin.glob("10.*/x64/MakeAppx.exe") if path.is_file()]
    if not candidates:
        raise FileNotFoundError("Instale o Windows SDK com a ferramenta MakeAppx.exe.")
    return str(max(candidates, key=lambda path: tuple(map(int, path.parents[1].name.split(".")))))


def render_logos(destination: Path) -> None:
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QGuiApplication, QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    app = QGuiApplication(["build_msix", "-platform", "offscreen"])
    destination.mkdir()
    renderer = QSvgRenderer(str(ROOT / "assets" / "app_icon.svg"))
    if not renderer.isValid():
        raise ValueError("Não foi possível ler o ícone do aplicativo.")
    for name, size in (("StoreLogo", 50), ("Square44x44Logo", 44), ("Square150x150Logo", 150)):
        image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        if not image.save(str(destination / f"{name}.png")):
            raise OSError(f"Não foi possível salvar a imagem {name}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera um MSIX x64 para a Microsoft Store.")
    parser.add_argument("--package-name", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--publisher-display-name", required=True)
    parser.add_argument("--version", default=PACKAGE_VERSION)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "AgendaDeConcursos.msix")
    args = parser.parse_args()
    if sysconfig.get_platform() != "win-amd64":
        parser.error("Use Python x64 no Windows.")
    output = args.output.resolve()
    if output.suffix.lower() != ".msix":
        parser.error("O arquivo de saída precisa terminar em .msix.")
    manifest = render_manifest(args.package_name, args.publisher, args.publisher_display_name, args.version)
    makeappx = makeappx_path()
    with TemporaryDirectory(prefix="agenda-msix-") as directory:
        build = Path(directory)
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
             "--name", APP_NAME, "--onedir", "--add-data", "assets;assets",
             "--distpath", str(build), "--workpath", str(build / "work"),
             "--specpath", str(build), str(ROOT / "main.py")],
            cwd=ROOT,
            check=True,
        )
        package = build / APP_NAME
        (package / "AppxManifest.xml").write_text(manifest, encoding="utf-8")
        render_logos(package / "StoreAssets")
        output.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([makeappx, "pack", "/d", str(package), "/p", str(output), "/o"], check=True)
    print(output)


if __name__ == "__main__":
    main()
