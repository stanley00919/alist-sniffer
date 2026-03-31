# Dark theme (Catppuccin Mocha inspired)
COLORS = {
    'bg':           '#1E1E2E',
    'surface':      '#181825',
    'surface2':     '#313244',
    'primary':      '#6C5CE7',
    'primary_hover':'#A29BFE',
    'accent':       '#00CEC9',
    'success':      '#00B894',
    'warning':      '#FDCB6E',
    'error':        '#E17055',
    'text':         '#CDD6F4',
    'text_muted':   '#A6ADC8',
    'border':       '#313244',
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
}}
QWidget {{
    background-color: {COLORS['bg']};
    color: {COLORS['text']};
    font-family: 'Segoe UI', Arial, sans-serif;
}}
QLineEdit {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 14px;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['primary']};
}}
QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['text']};
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 14px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}
QPushButton:pressed {{
    background-color: {COLORS['surface2']};
}}
QPushButton:disabled {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text_muted']};
}}
QPushButton#btn_secondary {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text']};
}}
QPushButton#btn_secondary:hover {{
    background-color: {COLORS['border']};
}}
QPushButton#btn_danger {{
    background-color: {COLORS['error']};
}}
QListWidget, QTreeWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    color: {COLORS['text']};
    outline: 0;
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text']};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {COLORS['surface2']};
}}
QProgressBar {{
    background-color: {COLORS['surface2']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['primary']}, stop:1 {COLORS['accent']});
    border-radius: 4px;
}}
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['surface']};
}}
QTabBar::tab {{
    background-color: {COLORS['surface2']};
    color: {COLORS['text_muted']};
    padding: 8px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {COLORS['primary']};
    color: {COLORS['text']};
}}
QScrollBar:vertical {{
    background: {COLORS['surface']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['surface2']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {COLORS['surface']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['surface2']};
    border-radius: 4px;
    min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollArea {{
    background-color: {COLORS['bg']};
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: {COLORS['bg']};
}}
QLabel {{
    color: {COLORS['text']};
}}
QLabel#label_muted {{
    color: {COLORS['text_muted']};
    font-size: 12px;
}}
QCheckBox {{
    color: {COLORS['text']};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS['border']};
    border-radius: 3px;
    background-color: {COLORS['surface']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}
QComboBox {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
QSpinBox {{
    background-color: {COLORS['surface']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
QStatusBar {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_muted']};
    font-size: 12px;
}}
"""
