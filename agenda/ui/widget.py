from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QScrollArea, QVBoxLayout, QWidget

from agenda.ui.assets import asset_path
from agenda.ui.cards import ContestCard
from agenda.ui.styles import THEMES


class DesktopWidget(QWidget):
    """Widget flutuante com a agenda dos próximos concursos."""

    contest_selected = Signal(int)

    def __init__(self, database, parent=None):
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.database = database
        self._drag_offset: QPoint | None = None
        self._positioned = False

        self.setObjectName("DesktopWidgetRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("Agenda de Concursos")
        self.setWindowIcon(QIcon(str(asset_path("app_icon.svg"))))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(1, 1, 1, 1)
        outer.setSpacing(0)

        shell = QFrame(self)
        shell.setObjectName("WidgetShell")
        outer.addWidget(shell)
        root = QVBoxLayout(shell)
        root.setContentsMargins(14, 12, 14, 11)
        root.setSpacing(8)

        header = QFrame()
        header.setObjectName("WidgetHeader")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(2, 0, 2, 4)
        header_layout.setSpacing(2)

        title = QLabel("PRÓXIMOS CONCURSOS")
        title.setObjectName("WidgetTitle")
        title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        subtitle = QLabel("Datas de prova e oportunidades em aberto")
        subtitle.setObjectName("WidgetSubtitle")
        subtitle.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        root.addWidget(header)

        self.cards_host = QWidget()
        self.cards_host.setObjectName("WidgetCardsHost")
        self.cards_layout = QVBoxLayout(self.cards_host)
        self.cards_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(7)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.setAccessibleName("Próximos concursos")
        self.cards_scroll.setWidget(self.cards_host)
        root.addWidget(self.cards_scroll, 1)

        footer = QFrame()
        footer.setObjectName("WidgetFooter")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(2, 3, 2, 0)
        self.count_label = QLabel("")
        self.count_label.setObjectName("WidgetSubtitle")
        self.count_label.setWordWrap(True)
        footer_layout.addWidget(self.count_label, 1)
        root.addWidget(footer)

        self.apply_theme(database.get_setting("theme", "claro"))
        self.load_preferences()

    def load_preferences(self) -> None:
        self.item_limit = self._setting_int("widget_items", 5, 1, 20)
        self.set_dimensions(
            self._setting_int("widget_width", 390, 320, 700),
            self._setting_int("widget_height", 470, 300, 900),
        )

    def _setting_int(self, key: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(self.database.get_setting(key, str(default)) or default)
        except (TypeError, ValueError):
            value = default
        return max(minimum, min(maximum, value))

    def apply_theme(self, theme: str) -> None:
        self.theme = theme if theme in ("claro", "escuro") else "claro"
        c = THEMES[self.theme]
        self.setStyleSheet(f"""
            QWidget#DesktopWidgetRoot {{ background:transparent; border:none; }}
            QFrame#WidgetShell {{
                background:{c['background']}; color:{c['text']};
                border:1px solid {c['border']}; border-radius:16px;
            }}
            QFrame#WidgetHeader, QFrame#WidgetFooter {{ background:transparent; border:none; }}
            QWidget#WidgetCardsHost {{ background:transparent; border:none; }}
            QLabel#WidgetTitle {{ background:transparent; color:{c['text']}; font-size:12pt; font-weight:800; }}
            QLabel#WidgetSubtitle {{ background:transparent; color:{c['muted']}; font-size:8pt; }}
            QFrame#ContestCard {{ background:{c['panel']}; border:1px solid {c['border']}; border-radius:10px; }}
            QFrame#ContestCard:hover, QFrame#ContestCard:focus {{
                background:{c['card_hover']}; border:1px solid #4D8DF0;
            }}
            QLabel#ContestCardTitle {{ background:transparent; color:{c['text']}; font-weight:700; font-size:9pt; }}
            QLabel#ContestCardDescription, QLabel#ContestCardMeta {{
                background:transparent; color:{c['text']}; font-size:9pt; }}
            QLabel#ContestCardInterest {{
                background:transparent; color:{c['chip_text']}; font-size:9pt; font-weight:700; }}
            QLabel#ContestCardStatus {{ background:{c['chip_bg']}; color:{c['chip_text']};
                border:1px solid {c['border']}; border-radius:7px; padding:1px 6px;
                font-size:7pt; font-weight:700; }}
            QToolTip {{ background:#0D1B32; color:#FFFFFF; border:1px solid #42536B; padding:6px; }}
        """)
        self.update()

    def set_dimensions(self, width: int, height: int) -> None:
        self.widget_width = max(320, min(700, int(width)))
        self.widget_height = max(300, min(900, int(height)))
        self.setFixedSize(self.widget_width, self.widget_height)
        if hasattr(self, "cards_layout"):
            self.refresh()

    def set_item_limit(self, limit: int) -> None:
        self.item_limit = max(1, min(20, int(limit)))
        self.refresh()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._positioned:
            screen = self.screen() or QGuiApplication.primaryScreen()
            if screen is not None:
                area = screen.availableGeometry()
                x = max(area.left() + 12, area.right() - self.width() - 22)
                y = max(area.top() + 12, area.top() + 22)
                self.move(x, y)
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

    def _clear_cards(self) -> None:
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()

    def refresh(self) -> None:
        if not hasattr(self, "cards_layout"):
            return
        self._clear_cards()
        contests = self.database.list_contests()
        today = date.today().isoformat()
        eligible = []
        for item in contests:
            event_date = item.get("data_prova") or ""
            if not event_date or event_date >= today:
                eligible.append(item)

        visible = eligible[:self.item_limit]

        for contest in visible:
            contest["cargos"] = self.database.list_cargos(int(contest["id"]))
            card = ContestCard(contest, compact=True, parent=self.cards_host)
            card.clicked.connect(self.contest_selected.emit)
            self.cards_layout.addWidget(card)
            card.show()

        if not eligible:
            empty = QLabel("Nenhum concurso futuro ou sem data de prova cadastrado.")
            empty.setObjectName("WidgetSubtitle")
            empty.setWordWrap(True)
            self.cards_layout.addWidget(empty)
            empty.show()

        omitted = max(0, len(eligible) - len(visible))
        if omitted:
            self.count_label.setText(f"Exibindo {len(visible)} de {len(eligible)} concursos.")
        elif len(visible) == 1:
            self.count_label.setText("1 concurso exibido")
        else:
            self.count_label.setText(f"{len(visible)} concursos exibidos")
