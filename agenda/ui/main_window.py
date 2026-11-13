from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFrame,
    QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QSpinBox, QStackedWidget, QSystemTrayIcon,
    QTableWidget, QTableWidgetItem, QToolBar, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)

from agenda.database import Database
from agenda.services.dates import format_date_pt_br
from agenda.services.profile import EDUCATION_LEVELS, profile_summary
from agenda.services.similarity import compare_programs
from agenda.startup import disable_startup, enable_startup, startup_enabled
from agenda.ui.assets import asset_path
from agenda.ui.cards import ContestCard
from agenda.ui.code_dialogs import ContestCodeDialog, PromptDialog
from agenda.ui.details_dialog import ContestDetailsDialog
from agenda.ui.dialogs import ContestDialog, NameDialog, TopicDialog
from agenda.ui.styles import theme_stylesheet
from agenda.ui.widget import DesktopWidget


class MainWindow(QMainWindow):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.theme = database.get_setting("theme", "claro")
        if self.theme not in ("claro", "escuro"):
            self.theme = "claro"
        self.desktop_widget = DesktopWidget(database)
        self.desktop_widget.contest_selected.connect(self._open_contest_details)
        self.setWindowTitle("Agenda de Concursos")
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
        self.resize(1280, 820)
        self.setMinimumSize(1000, 680)
        self.apply_theme(self.theme)
        self._build_toolbar()
        self._build_ui()
        self._setup_tray()
        self._refresh_all()
        if self.database.get_setting("widget_auto_show", "0") == "1":
            self.show_desktop_widget()

    def apply_theme(self, theme: str) -> None:
        self.theme = theme if theme in ("claro", "escuro") else "claro"
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
        prompts.triggered.connect(self._open_prompts)
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
        subtitle = QLabel("Cada card resume um concurso. Clique em qualquer um para consultar a ficha completa.")
        subtitle.setObjectName("MutedText")
        panel_layout.addWidget(subtitle)
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
        hint = QLabel("Dica: cadastre primeiro seus concursos de interesse. Você pode completar as datas depois.")
        hint.setWordWrap(True)
        hint.setObjectName("MutedText")
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
        add_code = QPushButton("Inserir por código JSON")
        add_code.setToolTip("Cadastrar uma ficha completa colando um objeto JSON validado")
        add_code.clicked.connect(self._add_contest_from_code)
        toolbar.addWidget(add_code)
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
        summary_layout.addWidget(self.compare_score)
        self.compare_detail = QLabel(
            "Estimativa textual baseada nos tópicos cadastrados. Revise os pares sugeridos antes de tomar decisões de estudo."
        )
        self.compare_detail.setWordWrap(True)
        self.compare_detail.setObjectName("MutedText")
        summary_layout.addWidget(self.compare_detail)
        self.compare_tree = QTreeWidget()
        self.compare_tree.setHeaderLabels(["Disciplina / tópico", "Correspondência", "Observação"])
        self.compare_tree.setColumnWidth(0, 440)
        summary_layout.addWidget(self.compare_tree, 1)
        layout.addWidget(summary_panel, 1)
        return page

    def _build_profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        profile = self.database.get_user_profile()
        general, general_layout = self._panel("Níveis de escolaridade desejados")
        intro = QLabel(
            "Marque os níveis que você aceita. Se nenhum nível for selecionado, o prompt "
            "considerará todos os níveis de escolaridade."
        )
        intro.setObjectName("MutedText")
        intro.setWordWrap(True)
        general_layout.addWidget(intro)

        self.profile_level_checks: dict[str, QCheckBox] = {}
        levels_row = QHBoxLayout()
        for level in EDUCATION_LEVELS:
            check = QCheckBox(level)
            check.setChecked(level in profile["niveis_escolaridade"])
            self.profile_level_checks[level] = check
            levels_row.addWidget(check)
        levels_row.addStretch()
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
        self.profile_roles_edit.setPlainText("\n".join(profile["cargos_desejados"]))
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
        self.profile_notes_edit.setPlainText(profile["observacoes"])
        roles_layout.addWidget(self.profile_notes_edit)
        save_profile = QPushButton("Salvar perfil")
        save_profile.setObjectName("PrimaryButton")
        save_profile.clicked.connect(self._save_profile)
        roles_layout.addWidget(save_profile)
        self.profile_saved_label = QLabel(profile_summary(profile))
        self.profile_saved_label.setObjectName("MutedText")
        self.profile_saved_label.setWordWrap(True)
        roles_layout.addWidget(self.profile_saved_label)
        layout.addWidget(roles_panel)
        layout.addStretch()
        return page

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
        row.addSpacing(16)

        row.addWidget(QLabel("Largura do widget (px):"))
        self.widget_width = QSpinBox()
        self.widget_width.setRange(320, 700)
        self.widget_width.setSingleStep(10)
        self.widget_width.setValue(max(320, min(700, int(self.database.get_setting("widget_width", "390") or 390))))
        row.addWidget(self.widget_width)

        row.addWidget(QLabel("Altura (px):"))
        self.widget_height = QSpinBox()
        self.widget_height.setRange(300, 900)
        self.widget_height.setSingleStep(10)
        self.widget_height.setValue(max(300, min(900, int(self.database.get_setting("widget_height", "470") or 470))))
        row.addWidget(self.widget_height)
        row.addStretch()
        general_layout.addLayout(row)
        dimensions_hint = QLabel(
            "A quantidade de cards visíveis se ajusta à altura escolhida. "
            "O widget não exibe barras de rolagem; aumente a altura para mostrar mais concursos."
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
        return page

    def show_page(self, key: str) -> None:
        if key == "prompts":
            for nav_key, button in self.nav_buttons.items():
                button.setChecked(nav_key == key)
            self._open_prompts()
            return
        labels = {
            "dashboard": ("Visão geral", "Acompanhe seus objetivos e organize sua preparação."),
            "contests": ("Concursos", "Mantenha uma ficha para cada oportunidade de interesse."),
            "content": ("Conteúdo programático", "Estruture disciplinas e tópicos de cada concurso."),
            "compare": ("Comparar conteúdos", "Descubra quais assuntos se repetem entre diferentes seleções."),
            "profile": ("Perfil", "Defina os níveis de escolaridade e os cargos que você deseja encontrar."),
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

    def _open_prompts(self) -> None:
        PromptDialog(self, self.database.get_user_profile()).exec()

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

    def show_desktop_widget(self) -> None:
        self.desktop_widget.refresh()
        self.desktop_widget.show()
        self.desktop_widget.raise_()
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
        self.tray_icon = None
        self.tray_widget_action = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            app = QApplication.instance()
            if app is not None:
                app.setQuitOnLastWindowClosed(True)
            return

        app = QApplication.instance()
        if app is not None:
            app.setQuitOnLastWindowClosed(False)
        tray = QSystemTrayIcon(QIcon(str(asset_path("app_icon.svg"))), self)
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
        tray.show()
        self.tray_icon = tray
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
        if self.tray_icon is not None:
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

    def _refresh_contest_table(self) -> None:
        if not hasattr(self, "contest_table"):
            return
        rows = self.database.list_contests(self.contest_search.text() if hasattr(self, "contest_search") else "")
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
                values = dialog.values()
                cargos = values.pop("cargos", [])
                contest_id = self.database.save_contest(values)
                self.database.replace_cargos(contest_id, cargos)
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
                values = dialog.values()
                cargos = values.pop("cargos", [])
                self.database.save_contest(values, contest_id)
                self.database.replace_cargos(contest_id, cargos)
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
        self.database.set_setting("theme", self.theme)
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
        if self.tray_icon is not None and not self._allow_quit:
            self.hide()
            event.ignore()
            return
        self.desktop_widget.hide()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        event.accept()
