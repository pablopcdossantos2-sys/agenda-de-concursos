from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QTextEdit, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QDate


STATUSES = ["Sem Previsão", "Previsto", "Edital publicado"]


class ContestDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, data: dict[str, Any] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ficha do concurso")
        self.setMinimumWidth(560)
        data = data or {}
        layout = QVBoxLayout(self)
        intro = QLabel("Cadastre o processo seletivo mesmo antes da publicação do edital.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color:#68788F; padding: 2px 0 8px;")
        layout.addWidget(intro)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.fields: dict[str, QLineEdit] = {}
        definitions = [
            ("nome", "Concurso / seleção *", True),
            ("orgao", "Órgão / instituição", False),
            ("cargo", "Cargo / especialidade", False),
            ("banca", "Banca organizadora", False),
            ("localidade", "Localidade", False),
            ("inscricoes_inicio", "Início das inscrições (AAAA-MM-DD)", False),
            ("inscricoes_fim", "Fim das inscrições (AAAA-MM-DD)", False),
            ("data_prova", "Data da prova (AAAA-MM-DD)", False),
            ("data_prevista", "Data prevista (AAAA-MM-DD)", False),
            ("url_edital", "Link do edital", False),
            ("url_oficial", "Site oficial", False),
        ]
        for key, label, required in definitions:
            edit = QLineEdit(str(data.get(key) or ""))
            edit.setPlaceholderText("Obrigatório" if required else "Não informado")
            self.fields[key] = edit
            form.addRow(label, edit)

        self.status = QComboBox()
        self.status.addItems(STATUSES)
        current = str(data.get("status") or "Sem Previsão")
        if current not in STATUSES:
            self.status.addItem(current)
        self.status.setCurrentText(current)
        form.addRow("Situação", self.status)

        self.priority = QCheckBox("Destacar como prioridade")
        self.priority.setChecked(bool(data.get("prioridade", 0)))
        form.addRow("", self.priority)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Anotações pessoais, fontes, previsões e observações...")
        self.notes.setFixedHeight(85)
        self.notes.setPlainText(str(data.get("observacoes") or ""))
        form.addRow("Observações", self.notes)
        layout.addLayout(form)

        hint = QLabel("As datas são opcionais. Use o formato AAAA-MM-DD para facilitar a ordenação.")
        hint.setStyleSheet("color:#7B8798; font-size:8pt;")
        layout.addWidget(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._original = data

    def _validate(self) -> None:
        if not self.fields["nome"].text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do concurso.")
            self.fields["nome"].setFocus()
            return
        for key in ("inscricoes_inicio", "inscricoes_fim", "data_prova", "data_prevista"):
            value = self.fields[key].text().strip()
            if value and (len(value) != 10 or not QDate.fromString(value, "yyyy-MM-dd").isValid()):
                QMessageBox.warning(self, "Data inválida", f"Confira a data do campo {key.replace('_', ' ')}.")
                self.fields[key].setFocus()
                return
        self.accept()

    def values(self) -> dict[str, Any]:
        data = {key: field.text().strip() for key, field in self.fields.items()}
        data.update({
            "status": self.status.currentText(),
            "prioridade": int(self.priority.isChecked()),
            "observacoes": self.notes.toPlainText().strip(),
        })
        return data


class TopicDialog(QDialog):
    def __init__(
        self, parent: QWidget | None = None, title: str = "Tópico programático",
        name: str = "", canonical_name: str = ""
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(name)
        self.name.setPlaceholderText("Ex.: Controle de constitucionalidade")
        self.canonical = QLineEdit(canonical_name)
        self.canonical.setPlaceholderText("Opcional: chave comum para tópicos equivalentes")
        self.canonical.setToolTip(
            "Use o mesmo nome padronizado em editais diferentes quando os tópicos forem equivalentes."
        )
        form.addRow("Descrição do tópico *", self.name)
        form.addRow("Nome padronizado", self.canonical)
        layout.addLayout(form)
        note = QLabel(
            "O nome padronizado é opcional. Ao usar a mesma chave em dois concursos, "
            "o comparador reconhecerá a correspondência explicitamente."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#68788F; font-size:8pt;")
        layout.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe a descrição do tópico.")
            return
        self.accept()

    def values(self) -> tuple[str, str]:
        return self.name.text().strip(), self.canonical.text().strip()


class NameDialog(QDialog):
    def __init__(self, title: str, label: str, parent: QWidget | None = None, value: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(label))
        self.edit = QLineEdit(value)
        layout.addWidget(self.edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def value(self) -> str:
        return self.edit.text().strip()
