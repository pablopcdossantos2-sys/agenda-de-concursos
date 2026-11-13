from __future__ import annotations

from datetime import date
from typing import Any

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QGuiApplication, QColor, QIcon

from agenda.ui.assets import asset_path
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
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))
        self.apply_theme(database.get_setting("theme", "claro"))
        self.setMinimumWidth(320)
        self.setMaximumWidth(390)
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

    def apply_theme(self, theme: str) -> None:
        self.theme = theme if theme in ("claro", "escuro") else "claro"
        if self.theme == "escuro":
            colors = {
                "background": "#101C30", "card": "#1B2B43", "border": "#3B5270",
                "text": "#F5F8FC", "muted": "#C7D3E1", "button": "#344A68",
                "button_hover": "#425D81",
            }
        else:
            colors = {
                "background": "#F4F7FC", "card": "#FFFFFF", "border": "#D4DEEA",
                "text": "#182437", "muted": "#53647A", "button": "#E8EEF6",
                "button_hover": "#D8E4F2",
            }
        self.setStyleSheet(f"""
            QWidget {{ background:{colors['background']}; color:{colors['text']}; font-family:'Segoe UI'; }}
            QFrame#Card {{ background:{colors['card']}; border:1px solid {colors['border']}; border-radius:10px; }}
            QLabel#Title {{ color:{colors['text']}; font-size:12pt; font-weight:700; }}
            QLabel#Sub {{ color:{colors['muted']}; font-size:8pt; }}
            QLabel#Contest {{ color:{colors['text']}; font-weight:600; }}
            QLabel#Date {{ color:{colors['muted']}; font-size:8pt; }}
            QPushButton {{ background:{colors['button']}; border:1px solid {colors['border']}; color:{colors['text']}; padding:6px 10px; border-radius:6px; }}
            QPushButton:hover {{ background:{colors['button_hover']}; }}
            QListWidget {{ border:0; background:transparent; color:{colors['text']}; }}
            QListWidget::item {{ border:0; padding:3px; }}
            QToolTip {{ background:#0D1B32; color:#FFFFFF; border:1px solid #42536B; padding:6px; }}
        """)

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

    def _status_color(self, status: str) -> str:
        if self.theme == "escuro":
            return {
                "Previsto": "#F6CD83",
                "Edital publicado": "#9BE2BE",
                "Sem Previsão": "#D0D9E5",
            }.get(status, "#F5F8FC")
        return {
            "Previsto": "#925100",
            "Edital publicado": "#116B4A",
            "Sem Previsão": "#516174",
        }.get(status, "#182437")

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
            item.setForeground(QColor(self._status_color(status)))
            item.setToolTip(f"{contest.get('orgao','')} — {contest.get('cargo','')}")
            item.setSizeHint(QSize(340, 56))
            self.items.addItem(item)
        if not visible:
            self.items.addItem(QListWidgetItem("Nenhum concurso com data cadastrada."))
        self.count_label.setText(f"Exibindo {len(visible)} de {len(eligible)} concursos futuros ou sem data")
        self.adjustSize()
