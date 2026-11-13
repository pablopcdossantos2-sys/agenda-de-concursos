APP_STYLE = """
QWidget {
    background: #F5F7FB;
    color: #202B3C;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background: #F5F7FB; }
QFrame#Sidebar { background: #17243A; border: none; }
QLabel#Brand { color: #FFFFFF; font-size: 17pt; font-weight: 700; padding: 8px 4px 18px; }
QLabel#BrandSub { color: #9EADC3; font-size: 8pt; padding-left: 5px; }
QPushButton#NavButton {
    color: #C8D3E2; background: transparent; border: none; border-radius: 9px;
    text-align: left; padding: 12px 14px; font-weight: 600;
}
QPushButton#NavButton:hover { background: #263750; color: white; }
QPushButton#NavButton:checked { background: #2D65C5; color: white; }
QLabel#PageTitle { color: #17243A; font-size: 23pt; font-weight: 700; }
QLabel#PageSubtitle { color: #718096; font-size: 9pt; }
QFrame#Panel, QFrame#MetricCard {
    background: #FFFFFF; border: 1px solid #E6EAF1; border-radius: 13px;
}
QLabel#MetricValue { color: #17243A; font-size: 23pt; font-weight: 700; }
QLabel#MetricCaption { color: #728096; font-size: 9pt; }
QPushButton {
    background: #E9EEF6; color: #29384E; border: 1px solid #DFE5EF;
    border-radius: 8px; padding: 8px 13px; font-weight: 600;
}
QPushButton:hover { background: #DDE7F5; }
QPushButton:pressed { background: #CFDCF0; }
QPushButton#PrimaryButton { background: #2864C5; color: white; border: 1px solid #2864C5; }
QPushButton#PrimaryButton:hover { background: #1F55AE; }
QPushButton#DangerButton { color: #B42318; background: #FFF1F0; border-color: #F6D1CE; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit, QPlainTextEdit {
    background: #FFFFFF; border: 1px solid #DCE3ED; border-radius: 8px;
    padding: 8px 10px; selection-background-color: #BDD5FA;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3980E8;
}
QComboBox::drop-down { border: none; width: 25px; }
QTableWidget, QTreeWidget, QListWidget {
    background: #FFFFFF; alternate-background-color: #F8FAFD;
    border: 1px solid #E6EAF1; border-radius: 10px; gridline-color: #EDF0F5;
    selection-background-color: #E7F0FF; selection-color: #193D70;
}
QHeaderView::section {
    background: #F7F9FC; color: #66758A; border: none;
    border-bottom: 1px solid #E6EAF1; padding: 10px 8px; font-weight: 700;
}
QListWidget::item, QTreeWidget::item { padding: 7px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #CFD7E3; border-radius: 4px; min-height: 25px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #17243A; color: white; border: 0; padding: 6px; }
QDialog { background: #F5F7FB; }
""" 
