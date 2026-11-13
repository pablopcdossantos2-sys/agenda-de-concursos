THEMES = {
    "claro": {
        "background": "#F3F6FA",
        "text": "#182437",
        "muted": "#53647A",
        "sidebar": "#17243A",
        "sidebar_text": "#D6E0EF",
        "panel": "#FFFFFF",
        "border": "#D6DEE8",
        "input": "#FFFFFF",
        "secondary": "#E8EEF6",
        "secondary_hover": "#DBE5F2",
        "selection": "#E1EDFF",
        "selection_text": "#153B70",
        "code_bg": "#101C30",
        "code_text": "#F5F8FF",
        "danger_bg": "#FFF1F0",
        "danger_text": "#B42318",
        "danger_border": "#F2C8C4",
    },
    "escuro": {
        "background": "#111827",
        "text": "#F3F4F6",
        "muted": "#C0CBD8",
        "sidebar": "#0C1423",
        "sidebar_text": "#DCE5F0",
        "panel": "#1F2937",
        "border": "#3B4758",
        "input": "#111C2C",
        "secondary": "#344256",
        "secondary_hover": "#43536B",
        "selection": "#27446E",
        "selection_text": "#FFFFFF",
        "code_bg": "#0B1220",
        "code_text": "#EDF3FB",
        "danger_bg": "#492C2A",
        "danger_text": "#FFB4AB",
        "danger_border": "#75413D",
    },
}


def theme_stylesheet(theme: str = "claro") -> str:
    """Retorna uma folha de estilos com contraste explícito para o tema escolhido."""
    colors = THEMES.get(theme, THEMES["claro"])
    c = colors
    return f"""
    QWidget {{
        background: {c['background']};
        color: {c['text']};
        font-family: "Segoe UI";
        font-size: 10pt;
    }}
    QMainWindow, QDialog {{ background: {c['background']}; }}
    QFrame#Sidebar {{ background: {c['sidebar']}; border: none; }}
    QLabel#Brand {{ color: #FFFFFF; font-size: 17pt; font-weight: 700; padding: 8px 4px 18px; }}
    QLabel#BrandSub {{ color: #B8C8DC; font-size: 8pt; padding-left: 5px; }}
    QPushButton#NavButton {{
        color: {c['sidebar_text']}; background: transparent; border: none;
        border-radius: 9px; text-align: left; padding: 12px 14px; font-weight: 600;
    }}
    QPushButton#NavButton:hover {{ background: #2A3D58; color: #FFFFFF; }}
    QPushButton#NavButton:checked {{ background: #2864C5; color: #FFFFFF; }}
    QLabel#PageTitle {{ color: {c['text']}; font-size: 23pt; font-weight: 700; }}
    QLabel#PageSubtitle, QLabel#MutedText, QLabel#HintText {{ color: {c['muted']}; }}
    QLabel#PageSubtitle {{ font-size: 9pt; }}
    QLabel#HintText {{ font-size: 8pt; }}
    QLabel#PanelTitle {{ color: {c['text']}; font-size: 12pt; font-weight: 700; }}
    QLabel#MetricValue {{ color: {c['text']}; font-size: 23pt; font-weight: 700; }}
    QLabel#MetricCaption {{ color: {c['muted']}; font-size: 9pt; }}
    QLabel#CompareScore {{ color: #4D8DF0; font-size: 17pt; font-weight: 700; }}
    QFrame#Panel, QFrame#MetricCard {{
        background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 13px;
    }}
    QPushButton {{
        background: {c['secondary']}; color: {c['text']}; border: 1px solid {c['border']};
        border-radius: 8px; padding: 8px 13px; font-weight: 600;
    }}
    QPushButton:hover {{ background: {c['secondary_hover']}; }}
    QPushButton:pressed {{ background: {c['selection']}; }}
    QPushButton:disabled {{ color: {c['muted']}; background: {c['background']}; }}
    QPushButton#PrimaryButton {{
        background: #2864C5; color: #FFFFFF; border: 1px solid #2864C5;
    }}
    QPushButton#PrimaryButton:hover {{ background: #1F55AE; }}
    QPushButton#DangerButton {{
        color: {c['danger_text']}; background: {c['danger_bg']}; border: 1px solid {c['danger_border']};
    }}
    QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {{
        background: {c['input']}; color: {c['text']}; border: 1px solid {c['border']};
        border-radius: 8px; padding: 8px 10px; selection-background-color: #2864C5;
        selection-color: #FFFFFF;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus,
    QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid #4D8DF0; }}
    QComboBox::drop-down {{ border: none; width: 25px; }}
    QTableWidget, QTreeWidget, QListWidget {{
        background: {c['panel']}; color: {c['text']};
        alternate-background-color: {c['background']}; border: 1px solid {c['border']};
        border-radius: 10px; gridline-color: {c['border']};
        selection-background-color: {c['selection']}; selection-color: {c['selection_text']};
    }}
    QHeaderView::section {{
        background: {c['secondary']}; color: {c['text']}; border: none;
        border-bottom: 1px solid {c['border']}; padding: 10px 8px; font-weight: 700;
    }}
    QListWidget::item, QTreeWidget::item {{ padding: 7px; }}
    QCheckBox {{ color: {c['text']}; spacing: 8px; }}
    QCheckBox::indicator {{ width: 17px; height: 17px; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {c['muted']}; border-radius: 4px; min-height: 25px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QToolTip {{ background: #0D1B32; color: #FFFFFF; border: 1px solid #42536B; padding: 6px; }}
    QToolBar {{
        background: {c['panel']}; color: {c['text']}; border: none;
        border-bottom: 1px solid {c['border']}; spacing: 8px; padding: 6px 12px;
    }}
    QToolBar QToolButton {{
        color: {c['text']}; background: transparent; border: 1px solid transparent;
        border-radius: 7px; padding: 7px 10px; font-weight: 600;
    }}
    QToolBar QToolButton:hover {{ background: {c['secondary']}; border-color: {c['border']}; }}
    QToolBar::separator {{ background: {c['border']}; width: 1px; margin: 4px 7px; }}
    QPlainTextEdit#CodeEditor {{
        background: {c['code_bg']}; color: {c['code_text']}; border: 1px solid {c['border']};
        border-radius: 9px; font-family: Consolas, "Cascadia Code", monospace; font-size: 9pt;
    }}
    """


APP_STYLE = theme_stylesheet("claro")
