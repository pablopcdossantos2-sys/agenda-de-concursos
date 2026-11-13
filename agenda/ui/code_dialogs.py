from __future__ import annotations

from typing import Any

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWidget,
)

from agenda.services.contest_payload import parse_contest_json
from agenda.services.prompts import PROMPT_EXTRACAO_CONCURSO


SAMPLE_JSON = """{
  "schema_version": 1,
  "concurso": {
    "nome": "Concurso de exemplo",
    "orgao": "Órgão público",
    "cargo": "Cargo / especialidade",
    "banca": "",
    "localidade": "",
    "status": "Previsto",
    "inscricoes_inicio": "",
    "inscricoes_fim": "",
    "data_prova": "",
    "data_prevista": "",
    "url_edital": "",
    "url_oficial": "",
    "observacoes": "",
    "prioridade": false,
    "disciplinas": [
      {
        "nome": "Língua Portuguesa",
        "topicos": [
          {
            "nome": "Compreensão e interpretação de textos",
            "nome_padronizado": ""
          }
        ]
      }
    ]
  }
}"""


class ContestCodeDialog(QDialog):
    """Recebe uma ficha individual por JSON, valida e prepara para gravação."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Inserir concurso por código JSON")
        self.setMinimumSize(760, 620)
        self._payload: dict[str, Any] | None = None

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Cole abaixo o JSON produzido por uma IA usando a seção Prompts, "
            "ou edite o exemplo. O conteúdo será validado antes de ser salvo."
        )
        intro.setObjectName("MutedText")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("CodeEditor")
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.editor.setTabStopDistance(4 * self.editor.fontMetrics().horizontalAdvance(" "))
        self.editor.setPlainText(SAMPLE_JSON)
        layout.addWidget(self.editor, 1)

        self.result_label = QLabel("O cadastro ainda não foi validado.")
        self.result_label.setObjectName("MutedText")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Validar e adicionar")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate_and_accept(self) -> None:
        try:
            payload = parse_contest_json(self.editor.toPlainText())
        except ValueError as error:
            self._payload = None
            self.result_label.setText(f"Não foi possível validar: {error}")
            QMessageBox.warning(self, "JSON não válido", str(error))
            return

        contest = payload["concurso"]
        discipline_count = len(contest["disciplinas"])
        topic_count = sum(len(item["topicos"]) for item in contest["disciplinas"])
        self._payload = payload
        self.result_label.setText(
            f"Ficha válida: {contest['nome']} · {discipline_count} disciplina(s) · "
            f"{topic_count} tópico(s)."
        )
        self.accept()

    def payload(self) -> dict[str, Any]:
        if self._payload is None:
            raise RuntimeError("A ficha precisa ser validada antes de ser utilizada.")
        return self._payload


class PromptDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Prompts — extração de informações de editais")
        self.setMinimumSize(760, 620)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Anexe o edital em PDF ou imagens à ferramenta de IA, cole o prompt abaixo "
            "e solicite a extração. A IA deve devolver somente JSON compatível com o sistema."
        )
        intro.setObjectName("MutedText")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.editor = QPlainTextEdit()
        self.editor.setObjectName("CodeEditor")
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.editor.setPlainText(PROMPT_EXTRACAO_CONCURSO)
        layout.addWidget(self.editor, 1)

        footer = QHBoxLayout()
        copy_button = QPushButton("Copiar prompt")
        copy_button.setObjectName("PrimaryButton")
        copy_button.clicked.connect(self._copy_prompt)
        footer.addWidget(copy_button)
        footer.addStretch()
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

    def _copy_prompt(self) -> None:
        QGuiApplication.clipboard().setText(PROMPT_EXTRACAO_CONCURSO)
        QMessageBox.information(self, "Prompt copiado", "O prompt foi copiado para a área de transferência.")
