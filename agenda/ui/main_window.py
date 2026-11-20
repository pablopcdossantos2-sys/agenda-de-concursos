from __future__ import annotations

import sys
from datetime import date
from html import escape
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QSignalBlocker, QSize, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QSpinBox, QStackedWidget, QStyle, QSystemTrayIcon,
    QTableWidget, QTableWidgetItem, QToolBar, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)

from agenda.database import Database
from agenda.services.dates import format_date_pt_br
from agenda.services.profile import EDUCATION_LEVELS, profile_summary
from agenda.services.similarity import compare_programs
from agenda.ui.assets import asset_path
from agenda.ui.cards import ContestCard
from agenda.ui.code_dialogs import ContestCodeDialog, PromptPage
from agenda.ui.details_dialog import ContestDetailsDialog
from agenda.ui.dialogs import ContestDialog, NameDialog, TopicDialog
from agenda.ui.styles import DEFAULT_THEME, THEMES, theme_stylesheet
from agenda.ui.widget import DesktopWidget


class MainWindow(QMainWindow):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.theme = database.get_setting("theme", DEFAULT_THEME)
        self.desktop_widget = DesktopWidget(database)
        self.desktop_widget.contest_selected.connect(self._open_contest_details)
        self.desktop_widget.open_agenda_requested.connect(self._restore_main_window)
        self.setWindowTitle("Agenda de Concursos")
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        self.apply_theme(self.theme)
        self._build_toolbar()
        self._build_ui()
        self._setup_tray()
        self._refresh_all()

    def launch(self) -> None:
        if self.database.get_setting("widget_auto_show", "1") == "1":
            self.show_desktop_widget(activate=False)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.show()

    def apply_theme(self, theme: str) -> None:
        self.theme = theme if theme in THEMES else DEFAULT_THEME
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme_stylesheet(self.theme))
        if hasattr(self, "desktop_widget"):
            self.desktop_widget.apply_theme(self.theme)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Barra principal", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(22, 22))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        brand = QAction(QIcon(str(asset_path("app_icon.svg"))), "Agenda de Concursos", self)
        brand.setToolTip("Ícone e identidade visual do Agenda de Concursos")
        brand.triggered.connect(lambda: self.show_page("dashboard"))
        toolbar.addAction(brand)
        toolbar.addSeparator()

        prompts = QAction("Prompts", self)
        prompts.triggered.connect(lambda: self.show_page("prompts"))
        toolbar.addAction(prompts)

        code = QAction("Inserir por JSON", self)
        code.triggered.connect(self._add_contest_from_code)
        toolbar.addAction(code)

        self.widget_action = QAction("Mostrar widget", self)
        self.widget_action.triggered.connect(self._toggle_desktop_widget)
        toolbar.addAction(self.widget_action)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("CentralRoot")
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

        self.nav_buttons: dict[str, QPushButton] = {}
        nav_items = [
            ("dashboard", "⌂   Visão geral"),
            ("contests", "▤   Concursos"),
            ("content", "☷   Conteúdo programático"),
            ("compare", "⇄   Comparar conteúdos"),
            ("prompts", "✦   Prompts"),
            ("profile", "◎   Perfil"),
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
        outer.addWidget(sidebar)

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
        self.page_subtitle.setWordWrap(True)
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        header.addLayout(titles)
        header.addStretch()
        main_layout.addLayout(header)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        outer.addWidget(main, 1)

        self.pages: dict[str, QWidget] = {}
        self.pages["dashboard"] = self._build_dashboard_page()
        self.pages["contests"] = self._build_contests_page()
        self.pages["content"] = self._build_content_page()
        self.pages["compare"] = self._build_compare_page()
        self.prompts_page = PromptPage()
        self.pages["prompts"] = self.prompts_page
        self.pages["profile"] = self._build_profile_page()
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
            label.setObjectName("PanelTitle")
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
        self.dashboard_scroll = QScrollArea()
        self.dashboard_scroll.setWidgetResizable(True)
        self.dashboard_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dashboard_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.dashboard_scroll.setMinimumHeight(260)
        self.dashboard_cards_host = QWidget()
        self.dashboard_cards_host.setObjectName("DashboardCardsHost")
        self.dashboard_cards_layout = QVBoxLayout(self.dashboard_cards_host)
        self.dashboard_cards_layout.setContentsMargins(2, 2, 8, 2)
        self.dashboard_cards_layout.setSpacing(8)
        self.dashboard_cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.dashboard_scroll.setWidget(self.dashboard_cards_host)
        panel_layout.addWidget(self.dashboard_scroll, 1)
        layout.addWidget(panel, 1)

        actions = QHBoxLayout()
        actions.addStretch()
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
        self.contest_search.setAccessibleName("Buscar concursos")
        self.contest_search.setClearButtonEnabled(True)
        self.contest_search.setPlaceholderText("Buscar por concurso, órgão, cargo ou banca...")
        self.contest_search.textChanged.connect(self._refresh_contest_table)
        toolbar.addWidget(self.contest_search, 1)
        add = QPushButton("+ Novo concurso")
        add.setObjectName("PrimaryButton")
        add.clicked.connect(self._add_contest)
        toolbar.addWidget(add)
        add_code = QPushButton("Inserir por código JSON")
        add_code.setToolTip("Cadastrar uma ficha completa colando um objeto JSON validado")
        add_code.clicked.connect(self._add_contest_from_code)
        toolbar.addWidget(add_code)
        layout.addLayout(toolbar)

        panel, panel_layout = self._panel()
        self.contest_table = QTableWidget(0, 6)
        self.contest_table.setHorizontalHeaderLabels(
            ["Concurso / seleção", "Órgão", "Cargo", "Situação", "Data da prova", "Banca"]
        )
        self.contest_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.contest_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.contest_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.contest_table.setAlternatingRowColors(True)
        self.contest_table.verticalHeader().setVisible(False)
        self.contest_table.setWordWrap(False)
        header = self.contest_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for index in (3, 4):
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.Interactive)
        self.contest_table.setColumnWidth(3, 132)
        self.contest_table.setColumnWidth(4, 144)
        self.contest_table.itemActivated.connect(self._show_selected_contest)
        panel_layout.addWidget(self.contest_table)
        layout.addWidget(panel, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()
        view = QPushButton("Ver ficha")
        view.setObjectName("PrimaryButton")
        view.clicked.connect(self._show_selected_contest)
        edit = QPushButton("Editar ficha")
        edit.clicked.connect(self._edit_contest)
        delete = QPushButton("Excluir")
        delete.setObjectName("DangerButton")
        delete.clicked.connect(self._delete_contest)
        for button in (view, edit, delete):
            button.setEnabled(False)
            self.contest_table.itemSelectionChanged.connect(
                lambda control=button: control.setEnabled(self._selected_contest_id() is not None)
            )
            buttons.addWidget(button)
        layout.addLayout(buttons)
        return page

    def _build_content_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        selector = QHBoxLayout()
        selector.addWidget(QLabel("Concurso:"))
        self.content_contest_combo = QComboBox()
        self.content_contest_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
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
        rename_discipline = QPushButton("Renomear")
        rename_discipline.clicked.connect(self._rename_discipline)
        remove_discipline = QPushButton("Remover")
        remove_discipline.setObjectName("DangerButton")
        remove_discipline.clicked.connect(self._delete_discipline)
        discipline_buttons.addWidget(add_discipline)
        discipline_buttons.addWidget(rename_discipline)
        discipline_buttons.addWidget(remove_discipline)
        disciplines_layout.addLayout(discipline_buttons)
        columns.addWidget(disciplines_panel, 1)

        topics_panel, topics_layout = self._panel("Tópicos programáticos")
        topic_help = QLabel("Cadastre cada assunto separadamente. O nome padronizado ajuda a comparar editais.")
        topic_help.setWordWrap(True)
        topic_help.setObjectName("HintText")
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
        for combo in (self.compare_a, self.compare_b):
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setPlaceholderText("Selecione um concurso")
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
        self.compare_score.setObjectName("CompareScore")
        self.compare_score.setWordWrap(True)
        summary_layout.addWidget(self.compare_score)
        self.compare_detail = QLabel(
            "Estimativa textual baseada nos tópicos cadastrados. Revise os pares sugeridos antes de tomar decisões de estudo."
        )
        self.compare_detail.setWordWrap(True)
        self.compare_detail.setObjectName("MutedText")
        summary_layout.addWidget(self.compare_detail)
        self.compare_tree = QTreeWidget()
        self.compare_tree.setHeaderLabels(["Disciplina / tópico", "Correspondência", "Observação"])
        header = self.compare_tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for index in (1, 2):
            header.setSectionResizeMode(index, QHeaderView.ResizeMode.ResizeToContents)
        summary_layout.addWidget(self.compare_tree, 1)
        layout.addWidget(summary_panel, 1)
        self._clear_comparison()
        self.compare_a.currentIndexChanged.connect(self._clear_comparison)
        self.compare_b.currentIndexChanged.connect(self._clear_comparison)
        return page

    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        general, general_layout = self._panel("Níveis de escolaridade desejados")
        intro = QLabel(
            "Marque os níveis que você aceita. Se nenhum nível for selecionado, o prompt "
            "considerará todos os níveis de escolaridade."
        )
        intro.setObjectName("MutedText")
        intro.setWordWrap(True)
        general_layout.addWidget(intro)

        self.profile_level_checks: dict[str, QPushButton] = {}
        levels_row = QHBoxLayout()
        for level in EDUCATION_LEVELS:
            check = QPushButton(level)
            check.setObjectName("EducationOption")
            check.setCheckable(True)
            check.setAccessibleName(level)
            check.setCursor(Qt.CursorShape.PointingHandCursor)
            check.toggled.connect(
                lambda selected, button=check, name=level: button.setText(f"✓  {name}" if selected else name)
            )
            self.profile_level_checks[level] = check
            levels_row.addWidget(check, 1)
        general_layout.addLayout(levels_row)
        layout.addWidget(general)

        roles_panel, roles_layout = self._panel("Cargos e profissões de interesse")
        roles_help = QLabel(
            "Informe um cargo ou profissão por linha. Exemplos: Médico, Jornalista, "
            "Médico cardiologista. O prompt considerará também os requisitos obrigatórios "
            "para distinguir cargos semelhantes."
        )
        roles_help.setObjectName("MutedText")
        roles_help.setWordWrap(True)
        roles_layout.addWidget(roles_help)
        self.profile_roles_edit = QPlainTextEdit()
        self.profile_roles_edit.setPlaceholderText("Médico\nJornalista\nAnalista de sistemas")
        self.profile_roles_edit.setMaximumHeight(150)
        roles_layout.addWidget(self.profile_roles_edit)

        notes_label = QLabel("Requisitos adicionais (opcional)")
        notes_label.setObjectName("PanelTitle")
        roles_layout.addWidget(notes_label)
        self.profile_notes_edit = QPlainTextEdit()
        self.profile_notes_edit.setPlaceholderText(
            "Ex.: aceitar somente cargos com registro profissional ativo; não considerar contratos temporários."
        )
        self.profile_notes_edit.setMaximumHeight(90)
        roles_layout.addWidget(self.profile_notes_edit)
        save_profile = QPushButton("Salvar perfil")
        save_profile.setObjectName("PrimaryButton")
        save_profile.clicked.connect(self._save_profile)
        roles_layout.addWidget(save_profile)
        self.profile_saved_label = QLabel()
        self.profile_saved_label.setObjectName("MutedText")
        self.profile_saved_label.setTextFormat(Qt.TextFormat.PlainText)
        self.profile_saved_label.setWordWrap(True)
        roles_layout.addWidget(self.profile_saved_label)
        layout.addWidget(roles_panel)
        layout.addStretch()
        self._load_profile()
        return page

    def _load_profile(self) -> None:
        profile = self.database.get_user_profile()
        for level, check in self.profile_level_checks.items():
            check.setChecked(level in profile["niveis_escolaridade"])
        self.profile_roles_edit.setPlainText("\n".join(profile["cargos_desejados"]))
        self.profile_notes_edit.setPlainText(profile["observacoes"])
        self.profile_saved_label.setText(profile_summary(profile))

    def _save_profile(self) -> None:
        profile = {
            "niveis_escolaridade": [
                level for level, check in self.profile_level_checks.items() if check.isChecked()
            ],
            "cargos_desejados": self.profile_roles_edit.toPlainText().splitlines(),
            "observacoes": self.profile_notes_edit.toPlainText(),
        }
        normalized = self.database.save_user_profile(profile)
        self.profile_saved_label.setText("Perfil salvo. " + profile_summary(normalized))
        QMessageBox.information(
            self, "Perfil atualizado",
            "O perfil foi salvo e será aplicado ao próximo prompt gerado na seção Prompts."
        )

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        general, general_layout = self._panel("Preferências")
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Aparência:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Modo claro", "claro")
        self.theme_combo.addItem("Modo escuro", "escuro")
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(self.theme)))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch()
        general_layout.addLayout(theme_row)

        self.auto_widget_check = QCheckBox("Mostrar o widget ao iniciar")
        if sys.platform == "win32":
            startup = QPushButton("Abrir configurações de inicialização do Windows")
            startup.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("ms-settings:startupapps")))
            general_layout.addWidget(startup)
        general_layout.addWidget(self.auto_widget_check)
        row = QGridLayout()
        row.addWidget(QLabel("Quantidade de concursos no widget"), 0, 0)
        self.widget_count = QSpinBox()
        self.widget_count.setRange(1, 20)
        row.addWidget(self.widget_count, 0, 1)

        row.addWidget(QLabel("Largura do widget (px)"), 1, 0)
        self.widget_width = QSpinBox()
        self.widget_width.setRange(320, 700)
        self.widget_width.setSingleStep(10)
        row.addWidget(self.widget_width, 1, 1)

        row.addWidget(QLabel("Altura do widget (px)"), 2, 0)
        self.widget_height = QSpinBox()
        self.widget_height.setRange(300, 900)
        self.widget_height.setSingleStep(10)
        row.addWidget(self.widget_height, 2, 1)
        row.setColumnStretch(2, 1)
        general_layout.addLayout(row)
        dimensions_hint = QLabel(
            "A janela principal pode ser aberta pelo ícone da bandeja. "
            "Use a rolagem do widget quando os cards ultrapassarem a altura disponível."
        )
        dimensions_hint.setWordWrap(True)
        dimensions_hint.setObjectName("HintText")
        general_layout.addWidget(dimensions_hint)
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
        explanation.setObjectName("MutedText")
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
        self._sync_widget_controls()
        return page

    def _sync_widget_controls(self) -> None:
        self.auto_widget_check.setChecked(self.database.get_setting("widget_auto_show", "1") == "1")
        self.widget_count.setValue(self.desktop_widget.item_limit)
        self.widget_width.setValue(self.desktop_widget.widget_width)
        self.widget_height.setValue(self.desktop_widget.widget_height)

    def show_page(self, key: str) -> None:
        labels = {
            "dashboard": ("Visão geral", "Acompanhe seus objetivos e organize sua preparação."),
            "contests": ("Concursos", "Mantenha uma ficha para cada oportunidade de interesse."),
            "content": ("Conteúdo programático", "Estruture disciplinas e tópicos de cada concurso."),
            "compare": ("Comparar conteúdos", "Descubra quais assuntos se repetem entre diferentes seleções."),
            "profile": ("Perfil", "Defina os níveis de escolaridade e os cargos que você deseja encontrar."),
            "prompts": ("Prompts", "Extração de informações de editais"),
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

        elif key == "prompts":
            self.prompts_page.set_profile(self.database.get_user_profile())

    def _add_contest_from_code(self) -> None:
        dialog = ContestCodeDialog(self)
        if not dialog.exec():
            return
        try:
            contest_id = self.database.add_contest_payload(dialog.payload())
            self._refresh_all()
            QMessageBox.information(
                self,
                "Concurso cadastrado",
                f"A ficha e seu conteúdo programático foram adicionados ao banco de dados (código {contest_id}).",
            )
        except Exception as error:
            QMessageBox.critical(self, "Não foi possível importar o código", str(error))

    def _on_theme_changed(self, *_args) -> None:
        selected = self.theme_combo.currentData()
        if selected not in ("claro", "escuro"):
            return
        self.theme = selected
        self.database.set_setting("theme", selected)
        self.apply_theme(selected)
        self._refresh_contest_table()

    def show_desktop_widget(self, *, activate: bool = True) -> None:
        self.desktop_widget.refresh()
        self.desktop_widget.show()
        self.desktop_widget.raise_()
        if activate:
            self.desktop_widget.activateWindow()
        self._update_widget_actions()

    def _toggle_desktop_widget(self) -> None:
        if self.desktop_widget.isVisible():
            self.desktop_widget.hide()
        else:
            self.show_desktop_widget()
        self._update_widget_actions()

    def _update_widget_actions(self) -> None:
        visible = self.desktop_widget.isVisible()
        label = "Ocultar widget" if visible else "Mostrar widget"
        if hasattr(self, "widget_action"):
            self.widget_action.setText(label)
        if self.tray_widget_action is not None:
            self.tray_widget_action.setText(label)

    def _setup_tray(self) -> None:
        self._allow_quit = False
        QApplication.instance().setQuitOnLastWindowClosed(False)
        pixmap = self.windowIcon().pixmap(32, 32)
        icon = (
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
            if pixmap.isNull() else QIcon(pixmap)
        )
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip("Agenda de Concursos")
        menu = QMenu(self)
        open_action = QAction("Abrir Agenda de Concursos", self)
        open_action.triggered.connect(self._restore_main_window)
        menu.addAction(open_action)
        self.tray_widget_action = QAction("Mostrar widget", self)
        self.tray_widget_action.triggered.connect(self._toggle_desktop_widget)
        menu.addAction(self.tray_widget_action)
        menu.addSeparator()
        quit_action = QAction("Sair do aplicativo", self)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(quit_action)
        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        self.tray_icon = tray
        # Keep the icon requested even if Explorer has not created the tray yet.
        tray.show()
        self._update_widget_actions()

    def _restore_main_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._restore_main_window()

    def _quit_application(self) -> None:
        self._allow_quit = True
        self.desktop_widget.hide()
        self.tray_icon.hide()
        self.hide()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _refresh_all(self) -> None:
        self._refresh_contest_table()
        self._refresh_contest_combos(self.content_contest_combo)
        self._refresh_contest_combos(self.compare_a)
        self._refresh_contest_combos(self.compare_b)
        self._load_content()
        self._clear_comparison()
        self._refresh_dashboard()
        self.desktop_widget.refresh()

    def _clear_dashboard_cards(self) -> None:
        while self.dashboard_cards_layout.count():
            item = self.dashboard_cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_dashboard(self) -> None:
        contests = self.database.list_contests()
        self.metric_total.setText(str(len(contests)))
        self.metric_edital.setText(str(sum(item.get("status") == "Edital publicado" for item in contests)))
        self.metric_predicted.setText(str(sum(item.get("status") == "Previsto" for item in contests)))
        self.metric_no_date.setText(str(sum(item.get("status") == "Sem Previsão" for item in contests)))
        self._clear_dashboard_cards()

        for contest in contests:
            contest["cargos"] = self.database.list_cargos(int(contest["id"]))
            card = ContestCard(contest, compact=False, parent=self.dashboard_cards_host)
            card.clicked.connect(self._open_contest_details)
            self.dashboard_cards_layout.addWidget(card)

        if not contests:
            empty = QLabel("Nenhum concurso cadastrado. Use “Cadastrar concurso” para adicionar o primeiro.")
            empty.setObjectName("MutedText")
            empty.setWordWrap(True)
            self.dashboard_cards_layout.addWidget(empty)

    def _open_contest_details(self, contest_id: int) -> None:
        contest = self.database.get_contest(int(contest_id))
        if contest is None:
            QMessageBox.information(self, "Ficha não encontrada", "O concurso pode ter sido removido.")
            return
        program = self.database.get_program(int(contest_id))
        dialog = ContestDetailsDialog(contest, program, self, database=self.database)
        dialog.exec()
        self._refresh_all()

    def _show_selected_contest(self, *_args) -> None:
        contest_id = self._selected_contest_id()
        if contest_id is not None:
            self._open_contest_details(contest_id)

    def _refresh_contest_table(self) -> None:
        if not hasattr(self, "contest_table"):
            return
        rows = self.database.list_contests(self.contest_search.text() if hasattr(self, "contest_search") else "")
        selected_id = self._selected_contest_id()
        self.contest_table.setRowCount(0)
        for contest in rows:
            row_index = self.contest_table.rowCount()
            self.contest_table.insertRow(row_index)
            event_date = format_date_pt_br(contest.get("data_prova")) if contest.get("data_prova") else "—"
            cargo_rows = self.database.list_cargos(int(contest["id"]))
            cargo_names = [str(item.get("nome") or "").strip() for item in cargo_rows if item.get("nome")]
            cargo_summary = ", ".join(cargo_names[:2])
            if len(cargo_names) > 2:
                cargo_summary += f" e outros {len(cargo_names) - 2}"
            if not cargo_summary:
                cargo_summary = contest.get("cargo", "")
            values = [
                contest.get("nome", ""),
                contest.get("orgao", ""),
                cargo_summary,
                contest.get("status", ""),
                event_date,
                contest.get("banca", ""),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value or "—"))
                item.setData(Qt.ItemDataRole.UserRole, contest["id"])
                item.setToolTip(f"<qt>{escape(item.text())}</qt>")
                if column == 3:
                    if self.theme == "escuro":
                        colors = {
                            "Sem Previsão": "#C0CBD8",
                            "Previsto": "#F6CD83",
                            "Edital publicado": "#9BE2BE",
                        }
                    else:
                        colors = {
                            "Sem Previsão": "#53647A",
                            "Previsto": "#925100",
                            "Edital publicado": "#116B4A",
                        }
                    item.setForeground(QColor(colors.get(str(value), "#53647A")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.contest_table.setItem(row_index, column, item)
            if contest["id"] == selected_id:
                self.contest_table.selectRow(row_index)

    def _refresh_contest_combos(self, combo: QComboBox) -> None:
        if combo is None:
            return
        current = combo.currentData()
        with QSignalBlocker(combo):
            combo.clear()
            for contest in self.database.list_contests():
                combo.addItem(contest.get("nome", "Concurso"), contest["id"])
            index = combo.findData(current)
            if combo is self.compare_b and combo.count() < 2:
                combo.setCurrentIndex(-1)
            elif index >= 0:
                combo.setCurrentIndex(index)
            elif combo is self.compare_b:
                first_id = combo.itemData(0)
                combo.setCurrentIndex(int(first_id == self.compare_a.currentData()))
            elif combo.count():
                combo.setCurrentIndex(0)

    def _selected_contest_id(self) -> int | None:
        selected = self.contest_table.selectionModel().selectedRows()
        return int(selected[0].data(Qt.ItemDataRole.UserRole)) if selected else None

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
        data["cargos"] = self.database.list_cargos(contest_id)
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

    def _load_content(self, *_args, preferred_discipline_id: int | None = None) -> None:
        if not hasattr(self, "discipline_list"):
            return
        selected_id = preferred_discipline_id or self._selected_discipline_id()
        contest_id = self.content_contest_combo.currentData()
        disciplines = self.database.list_disciplines(int(contest_id)) if contest_id is not None else []
        selected_row = 0
        with QSignalBlocker(self.discipline_list):
            self.discipline_list.clear()
            for row, discipline in enumerate(disciplines):
                item = QListWidgetItem(discipline["nome"])
                item.setData(Qt.ItemDataRole.UserRole, discipline["id"])
                self.discipline_list.addItem(item)
                if discipline["id"] == selected_id:
                    selected_row = row
            self.discipline_list.setCurrentRow(selected_row)
        self._load_topics()

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
            discipline_id = self.database.add_discipline(int(contest_id), dialog.value())
            self._load_content(preferred_discipline_id=discipline_id)
            self._clear_comparison()

    def _rename_discipline(self) -> None:
        discipline_id = self._selected_discipline_id()
        selected = self.discipline_list.currentItem()
        if discipline_id is None or selected is None:
            QMessageBox.information(self, "Selecione uma disciplina", "Escolha uma disciplina para renomear.")
            return
        dialog = NameDialog("Renomear disciplina", "Novo nome:", self, selected.text())
        if dialog.exec() and dialog.value():
            self.database.rename_discipline(discipline_id, dialog.value())
            self._load_content()
            self._clear_comparison()

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
            self._clear_comparison()

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
            self._clear_comparison()

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
            self._clear_comparison()

    def _delete_topic(self) -> None:
        topic_id = self._selected_topic_id()
        if topic_id is None:
            QMessageBox.information(self, "Selecione um tópico", "Escolha um tópico para remover.")
            return
        answer = QMessageBox.question(self, "Excluir tópico", "Deseja excluir o tópico selecionado?")
        if answer == QMessageBox.StandardButton.Yes:
            self.database.delete_topic(topic_id)
            self._load_topics()
            self._clear_comparison()

    def _clear_comparison(self, *_args) -> None:
        self.compare_tree.clear()
        self.compare_score.setText("Selecione dois concursos e inicie a comparação.")
        self.compare_detail.setText("Estimativa textual baseada nos tópicos cadastrados.")
        self.compare_detail.setToolTip("")

    def _run_comparison(self) -> None:
        id_a, id_b = self.compare_a.currentData(), self.compare_b.currentData()
        if self.compare_a.count() < 2 or id_a is None or id_b is None:
            QMessageBox.information(self, "Cadastre concursos", "Cadastre pelo menos dois concursos.")
            return
        if id_a == id_b:
            QMessageBox.information(self, "Seleção inválida", "Escolha dois concursos diferentes.")
            return
        program_a = self.database.get_program(int(id_a))
        program_b = self.database.get_program(int(id_b))
        if not all(any(discipline["topicos"] for discipline in program) for program in (program_a, program_b)):
            self.compare_score.setText("Conteúdo insuficiente para comparar.")
            self.compare_detail.setText("Cadastre pelo menos um tópico em cada concurso selecionado.")
            return
        result = compare_programs(program_a, program_b)
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
        self.database.set_setting("theme", self.theme)
        count = self.widget_count.value()
        width = self.widget_width.value()
        height = self.widget_height.value()
        self.database.set_setting("widget_items", str(count))
        self.database.set_setting("widget_width", str(width))
        self.database.set_setting("widget_height", str(height))
        self.database.set_setting("widget_auto_show", "1" if self.auto_widget_check.isChecked() else "0")
        self.desktop_widget.set_item_limit(count)
        self.desktop_widget.set_dimensions(width, height)
        QMessageBox.information(self, "Preferências salvas", "As configurações foram atualizadas.")

    def _export_backup(self) -> None:
        suggested_name = f"agenda-de-concursos-backup-{date.today():%Y-%m-%d}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar backup", suggested_name, "Arquivo JSON (*.json)"
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
        dialog = QMessageBox(
            QMessageBox.Icon.Warning, "Substituir dados atuais",
            "A importação substituirá todas as fichas e conteúdos atualmente cadastrados. "
            "Recomenda-se exportar um backup antes de continuar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, self,
        )
        dialog.button(QMessageBox.StandardButton.Yes).setText("Sim")
        dialog.button(QMessageBox.StandardButton.Cancel).setText("Cancelar")
        dialog.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if dialog.exec() != QMessageBox.StandardButton.Yes:
            return
        try:
            self.database.import_json(Path(path))
            self.apply_theme(self.database.get_setting("theme", DEFAULT_THEME))
            with QSignalBlocker(self.theme_combo):
                self.theme_combo.setCurrentIndex(self.theme_combo.findData(self.theme))
            self.desktop_widget.load_preferences()
            self._sync_widget_controls()
            self._load_profile()
            self._refresh_all()
            QMessageBox.information(self, "Backup importado", "Os dados foram restaurados.")
        except Exception as error:
            QMessageBox.critical(self, "Falha na importação", str(error))

    def closeEvent(self, event) -> None:
        if not self._allow_quit:
            if not QSystemTrayIcon.isSystemTrayAvailable() and not self.desktop_widget.isVisible():
                self.show_desktop_widget(activate=False)
            self.hide()
            event.ignore()
            return
        self.desktop_widget.hide()
        self.tray_icon.hide()
        event.accept()
