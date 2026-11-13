from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame, QGridLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from agenda.database import Database
from agenda.services.similarity import compare_programs
from agenda.startup import disable_startup, enable_startup, startup_enabled
from agenda.ui.dialogs import ContestDialog, NameDialog, TopicDialog
from agenda.ui.styles import APP_STYLE
from agenda.ui.widget import DesktopWidget


class MainWindow(QMainWindow):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.desktop_widget = DesktopWidget(database)
        self.setWindowTitle("Agenda de Concursos")
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._refresh_all()
        if self.database.get_setting("widget_auto_show", "0") == "1":
            self.show_desktop_widget()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(225)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(17, 24, 17, 18)
        side.setSpacing(9)

        brand = QLabel("◈  Agenda")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        brand_sub = QLabel("ORGANIZE SEUS PRÓXIMOS PASSOS")
        brand_sub.setObjectName("BrandSub")
        side.addWidget(brand_sub)
        side.addSpacing(22)

        self.nav_buttons: dict[str, QPushButton] = {}
        nav_items = [
            ("dashboard", "⌂   Visão geral"),
            ("contests", "▤   Concursos"),
            ("content", "☷   Conteúdo programático"),
            ("compare", "⇄   Comparar conteúdos"),
            ("settings", "⚙   Configurações"),
        ]
        for key, label in nav_items:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False, page=key: self.show_page(page))
            side.addWidget(button)
            self.nav_buttons[key] = button
        side.addStretch()
        version = QLabel("AGENDA DE CONCURSOS\nVersão 0.1.0 · Dados locais")
        version.setObjectName("BrandSub")
        version.setWordWrap(True)
        side.addWidget(version)
        outer.addWidget(side)

        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(30, 24, 30, 24)
        main_layout.setSpacing(18)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        self.page_title = QLabel("Visão geral")
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel("Acompanhe seus objetivos e organize sua preparação.")
        self.page_subtitle.setObjectName("PageSubtitle")
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        header.addLayout(titles)
        header.addStretch()
        widget_button = QPushButton("▣  Mostrar widget")
        widget_button.clicked.connect(self.show_desktop_widget)
        header.addWidget(widget_button)
        new_button = QPushButton("+  Novo concurso")
        new_button.setObjectName("PrimaryButton")
        new_button.clicked.connect(self._add_contest)
        header.addWidget(new_button)
        main_layout.addLayout(header)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        outer.addWidget(main, 1)

        self.pages: dict[str, QWidget] = {}
        self.pages["dashboard"] = self._build_dashboard_page()
        self.pages["contests"] = self._build_contests_page()
        self.pages["content"] = self._build_content_page()
        self.pages["compare"] = self._build_compare_page()
        self.pages["settings"] = self._build_settings_page()
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.show_page("dashboard")

    def _panel(self, title: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("Panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(17, 15, 17, 16)
        layout.setSpacing(11)
        if title:
            label = QLabel(title)
            label.setStyleSheet("font-size:12pt; font-weight:700; color:#24344B;")
            layout.addWidget(label)
        return frame, layout

    def _metric_card(self, caption: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setObjectName("MetricCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 13, 16, 13)
        value = QLabel("0")
        value.setObjectName("MetricValue")
        label = QLabel(caption)
        label.setObjectName("MetricCaption")
        layout.addWidget(value)
        layout.addWidget(label)
        return frame, value

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.metric_total_card, self.metric_total = self._metric_card("Concursos cadastrados")
        self.metric_edital_card, self.metric_edital = self._metric_card("Editais publicados")
        self.metric_predicted_card, self.metric_predicted = self._metric_card("Concursos previstos")
        self.metric_no_date_card, self.metric_no_date = self._metric_card("Sem previsão")
        for column, card in enumerate((
            self.metric_total_card, self.metric_edital_card,
            self.metric_predicted_card, self.metric_no_date_card,
        )):
            metrics.addWidget(card, 0, column)
        layout.addLayout(metrics)

        panel, panel_layout = self._panel("Agenda de datas")
        subtitle = QLabel("Provas e previsões cadastradas, em ordem cronológica.")
        subtitle.setStyleSheet("color:#7A8799; font-size:9pt;")
        panel_layout.addWidget(subtitle)
        self.dashboard_list = QListWidget()
        self.dashboard_list.setAlternatingRowColors(True)
        self.dashboard_list.setMinimumHeight(260)
        panel_layout.addWidget(self.dashboard_list)
        layout.addWidget(panel, 1)

        actions = QHBoxLayout()
        hint = QLabel("Dica: cadastre primeiro seus concursos de interesse. Você pode completar as datas depois.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#7A8799; font-size:9pt;")
        actions.addWidget(hint, 1)
        add = QPushButton("+ Cadastrar concurso")
        add.setObjectName("PrimaryButton")
        add.clicked.connect(self._add_contest)
        actions.addWidget(add)
        layout.addLayout(actions)
        return page

    def _build_contests_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.contest_search = QLineEdit()
        self.contest_search.setPlaceholderText("Buscar por concurso, órgão, cargo ou banca...")
        self.contest_search.textChanged.connect(self._refresh_contest_table)
        toolbar.addWidget(self.contest_search, 1)
        add = QPushButton("+ Novo concurso")
        add.setObjectName("PrimaryButton")
        add.clicked.connect(self._add_contest)
        toolbar.addWidget(add)
        layout.addLayout(toolbar)

        panel, panel_layout = self._panel()
        self.contest_table = QTableWidget(0, 6)
        self.contest_table.setHorizontalHeaderLabels(
            ["Concurso / seleção", "Órgão", "Cargo", "Situação", "Data principal", "Banca"]
        )
        self.contest_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contest_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.contest_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.contest_table.setAlternatingRowColors(True)
        self.contest_table.verticalHeader().setVisible(False)
        self.contest_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for index in (1, 2, 3, 4, 5):
            self.contest_table.horizontalHeader().setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
        self.contest_table.doubleClicked.connect(self._edit_contest)
        panel_layout.addWidget(self.contest_table)
        layout.addWidget(panel, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        edit = QPushButton("Editar ficha")
        edit.clicked.connect(self._edit_contest)
        delete = QPushButton("Excluir")
        delete.setObjectName("DangerButton")
        delete.clicked.connect(self._delete_contest)
        buttons.addWidget(edit)
        buttons.addWidget(delete)
        layout.addLayout(buttons)
        return page

    def _build_content_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        selector = QHBoxLayout()
        selector.addWidget(QLabel("Concurso:"))
        self.content_contest_combo = QComboBox()
        self.content_contest_combo.currentIndexChanged.connect(self._load_content)
        selector.addWidget(self.content_contest_combo, 1)
        layout.addLayout(selector)

        columns = QHBoxLayout()
        disciplines_panel, disciplines_layout = self._panel("Disciplinas")
        self.discipline_list = QListWidget()
        self.discipline_list.currentItemChanged.connect(self._load_topics)
        disciplines_layout.addWidget(self.discipline_list, 1)
        discipline_buttons = QHBoxLayout()
        add_discipline = QPushButton("+ Disciplina")
        add_discipline.setObjectName("PrimaryButton")
        add_discipline.clicked.connect(self._add_discipline)
        remove_discipline = QPushButton("Remover")
        remove_discipline.setObjectName("DangerButton")
        remove_discipline.clicked.connect(self._delete_discipline)
        discipline_buttons.addWidget(add_discipline)
        discipline_buttons.addWidget(remove_discipline)
        disciplines_layout.addLayout(discipline_buttons)
        columns.addWidget(disciplines_panel, 1)

        topics_panel, topics_layout = self._panel("Tópicos programáticos")
        topic_help = QLabel("Cadastre cada assunto separadamente. O nome padronizado ajuda a comparar editais.")
        topic_help.setWordWrap(True)
        topic_help.setStyleSheet("color:#78869A; font-size:8pt;")
        topics_layout.addWidget(topic_help)
        self.topic_list = QListWidget()
        self.topic_list.itemDoubleClicked.connect(self._edit_topic)
        topics_layout.addWidget(self.topic_list, 1)
        topic_buttons = QHBoxLayout()
        add_topic = QPushButton("+ Tópico")
        add_topic.setObjectName("PrimaryButton")
        add_topic.clicked.connect(self._add_topic)
        edit_topic = QPushButton("Editar")
        edit_topic.clicked.connect(self._edit_topic)
        delete_topic = QPushButton("Excluir")
        delete_topic.setObjectName("DangerButton")
        delete_topic.clicked.connect(self._delete_topic)
        topic_buttons.addWidget(add_topic)
        topic_buttons.addWidget(edit_topic)
        topic_buttons.addWidget(delete_topic)
        topics_layout.addLayout(topic_buttons)
        columns.addWidget(topics_panel, 1)
        layout.addLayout(columns, 1)
        return page

    def _build_compare_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        panel, panel_layout = self._panel("Selecione os concursos")
        selectors = QHBoxLayout()
        self.compare_a = QComboBox()
        self.compare_b = QComboBox()
        selectors.addWidget(QLabel("Concurso A"))
        selectors.addWidget(self.compare_a, 1)
        selectors.addWidget(QLabel("Concurso B"))
        selectors.addWidget(self.compare_b, 1)
        run = QPushButton("⇄  Comparar conteúdos")
        run.setObjectName("PrimaryButton")
        run.clicked.connect(self._run_comparison)
        selectors.addWidget(run)
        panel_layout.addLayout(selectors)
        layout.addWidget(panel)

        summary_panel, summary_layout = self._panel("Resultado da comparação")
        self.compare_score = QLabel("Selecione dois concursos e inicie a comparação.")
        self.compare_score.setStyleSheet("font-size:17pt; font-weight:700; color:#2864C5;")
        summary_layout.addWidget(self.compare_score)
        self.compare_detail = QLabel(
            "Estimativa textual baseada nos tópicos cadastrados. Revise os pares sugeridos antes de tomar decisões de estudo."
        )
        self.compare_detail.setWordWrap(True)
        self.compare_detail.setStyleSheet("color:#6F7E93;")
        summary_layout.addWidget(self.compare_detail)
        self.compare_tree = QTreeWidget()
        self.compare_tree.setHeaderLabels(["Disciplina / tópico", "Correspondência", "Observação"])
        self.compare_tree.setColumnWidth(0, 440)
        summary_layout.addWidget(self.compare_tree, 1)
        layout.addWidget(summary_panel, 1)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        general, general_layout = self._panel("Preferências")
        self.startup_check = QCheckBox("Iniciar automaticamente quando eu entrar no Windows")
        self.startup_check.setChecked(startup_enabled())
        self.auto_widget_check = QCheckBox("Mostrar o widget automaticamente ao abrir o aplicativo")
        self.auto_widget_check.setChecked(self.database.get_setting("widget_auto_show", "0") == "1")
        general_layout.addWidget(self.startup_check)
        general_layout.addWidget(self.auto_widget_check)
        row = QHBoxLayout()
        row.addWidget(QLabel("Quantidade de concursos no widget:"))
        self.widget_count = QSpinBox()
        self.widget_count.setRange(1, 20)
        self.widget_count.setValue(max(1, min(20, int(self.database.get_setting("widget_items", "5") or 5))))
        row.addWidget(self.widget_count)
        row.addStretch()
        general_layout.addLayout(row)
        save = QPushButton("Salvar preferências")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._save_settings)
        general_layout.addWidget(save)
        layout.addWidget(general)

        backup, backup_layout = self._panel("Backup e portabilidade")
        explanation = QLabel(
            "Exporte suas fichas, disciplinas, tópicos e preferências para um arquivo JSON. "
            "A importação substitui os dados atuais; faça uma cópia antes de restaurar."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color:#718096;")
        backup_layout.addWidget(explanation)
        actions = QHBoxLayout()
        export_button = QPushButton("Exportar backup JSON")
        export_button.clicked.connect(self._export_backup)
        import_button = QPushButton("Importar backup JSON")
        import_button.clicked.connect(self._import_backup)
        actions.addWidget(export_button)
        actions.addWidget(import_button)
        actions.addStretch()
        backup_layout.addLayout(actions)
        layout.addWidget(backup)
        layout.addStretch()
        return page

    def show_page(self, key: str) -> None:
        labels = {
            "dashboard": ("Visão geral", "Acompanhe seus objetivos e organize sua preparação."),
            "contests": ("Concursos", "Mantenha uma ficha para cada oportunidade de interesse."),
            "content": ("Conteúdo programático", "Estruture disciplinas e tópicos de cada concurso."),
            "compare": ("Comparar conteúdos", "Descubra quais assuntos se repetem entre diferentes seleções."),
            "settings": ("Configurações", "Ajuste a inicialização, o widget e seus backups locais."),
        }
        if key not in self.pages:
            return
        self.stack.setCurrentWidget(self.pages[key])
        self.page_title.setText(labels[key][0])
        self.page_subtitle.setText(labels[key][1])
        for nav_key, button in self.nav_buttons.items():
            button.setChecked(nav_key == key)
        if key == "dashboard":
            self._refresh_dashboard()
        elif key == "contests":
            self._refresh_contest_table()
        elif key == "content":
            self._refresh_contest_combos(self.content_contest_combo)
            self._load_content()
        elif key == "compare":
            self._refresh_contest_combos(self.compare_a)
            self._refresh_contest_combos(self.compare_b)

    def show_desktop_widget(self) -> None:
        self.desktop_widget.refresh()
        self.desktop_widget.show()
        self.desktop_widget.raise_()
        self.desktop_widget.activateWindow()

    def _refresh_all(self) -> None:
        self._refresh_contest_table()
        self._refresh_contest_combos(self.content_contest_combo)
        self._refresh_contest_combos(self.compare_a)
        self._refresh_contest_combos(self.compare_b)
        self._refresh_dashboard()
        self.desktop_widget.refresh()

    def _refresh_dashboard(self) -> None:
        contests = self.database.list_contests()
        self.metric_total.setText(str(len(contests)))
        self.metric_edital.setText(str(sum(item.get("status") == "Edital publicado" for item in contests)))
        self.metric_predicted.setText(str(sum(item.get("status") == "Previsto" for item in contests)))
        self.metric_no_date.setText(str(sum(item.get("status") == "Sem Previsão" for item in contests)))
        self.dashboard_list.clear()
        today = date.today().isoformat()
        dated = []
        for item in contests:
            event_date = item.get("data_prova") or item.get("data_prevista")
            if event_date and event_date >= today:
                dated.append((event_date, item))
        for event_date, item in sorted(dated)[:12]:
            label = f"{event_date}   •   {item.get('nome', '')}   •   {item.get('status', '')}"
            row = QListWidgetItem(label)
            row.setData(Qt.ItemDataRole.UserRole, item["id"])
            self.dashboard_list.addItem(row)
        if not dated:
            self.dashboard_list.addItem("Nenhuma prova ou previsão futura cadastrada. Adicione datas às suas fichas.")

    def _refresh_contest_table(self) -> None:
        if not hasattr(self, "contest_table"):
            return
        rows = self.database.list_contests(self.contest_search.text() if hasattr(self, "contest_search") else "")
        self.contest_table.setRowCount(0)
        for contest in rows:
            row_index = self.contest_table.rowCount()
            self.contest_table.insertRow(row_index)
            event_date = contest.get("data_prova") or contest.get("data_prevista") or "—"
            values = [
                contest.get("nome", ""),
                contest.get("orgao", ""),
                contest.get("cargo", ""),
                contest.get("status", ""),
                event_date,
                contest.get("banca", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value or "—"))
                item.setData(Qt.ItemDataRole.UserRole, contest["id"])
                if column == 3:
                    colors = {
                        "Sem Previsão": ("#EEF1F5", "#526174"),
                        "Previsto": ("#FFF2D9", "#9A5B00"),
                        "Edital publicado": ("#E2F5EC", "#176B4B"),
                    }
                    background, foreground = colors.get(str(value), ("#EEF1F5", "#526174"))
                    item.setBackground(QColor(background))
                    item.setForeground(QColor(foreground))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.contest_table.setItem(row_index, column, item)

    def _refresh_contest_combos(self, combo: QComboBox) -> None:
        if combo is None:
            return
        current = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for contest in self.database.list_contests():
            combo.addItem(contest.get("nome", "Concurso"), contest["id"])
        if current is not None:
            index = combo.findData(current)
            if index >= 0:
                combo.setCurrentIndex(index)
        combo.blockSignals(False)

    def _selected_contest_id(self) -> int | None:
        row = self.contest_table.currentRow()
        if row < 0:
            return None
        item = self.contest_table.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _add_contest(self) -> None:
        dialog = ContestDialog(self)
        if dialog.exec():
            try:
                self.database.save_contest(dialog.values())
                self._refresh_all()
            except Exception as error:
                QMessageBox.critical(self, "Não foi possível salvar", str(error))

    def _edit_contest(self) -> None:
        contest_id = self._selected_contest_id()
        if contest_id is None:
            QMessageBox.information(self, "Selecione um concurso", "Escolha uma ficha na tabela para editar.")
            return
        data = self.database.get_contest(contest_id)
        if data is None:
            return
        dialog = ContestDialog(self, data)
        if dialog.exec():
            try:
                self.database.save_contest(dialog.values(), contest_id)
                self._refresh_all()
            except Exception as error:
                QMessageBox.critical(self, "Não foi possível salvar", str(error))

    def _delete_contest(self) -> None:
        contest_id = self._selected_contest_id()
        if contest_id is None:
            QMessageBox.information(self, "Selecione um concurso", "Escolha uma ficha na tabela.")
            return
        answer = QMessageBox.question(
            self, "Excluir concurso",
            "Excluir esta ficha e todas as suas disciplinas e tópicos? Esta ação não pode ser desfeita."
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_contest(contest_id)
            self._refresh_all()

    def _load_content(self, *_args) -> None:
        if not hasattr(self, "discipline_list"):
            return
        self.discipline_list.clear()
        self.topic_list.clear()
        contest_id = self.content_contest_combo.currentData()
        if contest_id is None:
            return
        for discipline in self.database.list_disciplines(int(contest_id)):
            item = QListWidgetItem(discipline["nome"])
            item.setData(Qt.ItemDataRole.UserRole, discipline["id"])
            self.discipline_list.addItem(item)
        if self.discipline_list.count():
            self.discipline_list.setCurrentRow(0)

    def _selected_discipline_id(self) -> int | None:
        item = self.discipline_list.currentItem()
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _selected_topic_id(self) -> int | None:
        item = self.topic_list.currentItem()
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _load_topics(self, current=None, _previous=None) -> None:
        if not hasattr(self, "topic_list"):
            return
        self.topic_list.clear()
        if current is None:
            current = self.discipline_list.currentItem()
        if current is None:
            return
        discipline_id = int(current.data(Qt.ItemDataRole.UserRole))
        for topic in self.database.list_topics(discipline_id):
            label = topic["nome"]
            if topic.get("nome_padronizado"):
                label += f"   ·   ↳ {topic['nome_padronizado']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, topic["id"])
            item.setToolTip("Nome padronizado: " + (topic.get("nome_padronizado") or "não definido"))
            self.topic_list.addItem(item)

    def _add_discipline(self) -> None:
        contest_id = self.content_contest_combo.currentData()
        if contest_id is None:
            QMessageBox.information(self, "Nenhum concurso", "Cadastre ou selecione um concurso primeiro.")
            return
        dialog = NameDialog("Nova disciplina", "Nome da disciplina:", self)
        if dialog.exec() and dialog.value():
            self.database.add_discipline(int(contest_id), dialog.value())
            self._load_content()

    def _delete_discipline(self) -> None:
        discipline_id = self._selected_discipline_id()
        if discipline_id is None:
            QMessageBox.information(self, "Selecione uma disciplina", "Escolha uma disciplina para remover.")
            return
        answer = QMessageBox.question(
            self, "Remover disciplina",
            "Remover a disciplina e todos os seus tópicos?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_discipline(discipline_id)
            self._load_content()

    def _add_topic(self) -> None:
        discipline_id = self._selected_discipline_id()
        if discipline_id is None:
            QMessageBox.information(self, "Selecione uma disciplina", "Escolha a disciplina do tópico.")
            return
        dialog = TopicDialog(self)
        if dialog.exec():
            name, canonical = dialog.values()
            self.database.add_topic(discipline_id, name, canonical)
            self._load_topics()

    def _edit_topic(self, *_args) -> None:
        topic_id = self._selected_topic_id()
        if topic_id is None:
            QMessageBox.information(self, "Selecione um tópico", "Escolha o tópico que deseja editar.")
            return
        discipline_id = self._selected_discipline_id()
        topics = self.database.list_topics(discipline_id) if discipline_id else []
        topic = next((entry for entry in topics if entry["id"] == topic_id), None)
        if not topic:
            return
        dialog = TopicDialog(self, "Editar tópico", topic["nome"], topic.get("nome_padronizado", ""))
        if dialog.exec():
            name, canonical = dialog.values()
            self.database.update_topic(topic_id, name, canonical)
            self._load_topics()

    def _delete_topic(self) -> None:
        topic_id = self._selected_topic_id()
        if topic_id is None:
            QMessageBox.information(self, "Selecione um tópico", "Escolha um tópico para remover.")
            return
        answer = QMessageBox.question(self, "Excluir tópico", "Deseja excluir o tópico selecionado?")
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_topic(topic_id)
            self._load_topics()

    def _run_comparison(self) -> None:
        id_a, id_b = self.compare_a.currentData(), self.compare_b.currentData()
        if id_a is None or id_b is None:
            QMessageBox.information(self, "Cadastre concursos", "Cadastre pelo menos dois concursos.")
            return
        if id_a == id_b:
            QMessageBox.information(self, "Seleção inválida", "Escolha dois concursos diferentes.")
            return
        result = compare_programs(
            self.database.get_program(int(id_a)),
            self.database.get_program(int(id_b)),
        )
        self.compare_score.setText(f"Similaridade estimada: {result['percentual']:.1f}%")
        self.compare_detail.setText(
            f"{result['disciplinas_comparadas']} disciplinas associadas · "
            f"{result['topicos_correspondentes']} tópicos correspondentes · "
            f"{result['topicos_exclusivos_a']} exclusivos do concurso A · "
            f"{result['topicos_exclusivos_b']} exclusivos do concurso B. "
            "Revise os pares sugeridos: trata-se de uma estimativa textual."
        )
        self.compare_detail.setToolTip(result["metodologia"])
        self.compare_tree.clear()
        for discipline in result["disciplinas"]:
            name_a = discipline.get("disciplina_a") or "—"
            name_b = discipline.get("disciplina_b") or "—"
            root = QTreeWidgetItem([
                f"{name_a}  ⇄  {name_b}",
                f"{discipline['similaridade']:.1f}%",
                "Disciplina correspondente" if discipline["similaridade"] else "Sem correspondência",
            ])
            self.compare_tree.addTopLevelItem(root)
            detail = discipline["topicos"]
            for match in detail["matches"]:
                suffix = " · padronizado" if match["padronizado"] else ""
                child = QTreeWidgetItem([
                    f"{match['topico_a']}  ⇄  {match['topico_b']}",
                    f"{match['similaridade']:.1f}%",
                    "Correspondência textual" + suffix,
                ])
                root.addChild(child)
            for text in detail["somente_a"]:
                root.addChild(QTreeWidgetItem([text, "—", "Somente no concurso A"]))
            for text in detail["somente_b"]:
                root.addChild(QTreeWidgetItem([text, "—", "Somente no concurso B"]))
            root.setExpanded(True)

    def _save_settings(self) -> None:
        try:
            if self.startup_check.isChecked():
                enable_startup()
                self.database.set_setting("startup_enabled", "1")
            else:
                if startup_enabled():
                    disable_startup()
                self.database.set_setting("startup_enabled", "0")
        except Exception as error:
            QMessageBox.warning(self, "Inicialização do Windows", str(error))
            return
        count = self.widget_count.value()
        self.database.set_setting("widget_items", str(count))
        self.database.set_setting("widget_auto_show", "1" if self.auto_widget_check.isChecked() else "0")
        self.desktop_widget.set_item_limit(count)
        QMessageBox.information(self, "Preferências salvas", "As configurações foram atualizadas.")

    def _export_backup(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar backup", "agenda-de-concursos-backup.json", "Arquivo JSON (*.json)"
        )
        if not path:
            return
        try:
            self.database.export_json(Path(path))
            QMessageBox.information(self, "Backup exportado", "O backup foi salvo com sucesso.")
        except Exception as error:
            QMessageBox.critical(self, "Falha no backup", str(error))

    def _import_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importar backup", "", "Arquivo JSON (*.json)")
        if not path:
            return
        answer = QMessageBox.warning(
            self, "Substituir dados atuais",
            "A importação substituirá todas as fichas e conteúdos atualmente cadastrados. "
            "Recomenda-se exportar um backup antes de continuar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.import_json(Path(path))
            self._refresh_all()
            QMessageBox.information(self, "Backup importado", "Os dados foram restaurados.")
        except Exception as error:
            QMessageBox.critical(self, "Falha na importação", str(error))

    def closeEvent(self, event) -> None:
        self.desktop_widget.hide()
        event.accept()
