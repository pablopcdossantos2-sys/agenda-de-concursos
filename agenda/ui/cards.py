from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from agenda.services.dates import format_date_pt_br


class ContestCard(QFrame):
    """Card clicável com hierarquia visual e textos ajustados ao espaço."""

    clicked = Signal(int)

    def __init__(self, contest: dict, compact: bool = False, parent=None):
        super().__init__(parent)
        self.contest_id = int(contest["id"])
        self.compact = compact
        self._contest = dict(contest)
        self.setObjectName("ContestCard")
        self.setProperty("compact", "true" if compact else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Abrir ficha do concurso {contest.get('nome', 'Concurso')}")
        self.setToolTip("Clique para abrir a ficha completa deste concurso.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(8)
        self.title_label = QLabel()
        self.title_label.setObjectName("ContestCardTitle")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title_row.addWidget(self.title_label, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("ContestCardStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title_row.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        self.description_label = QLabel()
        self.description_label.setObjectName("ContestCardDescription")
        self.description_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.description_label.setWordWrap(False)
        layout.addWidget(self.description_label)

        self.date_label = QLabel()
        self.date_label.setObjectName("ContestCardMeta")
        self.date_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.date_label.setWordWrap(False)
        layout.addWidget(self.date_label)
        self._update_text()

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

    def _update_text(self) -> None:
        name = str(self._contest.get("nome") or "Concurso sem nome")
        self.title_label.setText(name)
        self.status_label.setText(str(self._contest.get("status") or "Sem Previsão"))
        self.description_label.setText(self._description())
        self.date_label.setText(self._date_label(self._contest))
        cargo_tooltip = "\n".join(
            f"{item.get('nome', '')} — {item.get('salario_inicial') or 'Remuneração não informada'}"
            for item in (self._contest.get("cargos") or [])
        )
        self.setToolTip(
            f"{name}\n{self._description()}\n{self._date_label(self._contest)}\n"
            f"{'Cargos e salários:\\n' + cargo_tooltip if cargo_tooltip else ''}\n"
            "Clique para abrir a ficha completa."
        )
        self.setFixedHeight(88 if self.compact else 104)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.title_label.setText(
            QFontMetrics(self.title_label.font()).elidedText(
                str(self._contest.get("nome") or "Concurso sem nome"),
                Qt.TextElideMode.ElideRight, max(20, self.title_label.width())
            )
        )
        self.description_label.setText(
            QFontMetrics(self.description_label.font()).elidedText(
                self._description(), Qt.TextElideMode.ElideRight,
                max(20, self.description_label.width())
            )
        )
        self.date_label.setText(
            QFontMetrics(self.date_label.font()).elidedText(
                self._date_label(self._contest), Qt.TextElideMode.ElideRight,
                max(20, self.date_label.width())
            )
        )

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
