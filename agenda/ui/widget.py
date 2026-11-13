from __future__ import annotations

from datetime import date
from typing import Any

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QPushButton


STATUS_COLORS = {
    "Previsto": "#D97706",
    "Edital publicado": "#16835D",
    "Sem Previsão": "#64748B",
}


class DesktopWidget(QWidget):
    """Widget compacto destacável; permanece acessível enquanto estiver visível."""

    def __init__(self, database, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.database = database
        self.item_limit = int(database.get_setting("widget_items", "5") or 5)
        self._drag_offset: QPoint | None = None
        self._positioned = False
        self.setWindowTitle("Agenda de Concursos")
        self.setMinimumWidth(320)
        self.setMaximumWidth(390)
        self.setStyleSheet("""
            QWidget { background:#17243A; color:#F4F7FC; font-family:'Segoe UI'; }
            QFrame#Card { background:#22344F; border:1px solid #314764; border-radius:10px; }
            QLabel#Title { color:#FFFFFF; font-size:12pt; font-weight:700; }
            QLabel#Sub { color:#A9B8CD; font-size:8pt; }
            QLabel#Contest { color:#F7F9FC; font-weight:600; }
            QLabel#Date { color:#B9C8DA; font-size:8pt; }
            QPushButton { background:#2B4161; border:0; color:#EAF1FA; padding:5px 9px; border-radius:6px; }
            QPushButton:hover { background:#3A567D; }
            QListWidget { border:0; background:transparent; }
            QListWidget::item { border:0; padding:3px; }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(15, 13, 15, 13)
        top = QVBoxLayout()
        title_row = QVBoxLayout()
        title = QLabel("PRÓXIMOS CONCURSOS")
        title.setObjectName("Title")
        subtitle = QLabel("Sua agenda de oportunidades")
        subtitle.setObjectName("Sub")
        title_row.addWidget(title)
        title_row.addWidget(subtitle)
        root.addLayout(title_row)
        self.items = QListWidget()
        self.items.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        root.addWidget(self.items)
        footer = QVBoxLayout()
        self.count_label = QLabel("")
        self.count_label.setObjectName("Sub")
        footer.addWidget(self.count_label)
        close = QPushButton("Ocultar widget")
        close.clicked.connect(self.hide)
        footer.addWidget(close)
        root.addLayout(footer)
        self.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._positioned:
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                self.move(area.right() - self.width() - 22, area.top() + 22)
            self._positioned = True

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def set_item_limit(self, limit: int) -> None:
        self.item_limit = max(1, min(20, int(limit)))
        self.refresh()

    def refresh(self) -> None:
        self.items.clear()
        contests = self.database.list_contests()
        today_iso = date.today().isoformat()
        eligible = []
        for item in contests:
            event_date = item.get("data_prova") or item.get("data_prevista") or ""
            if not event_date or event_date >= today_iso:
                eligible.append(item)
        eligible.sort(key=lambda item: item.get("data_prova") or item.get("data_prevista") or "9999-12-31")
        visible = eligible[:self.item_limit]
        today = date.today()
        for contest in visible:
            event_date = contest.get("data_prova") or contest.get("data_prevista") or ""
            date_label = event_date or "Data ainda não informada"
            try:
                parsed = date.fromisoformat(event_date)
                delta = (parsed - today).days
                if delta == 0:
                    date_label = "Hoje"
                elif delta > 0:
                    date_label = f"Em {delta} dias · {event_date}"
                else:
                    date_label = f"Data passada · {event_date}"
            except ValueError:
                pass
            status = contest.get("status") or "Sem Previsão"
            text = f"{contest.get('nome', 'Concurso')}\n{date_label}  •  {status}"
            item = QListWidgetItem(text)
            item.setToolTip(f"{contest.get('orgao','')} — {contest.get('cargo','')}")
            item.setSizeHint(QSize(340, 56))
            self.items.addItem(item)
        if not visible:
            self.items.addItem(QListWidgetItem("Nenhum concurso com data cadastrada."))
        self.count_label.setText(f"Exibindo {len(visible)} de {len(eligible)} concursos futuros ou sem data")
        self.adjustSize()
