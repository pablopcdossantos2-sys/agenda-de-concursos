from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class ContestCard(QFrame):
    """Card compacto, clicável e com textos limitados ao espaço disponível."""

    clicked = Signal(int)

    def __init__(self, contest: dict, compact: bool = False, parent=None):
        super().__init__(parent)
        self.contest_id = int(contest["id"])
        self.compact = compact
        self.setObjectName("ContestCard")
        self.setProperty("compact", "true" if compact else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName(f"Abrir ficha do concurso {contest.get('nome', 'Concurso')}")
        self.setToolTip("Clique para abrir a ficha completa deste concurso.")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(3)

        self.title_label = QLabel()
        self.title_label.setObjectName("ContestCardTitle")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.title_label)

        self.description_label = QLabel()
        self.description_label.setObjectName("ContestCardDescription")
        self.description_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.description_label)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 1, 0, 0)
        footer.setSpacing(8)

        self.date_label = QLabel()
        self.date_label.setObjectName("ContestCardMeta")
        self.date_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        footer.addWidget(self.date_label, 1)

        self.status_label = QLabel()
        self.status_label.setObjectName("ContestCardStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        footer.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(footer)

        self._contest = dict(contest)
        self._update_text()

    @staticmethod
    def _date_label(contest: dict) -> str:
        start = contest.get("inscricoes_inicio") or ""
        end = contest.get("inscricoes_fim") or ""
        exam = contest.get("data_prova") or ""
        predicted = contest.get("data_prevista") or ""
        if exam:
            event = f"Prova: {exam}"
        elif predicted:
            event = f"Previsão: {predicted}"
        else:
            event = "Data ainda não informada"
        if start or end:
            registration = f"Inscrições: {start or '—'} a {end or '—'}"
            return f"{event} · {registration}"
        return event

    def _update_text(self) -> None:
        contest = self._contest
        name = str(contest.get("nome") or "Concurso sem nome")
        organ = str(contest.get("orgao") or "Órgão não informado")
        role = str(contest.get("cargo") or "")
        bank = str(contest.get("banca") or "")
        locality = str(contest.get("localidade") or "")
        description_parts = [organ]
        if role:
            description_parts.append(role)
        if bank:
            description_parts.append(f"Banca: {bank}")
        if locality and not self.compact:
            description_parts.append(locality)

        self.title_label.setText(name)
        self.description_label.setText(" · ".join(description_parts))
        self.date_label.setText(self._date_label(contest))
        status = str(contest.get("status") or "Sem Previsão")
        self.status_label.setText(status)
        self.setToolTip(
            f"{name}\n{organ}\n{role}\n{bank}\n{locality}\n"
            f"{self._date_label(contest)}\nSituação: {status}"
        )
        if self.compact:
            self.setFixedHeight(78)
        else:
            self.setMinimumHeight(94)
            self.setMaximumHeight(112)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        metrics = QFontMetrics(self.title_label.font())
        self.title_label.setText(
            metrics.elidedText(str(self._contest.get("nome") or "Concurso sem nome"),
                               Qt.TextElideMode.ElideRight, max(20, self.title_label.width()))
        )
        description = self.description_label.toolTip()
        full_description = " · ".join(
            item for item in [
                str(self._contest.get("orgao") or "Órgão não informado"),
                str(self._contest.get("cargo") or ""),
                f"Banca: {self._contest.get('banca')}" if self._contest.get("banca") else "",
                str(self._contest.get("localidade") or "") if not self.compact else "",
            ] if item
        )
        self.description_label.setToolTip(full_description)
        self.description_label.setText(
            QFontMetrics(self.description_label.font()).elidedText(
                full_description, Qt.TextElideMode.ElideRight,
                max(20, self.description_label.width())
            )
        )
        self.date_label.setText(
            QFontMetrics(self.date_label.font()).elidedText(
                self._date_label(self._contest), Qt.TextElideMode.ElideRight,
                max(20, self.date_label.width())
            )
        )

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
