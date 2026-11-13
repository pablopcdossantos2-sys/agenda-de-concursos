from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)


CARGO_FIELDS = (
    ("nome", "Cargo / especialidade *"),
    ("nivel_escolaridade", "Nível de escolaridade"),
    ("requisitos", "Requisitos obrigatórios"),
    ("salario_inicial", "Remuneração inicial"),
    ("salario_final", "Remuneração final / teto"),
    ("beneficios", "Benefícios / gratificações"),
    ("jornada", "Jornada de trabalho"),
    ("vagas", "Número de vagas"),
    ("localidade", "Localidade / lotação"),
)


class CargoDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, data: dict[str, Any] | None = None):
        super().__init__(parent)
        data = data or {}
        self.setWindowTitle("Cargo e remuneração")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.fields: dict[str, QLineEdit] = {}
        for key, label in CARGO_FIELDS:
            edit = QLineEdit(str(data.get(key) or ""))
            edit.setPlaceholderText("Não informado" if key != "nome" else "Ex.: Médico — Cardiologia")
            self.fields[key] = edit
            form.addRow(label, edit)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText(
            "Condições específicas de remuneração, carga horária, titulação ou lotação..."
        )
        self.notes.setFixedHeight(85)
        self.notes.setPlainText(str(data.get("observacoes") or ""))
        form.addRow("Observações", self.notes)
        layout.addLayout(form)

        hint = QLabel(
            "Registre a remuneração exatamente como aparece no edital, incluindo unidade, "
            "periodicidade e condições. Não some benefícios ao salário-base."
        )
        hint.setObjectName("HintText")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        if not self.fields["nome"].text().strip():
            QMessageBox.warning(self, "Campo obrigatório", "Informe o nome do cargo.")
            self.fields["nome"].setFocus()
            return
        self.accept()

    def values(self) -> dict[str, str]:
        result = {key: field.text().strip() for key, field in self.fields.items()}
        result["observacoes"] = self.notes.toPlainText().strip()
        return result


class CargoManagerDialog(QDialog):
    def __init__(
        self,
        cargos: list[dict[str, Any]] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Cargos e salários")
        self.setMinimumSize(670, 480)
        self._cargos = [dict(item) for item in (cargos or [])]

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Cadastre cada cargo ou especialidade separadamente. Requisitos, remuneração, "
            "benefícios e jornada devem permanecer associados à vaga correta."
        )
        intro.setObjectName("MutedText")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget, 1)

        actions = QHBoxLayout()
        add = QPushButton("Adicionar cargo")
        add.setObjectName("PrimaryButton")
        add.clicked.connect(self._add)
        edit = QPushButton("Editar")
        edit.clicked.connect(self._edit)
        remove = QPushButton("Remover")
        remove.setObjectName("DangerButton")
        remove.clicked.connect(self._remove)
        actions.addWidget(add)
        actions.addWidget(edit)
        actions.addWidget(remove)
        actions.addStretch()
        layout.addLayout(actions)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Concluir")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self._refresh()

    def _refresh(self, selected: int = 0) -> None:
        self.list_widget.clear()
        for cargo in self._cargos:
            title = cargo.get("nome") or "Cargo sem nome"
            level = cargo.get("nivel_escolaridade") or "Nível não informado"
            salary = cargo.get("salario_inicial") or "Remuneração não informada"
            item = QListWidgetItem(f"{title}\n{level} · {salary}")
            item.setToolTip(
                f"{title}\nRequisitos: {cargo.get('requisitos') or 'Não informados'}\n"
                f"Salário inicial: {salary}\nSalário final: {cargo.get('salario_final') or 'Não informado'}"
            )
            self.list_widget.addItem(item)
        if self.list_widget.count():
            self.list_widget.setCurrentRow(min(max(0, selected), self.list_widget.count() - 1))

    def _selected_index(self) -> int | None:
        row = self.list_widget.currentRow()
        return row if 0 <= row < len(self._cargos) else None

    def _add(self) -> None:
        dialog = CargoDialog(self)
        if dialog.exec():
            self._cargos.append(dialog.values())
            self._refresh(len(self._cargos) - 1)

    def _edit(self) -> None:
        index = self._selected_index()
        if index is None:
            QMessageBox.information(self, "Selecione um cargo", "Escolha um cargo para editar.")
            return
        dialog = CargoDialog(self, self._cargos[index])
        if dialog.exec():
            self._cargos[index] = dialog.values()
            self._refresh(index)

    def _remove(self) -> None:
        index = self._selected_index()
        if index is None:
            QMessageBox.information(self, "Selecione um cargo", "Escolha um cargo para remover.")
            return
        self._cargos.pop(index)
        self._refresh(max(0, index - 1))

    def cargos(self) -> list[dict[str, str]]:
        return [dict(item) for item in self._cargos]
