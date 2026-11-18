from __future__ import annotations

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QPushButton

from agenda.database import Database
from agenda.ui.cards import ContestCard
from agenda.ui.cargo_dialogs import CargoManagerDialog
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
            "url_edital": "[Edital](<https://example.org/edital.pdf>)",
            "url_oficial": "Site oficial: //example.org/\n concursos",
            "observacoes": notes,
        })
        database.replace_cargos(contest_id, [{
            "nome": "Médico",
            "nivel_escolaridade": "Superior",
            "requisitos": "Graduação em Medicina e CRM",
            "salario_inicial": "R$ 12.000,00",
            "salario_final": "R$ 14.000,00",
            "jornada": "20 horas semanais",
        }, {"nome": "Enfermeiro", "salario_inicial": "R$ 8.000,00"}])
        manager = CargoManagerDialog(database.list_cargos(contest_id))
        manager.interest_button.click()
        assert "De interesse" in manager.list_widget.item(0).text()
        assert "De interesse" not in manager.list_widget.item(1).text()
        database.replace_cargos(contest_id, manager.cargos())
        manager.close()
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
        with (
            patch.object(window, "tray_icon", Mock()),
            patch("agenda.ui.main_window.sys.platform", "win32"),
            patch("agenda.ui.main_window.enable_startup") as enable_startup,
        ):
            window.launch()
            enable_startup.assert_called_once()
            assert not window.isVisible() and window.desktop_widget.isVisible()
            database.set_setting("startup_enabled", "0")
            enable_startup.reset_mock()
            window.launch()
            enable_startup.assert_not_called()
        window._restore_main_window()
        app.processEvents()
        assert window.isVisible()
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
        assert detail._normalized_url("Disponível no site oficial") is None
        assert detail._normalized_url("file:///C:/edital.pdf") is None
        with patch("agenda.ui.details_dialog.QDesktopServices.openUrl", return_value=True) as open_url:
            for title in ("Abrir edital", "Abrir site oficial"):
                next(button for button in detail.findChildren(QPushButton) if button.text() == title).click()
        assert [call.args[0].toString() for call in open_url.call_args_list] == [
            "https://example.org/edital.pdf", "https://example.org/concursos",
        ]
        interest = detail.findChild(QLabel, "CargoInterest")
        assert interest is not None and "Cargo de interesse" in interest.text()
        notes_label = next(label for label in detail.findChildren(QLabel) if label.text() == notes)
        assert notes_label.textFormat() == Qt.TextFormat.PlainText
        assert "Médico" in build_extraction_prompt(database.get_user_profile())
        assert window.profile_level_checks["Superior"].isChecked()
        assert window.profile_level_checks["Superior"].text().startswith("✓")
        fundamental = window.profile_level_checks["Fundamental"]
        fundamental.click()
        assert fundamental.isChecked() and fundamental.text().startswith("✓")
        fundamental.click()
        assert not fundamental.isChecked() and fundamental.text() == "Fundamental"
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
        compact = widget.cards_layout.itemAt(0).widget()
        dates = compact.findChildren(QLabel, "ContestCardMeta")
        assert [label.text().split(":")[0] for label in dates] == [
            "Início das inscrições", "Fim das inscrições", "Data da prova",
        ]
        roles = compact.findChildren(QLabel, "ContestCardInterest")
        assert [label.text() for label in roles] == ["Médico · R$ 12.000,00 a R$ 14.000,00"]
        assert widget.cards_scroll.verticalScrollBar().maximum() == 0
        assert widget.count_label.text(), "O rodapé do widget deve informar a quantidade exibida."
        assert not widget.findChildren(QPushButton), "O widget não deve ter botão interno para ocultá-lo."
        assert "border-radius:16px" in widget.styleSheet()
        for index in range(12):
            database.save_cargo(contest_id, {"nome": f"Cargo de teste {index}", "interesse": True})
        widget.set_dimensions(320, 300)
        app.processEvents()
        assert widget.cards_scroll.verticalScrollBar().maximum() > 0
        assert not widget.cards_scroll.horizontalScrollBar().isVisible()
        compact = widget.cards_layout.itemAt(0).widget()
        roles = compact.findChildren(QLabel, "ContestCardInterest")
        assert len(roles) == 13
        widget.cards_scroll.ensureWidgetVisible(roles[-1])
        assert widget.cards_scroll.verticalScrollBar().value() > 0

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
