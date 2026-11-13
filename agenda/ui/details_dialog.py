from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)


FIELD_LABELS = (
    ("orgao", "Órgão / instituição"),
    ("cargo", "Cargo / especialidade"),
    ("banca", "Banca organizadora"),
    ("localidade", "Localidade"),
    ("status", "Situação"),
    ("prioridade", "Prioridade"),
    ("inscricoes_inicio", "Início das inscrições"),
    ("inscricoes_fim", "Fim das inscrições"),
    ("data_prova", "Data da prova"),
    ("data_prevista", "Data prevista"),
    ("url_edital", "Link do edital"),
    ("url_oficial", "Site oficial"),
    ("created_at", "Ficha criada em"),
    ("updated_at", "Última atualização"),
)


class ContestDetailsDialog(QDialog):
    """Apresenta todos os dados da ficha e o conteúdo programático."""

    def __init__(
        self,
        contest: dict[str, Any],
        program: list[dict[str, Any]] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.contest = dict(contest)
        self.program = program or []
        self.setWindowTitle(f"Ficha completa — {self.contest.get('nome', 'Concurso')}")
        self.setMinimumSize(650, 520)
        self.resize(790, 720)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("DetailsContent")
        body = QVBoxLayout(content)
        body.setContentsMargins(4, 4, 10, 4)
        body.setSpacing(12)

        title = QLabel(str(self.contest.get("nome") or "Concurso sem nome"))
        title.setObjectName("DetailsTitle")
        title.setWordWrap(True)
        body.addWidget(title)

        status = QLabel(str(self.contest.get("status") or "Sem Previsão"))
        status.setObjectName("ContestCardStatus")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status.setMaximumWidth(190)
        body.addWidget(status, 0, Qt.AlignmentFlag.AlignLeft)

        main_fields = [(key, label) for key, label in FIELD_LABELS
                       if key not in ("status", "inscricoes_inicio", "inscricoes_fim", "data_prova",
                                      "data_prevista", "url_edital", "url_oficial",
                                      "created_at", "updated_at")]
        self._add_field_section(body, "Informações gerais", main_fields)
        self._add_field_section(
            body,
            "Calendário",
            [
                ("inscricoes_inicio", "Início das inscrições"),
                ("inscricoes_fim", "Fim das inscrições"),
                ("data_prova", "Data da prova"),
                ("data_prevista", "Data prevista"),
            ],
        )
        self._add_link_section(body)
        self._add_observations(body)
        self._add_program_section(body)
        self._add_field_section(
            body,
            "Registro da ficha",
            [("created_at", "Criada em"), ("updated_at", "Atualizada em")],
        )
        body.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        close = QPushButton("Fechar")
        close.setObjectName("PrimaryButton")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        outer.addLayout(footer)

    @staticmethod
    def _display_value(key: str, value: Any) -> str:
        if key == "prioridade":
            return "Sim" if bool(value) else "Não"
        if value is None or str(value).strip() == "":
            return "Não informado"
        return str(value)

    def _section(self, title: str, parent_layout: QVBoxLayout) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame()
        frame.setObjectName("DetailsSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        parent_layout.addWidget(frame)
        return frame, layout

    def _add_field_section(
        self, parent_layout: QVBoxLayout, title: str, fields: list[tuple[str, str]]
    ) -> None:
        if not fields:
            return
        _, layout = self._section(title, parent_layout)
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(9)
        for row, (key, label) in enumerate(fields):
            caption = QLabel(label)
            caption.setObjectName("DetailCaption")
            value = QLabel(self._display_value(key, self.contest.get(key)))
            value.setObjectName("DetailValue")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(caption, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(value, row, 1)
        layout.addLayout(grid)

    def _add_link_section(self, parent_layout: QVBoxLayout) -> None:
        links = [
            ("url_edital", "Abrir edital"),
            ("url_oficial", "Abrir site oficial"),
        ]
        available = [(key, label, str(self.contest.get(key) or "").strip())
                     for key, label in links if str(self.contest.get(key) or "").strip()]
        if not available:
            self._add_field_section(parent_layout, "Links e fontes", links)
            return
        _, layout = self._section("Links e fontes", parent_layout)
        for key, label, url in available:
            row = QHBoxLayout()
            value = QLabel(url)
            value.setObjectName("DetailValue")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(value, 1)
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, address=url: QDesktopServices.openUrl(QUrl(address)))
            row.addWidget(button)
            layout.addLayout(row)
        for key, label in links:
            if not str(self.contest.get(key) or "").strip():
                value = QLabel(f"{label}: Não informado")
                value.setObjectName("DetailCaption")
                layout.addWidget(value)

    def _add_observations(self, parent_layout: QVBoxLayout) -> None:
        notes = str(self.contest.get("observacoes") or "").strip()
        _, layout = self._section("Observações", parent_layout)
        value = QLabel(notes or "Nenhuma observação registrada.")
        value.setObjectName("DetailValue")
        value.setWordWrap(True)
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(value)

    def _add_program_section(self, parent_layout: QVBoxLayout) -> None:
        _, layout = self._section("Conteúdo programático", parent_layout)
        if not self.program:
            label = QLabel("Nenhuma disciplina ou tópico cadastrado.")
            label.setObjectName("DetailCaption")
            layout.addWidget(label)
            return

        for discipline in self.program:
            name = QLabel(str(discipline.get("nome") or "Disciplina sem nome"))
            name.setObjectName("DisciplineTitle")
            layout.addWidget(name)
            topics = discipline.get("topicos") or []
            if not topics:
                empty = QLabel("Sem tópicos cadastrados.")
                empty.setObjectName("DetailCaption")
                layout.addWidget(empty)
            for topic in topics:
                topic_name = str(topic.get("nome") or "Tópico sem nome")
                canonical = str(topic.get("nome_padronizado") or "").strip()
                text = f"• {topic_name}"
                if canonical:
                    text += f"  ·  Padronizado: {canonical}"
                item = QLabel(text)
                item.setObjectName("DetailValue")
                item.setWordWrap(True)
                item.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                layout.addWidget(item)
