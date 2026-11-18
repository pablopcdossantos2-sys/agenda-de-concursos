from __future__ import annotations

from html import escape

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from agenda.services.cargos import format_cargo_salary
from agenda.services.dates import format_date_input, format_date_pt_br


class ContestCard(QFrame):
    """Card clicável com hierarquia visual e textos ajustados ao espaço."""

    clicked = Signal(int)

    def __init__(self, contest: dict, compact: bool = False, parent=None):
        super().__init__(parent)
        self.contest_id = int(contest["id"])
        self._contest = dict(contest)
        self._elided_labels: list[tuple[QLabel, str]] = []
        self.setObjectName("ContestCard")
        self.setProperty("compact", "true" if compact else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Abrir ficha do concurso {contest.get('nome', 'Concurso')}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        name = str(contest.get("nome") or "Concurso sem nome")
        self.title_label = self._label(name, "ContestCardTitle", elide=True)
        title_row.addWidget(self.title_label, 1)

        self.status_label = self._label(str(contest.get("status") or "Sem Previsão"), "ContestCardStatus")
        self.status_label.setWordWrap(False)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_row.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        cargos = contest.get("cargos") or []
        if compact:
            lines = []
            for key, caption in (
                ("inscricoes_inicio", "Início das inscrições"),
                ("inscricoes_fim", "Fim das inscrições"),
                ("data_prova", "Data da prova"),
            ):
                value = format_date_input(contest.get(key))
                line = f"{caption}: {value or 'Não informada'}"
                layout.addWidget(self._label(line, "ContestCardMeta"))
                lines.append(line)
            roles = [
                f"{cargo['nome']} · {format_cargo_salary(cargo)}"
                for cargo in cargos if cargo.get("interesse")
            ]
            if roles:
                layout.addSpacing(4)
                for role in roles:
                    layout.addWidget(self._label(role, "ContestCardInterest"))
            else:
                layout.addWidget(self._label("Nenhum cargo marcado como de interesse", "ContestCardMeta"))
            tooltip_parts = [name, *lines, *roles]
        else:
            description = self._description()
            dates = self._date_label(contest)
            layout.addWidget(self._label(description, "ContestCardDescription", elide=True))
            layout.addWidget(self._label(dates, "ContestCardMeta", elide=True))
            tooltip_parts = [
                name, description, dates,
                *(f"{cargo['nome']} · {format_cargo_salary(cargo)}" for cargo in cargos),
            ]
            self.setFixedHeight(104)
        tooltip = "<br>".join(escape(part).replace("\n", "<br>") for part in tooltip_parts)
        self.setToolTip(f"<qt>{tooltip}</qt>")

    def _label(self, text: str, name: str, *, elide: bool = False) -> QLabel:
        label = QLabel(text)
        label.setObjectName(name)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(not elide)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        if elide:
            label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            self._elided_labels.append((label, text))
        return label

    @staticmethod
    def _date_label(contest: dict) -> str:
        start = contest.get("inscricoes_inicio") or ""
        end = contest.get("inscricoes_fim") or ""
        exam = contest.get("data_prova") or ""
        if exam:
            event = f"Prova: {format_date_pt_br(exam)}"
        else:
            event = "Data da prova não informada"
        if start or end:
            registration = (
                f"Inscrições: {format_date_pt_br(start) if start else '—'} "
                f"a {format_date_pt_br(end) if end else '—'}"
            )
            return f"{event}  |  {registration}"
        return event

    def _description(self) -> str:
        contest = self._contest
        parts = []
        organ = str(contest.get("orgao") or "").strip()
        if organ:
            parts.append(organ)

        cargos = contest.get("cargos") or []
        roles = [str(item.get("nome") or "").strip() for item in cargos if item.get("nome")]
        legacy_role = str(contest.get("cargo") or "").strip()
        role = ", ".join(roles[:2]) if roles else legacy_role
        if role:
            parts.append(role if len(roles) <= 2 else f"{role} e outros {len(roles) - 2}")

        bank = str(contest.get("banca") or "").strip()
        if bank:
            parts.append(f"Banca: {bank}")
        return "  •  ".join(parts) or "Órgão e cargo não informados"

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.layout().activate()
        for label, text in self._elided_labels:
            label.setText(QFontMetrics(label.font()).elidedText(
                text, Qt.TextElideMode.ElideRight, label.width()
            ))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus(Qt.FocusReason.MouseFocusReason)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit(self.contest_id)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit(self.contest_id)
            event.accept()
            return
        super().keyPressEvent(event)
