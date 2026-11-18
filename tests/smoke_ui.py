from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton, QScrollBar

from agenda.database import Database
from agenda.ui.cards import ContestCard
from agenda.ui.details_dialog import ContestDetailsDialog
from agenda.ui.main_window import MainWindow
from agenda.services.prompts import build_extraction_prompt


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        database = Database(Path(directory) / "smoke.db")
        exam_date = date.today() + timedelta(days=30)
        notes = "- Fonte: https://example.org/edital\n\n<b>Texto do edital</b>"
        contest_id = database.save_contest({
            "nome": "Concurso de validação da interface",
            "orgao": "Órgão de teste",
            "cargo": "Analista",
            "banca": "Banca de teste",
            "status": "Previsto",
            "inscricoes_inicio": (exam_date - timedelta(days=20)).isoformat(),
            "inscricoes_fim": (exam_date - timedelta(days=7)).isoformat(),
            "data_prova": exam_date.isoformat(),
            "localidade": "Brasil",
            "url_edital": "https://example.org/edital",
            "observacoes": notes,
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
        database.set_setting("widget_width", "valor inválido")

        window = MainWindow(database)
        window.show()
        app.processEvents()
        assert window.widget_width.value() == 390

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
        notes_label = next(label for label in detail.findChildren(QLabel) if label.text() == notes)
        assert notes_label.textFormat() == Qt.TextFormat.PlainText
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
        assert not widget.findChildren(QPushButton), "O widget não deve ter botão interno para ocultá-lo."
        assert "border-radius:16px" in widget.styleSheet()

        widget.hide()
        window._update_widget_actions()
        assert window.widget_action.text() == "Mostrar widget"
        window._toggle_desktop_widget()
        assert widget.isVisible()
        window._toggle_desktop_widget()
        assert not widget.isVisible()

        window.show_page("contests")
        window.contest_search.setText("medico")
        assert window.contest_table.rowCount() == 1
        window.contest_table.selectRow(0)
        with patch.object(window, "_open_contest_details") as open_details:
            window.contest_table.itemActivated.emit(window.contest_table.item(0, 0))
            open_details.assert_called_once_with(contest_id)
        with patch.object(window, "_open_prompts"):
            window.nav_buttons["prompts"].click()
            assert window.nav_buttons["contests"].isChecked()
            assert not window.nav_buttons["prompts"].isChecked()

        other_id = database.save_contest({"nome": "Concurso sem conteúdo " + "Longo " * 30})
        window._refresh_all()
        assert window.compare_a.currentData() == contest_id
        assert window.compare_b.currentData() == other_id
        window._run_comparison()
        assert "Conteúdo insuficiente" in window.compare_score.text()
        other_discipline_id = database.add_discipline(other_id, "Direito Constitucional")
        database.add_topic(other_discipline_id, "Direitos fundamentais")
        window._run_comparison()
        assert "100.0%" in window.compare_score.text()
        window.compare_b.setCurrentIndex(0)
        assert window.compare_tree.topLevelItemCount() == 0

        backup_db = Database(Path(directory) / "backup.db")
        backup_db.save_contest({"nome": "Concurso restaurado"})
        backup_db.save_user_profile({"niveis_escolaridade": ["Médio/Técnico"], "cargos_desejados": ["Técnico"]})
        backup_db.set_setting("theme", "escuro")
        backup_db.set_setting("widget_items", "2")
        backup_db.set_setting("widget_width", "480")
        backup_db.set_setting("widget_height", "invalid")
        backup_path = Path(directory) / "backup.json"
        backup_db.export_json(backup_path)
        with (
            patch("agenda.ui.main_window.QFileDialog.getOpenFileName", return_value=(str(backup_path), "")),
            patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Yes),
            patch.object(QMessageBox, "information") as success,
            patch.object(QMessageBox, "critical") as error,
        ):
            window._import_backup()
            error.assert_not_called()
            success.assert_called_once()
        assert window.theme == "escuro" and window.theme_combo.currentData() == "escuro"
        assert window.profile_level_checks["Médio/Técnico"].isChecked()
        assert window.profile_roles_edit.toPlainText() == "Técnico"
        assert widget.width() == window.widget_width.value() == 480
        assert widget.height() == window.widget_height.value() == 470
        assert widget.item_limit == window.widget_count.value() == 2

        window.close()
        app.processEvents()
    app.quit()


if __name__ == "__main__":
    main()
