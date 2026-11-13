from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication, QPushButton, QScrollBar

from agenda.database import Database
from agenda.ui.cards import ContestCard
from agenda.ui.details_dialog import ContestDetailsDialog
from agenda.ui.main_window import MainWindow
from agenda.services.prompts import build_extraction_prompt


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
        database.replace_cargos(contest_id, [{
            "nome": "Médico",
            "nivel_escolaridade": "Superior",
            "requisitos": "Graduação em Medicina e CRM",
            "salario_inicial": "R$ 12.000,00",
            "jornada": "20 horas semanais",
        }])
        database.save_user_profile({
            "niveis_escolaridade": ["Superior"],
            "cargos_desejados": ["Médico"],
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
            database=database,
        )
        assert detail.windowTitle().startswith("Ficha completa")
        assert detail.cargos and detail.cargos[0]["nome"] == "Médico"
        assert detail._normalized_url("www.example.org/edital").scheme() == "https"
        assert "Médico" in build_extraction_prompt(database.get_user_profile())
        assert window.profile_level_checks["Superior"].isChecked()
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
        assert not widget.findChildren(QScrollBar), "O widget não deve conter barras de rolagem."
        assert not widget.findChildren(QPushButton), "O widget não deve ter botão interno para ocultá-lo."
        assert "border-radius:16px" in widget.styleSheet()

        widget.hide()
        window._update_widget_actions()
        assert window.widget_action.text() == "Mostrar widget"
        window._toggle_desktop_widget()
        assert widget.isVisible()
        window._toggle_desktop_widget()
        assert not widget.isVisible()

        window.close()
        app.processEvents()
    app.quit()


if __name__ == "__main__":
    main()
