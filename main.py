from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from agenda.database import Database
from agenda.paths import app_data_dir
from agenda.ui.assets import asset_path
from agenda.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Agenda de Concursos")
    app.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
    app.setOrganizationName("AgendaDeConcursos")
    app.setStyle("Fusion")

    data_dir = app_data_dir()
    database = Database(data_dir / "agenda.db")

    window = MainWindow(database)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
