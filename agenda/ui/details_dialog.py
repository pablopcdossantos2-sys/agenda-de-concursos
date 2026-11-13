from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from agenda.services.dates import format_date_pt_br, format_datetime_pt_br
from agenda.ui.cargo_dialogs import CargoManagerDialog


GENERAL_FIELDS = (
    ("orgao", "Órgão / instituição"),
    ("cargo", "Cargo / especialidade (campo legado)"),
    ("banca", "Banca organizadora"),
    ("localidade", "Localidade"),
    ("prioridade", "Prioridade"),
)


class ContestDetailsDialog(QDialog):
    """Apresenta os dados gerais, cargos, fontes e conteúdo programático."""

    def __init__(
        self,
        contest: dict[str, Any],
        program: list[dict[str, Any]] | None = None,
        parent: QWidget | None = None,
        database=None,
    ):
        super().__init__(parent)
        self.contest = dict(contest)
        self.program = program or []
        self.database = database
        self.cargos = database.list_cargos(int(contest["id"])) if database else list(contest.get("cargos") or [])
        self.setWindowTitle(f"Ficha completa — {self.contest.get('nome', 'Concurso')}")
        self.setMinimumSize(650, 520)
        self.resize(790, 760)

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

        self._add_field_section(body, "Informações gerais", list(GENERAL_FIELDS))
        self._add_field_section(
            body,
            "Calendário",
            [
                ("inscricoes_inicio", "Início das inscrições"),
                ("inscricoes_fim", "Fim das inscrições"),
                ("data_prova", "Data da prova"),
            ],
        )
        self._add_link_section(body)
        self._add_cargos_section(body)
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
        if key in ("inscricoes_inicio", "inscricoes_fim", "data_prova"):
            return format_date_pt_br(str(value))
        if key in ("created_at", "updated_at"):
            return format_datetime_pt_br(str(value))
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

    @staticmethod
    def _normalized_url(address: str) -> QUrl | None:
        clean = (address or "").strip()
        if not clean:
            return None
        url = QUrl.fromUserInput(clean)
        if not url.isValid() or url.scheme().lower() not in ("http", "https") or not url.host():
            return None
        return url

    def _open_link(self, address: str) -> None:
        url = self._normalized_url(address)
        if url is None:
            QMessageBox.warning(
                self, "Link inválido",
                "O endereço salvo não é um link HTTP/HTTPS válido. Confira a URL na ficha do concurso.",
            )
            return
        opened = QDesktopServices.openUrl(url)
        if not opened:
            QGuiApplication.clipboard().setText(url.toString())
            QMessageBox.warning(
                self, "Não foi possível abrir o link",
                "O Windows não conseguiu abrir o endereço. O link foi copiado para a área de transferência.",
            )

    def _add_link_section(self, parent_layout: QVBoxLayout) -> None:
        links = [
            ("url_edital", "Abrir edital"),
            ("url_oficial", "Abrir site oficial"),
        ]
        _, layout = self._section("Links e fontes", parent_layout)
        available = [
            (key, label, str(self.contest.get(key) or "").strip())
            for key, label in links if str(self.contest.get(key) or "").strip()
        ]
        if not available:
            label = QLabel("Nenhum link de edital ou site oficial foi cadastrado.")
            label.setObjectName("DetailCaption")
            layout.addWidget(label)
            return

        for key, label, address in available:
            row = QHBoxLayout()
            value = QLabel(address)
            value.setObjectName("DetailValue")
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(value, 1)
            button = QPushButton(label)
            button.setObjectName("PrimaryButton")
            button.clicked.connect(lambda checked=False, target=address: self._open_link(target))
            row.addWidget(button)
            layout.addLayout(row)

    def _add_cargos_section(self, parent_layout: QVBoxLayout) -> None:
        _, layout = self._section("Cargos e salários", parent_layout)
        heading_row = QHBoxLayout()
        self.cargos_count = QLabel("")
        self.cargos_count.setObjectName("DetailCaption")
        heading_row.addWidget(self.cargos_count, 1)
        if self.database is not None:
            manage = QPushButton("Gerenciar cargos e salários")
            manage.clicked.connect(self._manage_cargos)
            heading_row.addWidget(manage)
        layout.addLayout(heading_row)
        self.cargos_content_layout = QVBoxLayout()
        self.cargos_content_layout.setSpacing(8)
        layout.addLayout(self.cargos_content_layout)
        self._refresh_cargos()

    def _refresh_cargos(self) -> None:
        while self.cargos_content_layout.count():
            item = self.cargos_content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cargos_count.setText(f"{len(self.cargos)} cargo(s) registrado(s)")
        if not self.cargos:
            empty = QLabel("Nenhum cargo ou faixa salarial cadastrada. Edite a ficha para incluir essas informações.")
            empty.setObjectName("DetailCaption")
            empty.setWordWrap(True)
            self.cargos_content_layout.addWidget(empty)
            return

        for cargo in self.cargos:
            card = QFrame()
            card.setObjectName("CargoDetailCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(11, 9, 11, 9)
            card_layout.setSpacing(5)

            title = QLabel(str(cargo.get("nome") or "Cargo sem nome"))
            title.setObjectName("DisciplineTitle")
            title.setWordWrap(True)
            card_layout.addWidget(title)

            meta = []
            for field in ("nivel_escolaridade", "vagas", "jornada", "localidade"):
                value = str(cargo.get(field) or "").strip()
                if value:
                    meta.append(value)
            meta_label = QLabel(" · ".join(meta) if meta else "Escolaridade, vagas e jornada não informadas")
            meta_label.setObjectName("DetailCaption")
            meta_label.setWordWrap(True)
            card_layout.addWidget(meta_label)

            salary = str(cargo.get("salario_inicial") or "").strip()
            salary_final = str(cargo.get("salario_final") or "").strip()
            if salary or salary_final:
                salary_text = "Remuneração: " + (salary or "não informada")
                if salary_final:
                    salary_text += f" até {salary_final}"
            else:
                salary_text = "Remuneração não informada"
            if cargo.get("beneficios"):
                salary_text += f" · Benefícios: {cargo['beneficios']}"
            salary_label = QLabel(salary_text)
            salary_label.setObjectName("DetailValue")
            salary_label.setWordWrap(True)
            card_layout.addWidget(salary_label)

            for label, key in (
                ("Requisitos", "requisitos"),
                ("Observações", "observacoes"),
            ):
                value = str(cargo.get(key) or "").strip()
                if value:
                    field = QLabel(f"{label}: {value}")
                    field.setObjectName("DetailValue")
                    field.setWordWrap(True)
                    card_layout.addWidget(field)
            self.cargos_content_layout.addWidget(card)

    def _manage_cargos(self) -> None:
        if self.database is None:
            return
        contest_id = int(self.contest["id"])
        dialog = CargoManagerDialog(self.database.list_cargos(contest_id), self)
        if dialog.exec():
            try:
                self.database.replace_cargos(contest_id, dialog.cargos())
                self.cargos = self.database.list_cargos(contest_id)
                self._refresh_cargos()
            except Exception as error:
                QMessageBox.critical(self, "Não foi possível salvar os cargos", str(error))

    def _add_observations(self, parent_layout: QVBoxLayout) -> None:
        notes = str(self.contest.get("observacoes") or "").strip()
        _, layout = self._section("Observações", parent_layout)
        if not notes:
            empty = QLabel("Nenhuma observação registrada.")
            empty.setObjectName("DetailCaption")
            layout.addWidget(empty)
            return

        blocks = [line.strip() for line in notes.replace("\r\n", "\n").split("\n") if line.strip()]
        for line in blocks:
            card = QFrame()
            card.setObjectName("ObservationItem")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 7, 10, 7)
            card_layout.setSpacing(2)
            clean = line.lstrip("-• ").strip()
            if ":" in clean and len(clean.split(":", 1)[0]) <= 45:
                label_text, detail_text = clean.split(":", 1)
                label = QLabel(label_text.strip())
                label.setObjectName("DetailCaption")
                value = QLabel(detail_text.strip())
                value.setObjectName("DetailValue")
                value.setWordWrap(True)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                card_layout.addWidget(label)
                card_layout.addWidget(value)
            else:
                value = QLabel(clean)
                value.setObjectName("DetailValue")
                value.setWordWrap(True)
                value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                card_layout.addWidget(value)
            layout.addWidget(card)

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
