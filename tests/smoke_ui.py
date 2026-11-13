from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QScrollBar

from agenda.database import Database
from agenda.ui.cards import ContestCard
from agenda.ui.details_dialog import ContestDetailsDialog
from agenda.ui.main_window import MainWindow


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "smoke.db")
        contest_id = database.save_contest({
            "nome": "Concurso de validação da interface",
            "orgao": "Órgão de teste",
            "cargo": "Analista",
            "banca": "Banca de teste",
            "status": "Previsto",
            "inscricoes_inicio": "2027-01-10",
            "inscricoes_fim": "2027-01-30",
            "data_prova": "2027-03-15",
            "localidade": "Brasil",
            "url_edital": "https://example.org/edital",
        })
        discipline_id = database.add_discipline(contest_id, "Direito Constitucional")
        database.add_topic(
            discipline_id,
            "Direitos fundamentais",
            "Direitos fundamentais",
        )

        window = MainWindow(database)
        window.show()
        app.processEvents()

        dashboard_cards = [
            item.widget()
            for index in range(window.dashboard_cards_layout.count())
            if isinstance((item := window.dashboard_cards_layout.itemAt(index)).widget(), ContestCard)
        ]
        assert len(dashboard_cards) == 1, "A Agenda de datas deve renderizar um card por concurso."
        assert dashboard_cards[0].contest_id == contest_id

        detail = ContestDetailsDialog(
            database.get_contest(contest_id),
            database.get_program(contest_id),
            window,
        )
        assert detail.windowTitle().startswith("Ficha completa")
        detail.show()
        app.processEvents()
        detail.close()

        widget = window.desktop_widget
        widget.set_item_limit(10)
        widget.set_dimensions(420, 520)
        widget.show()
        app.processEvents()
        assert widget.size().width() == 420 and widget.size().height() == 520
        assert widget.cards_layout.count() == 1, "O widget deve exibir o concurso em um card."
        assert not widget.findChildren(QScrollBar), "O widget não deve conter barras de rolagem."
        assert widget.count_label.text(), "O rodapé do widget deve informar a quantidade exibida."

        window.close()
        app.processEvents()
    app.quit()


if __name__ == "__main__":
    main()
