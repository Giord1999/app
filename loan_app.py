#Imports for the GUI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QListWidget, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QSplashScreen, QDialog, QPushButton, 
                             QDoubleSpinBox, QSpinBox, QScrollArea, QFormLayout, 
                             QTextEdit, QHBoxLayout, QToolButton, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QToolButton, QListWidgetItem, QSizePolicy, QScrollArea, QAction, QTabWidget, QFrame, QDateEdit, QCheckBox, QFileDialog, QGroupBox)


from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont, QPainter, QPen
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QDate


# Set the backend for matplotlib
import matplotlib
matplotlib.use('Qt5Agg')


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

#Imports for the backend
import sys
import os
import time
import numpy as np
import pandas as pd
import psycopg2
from loan import Loan, DbManager
from ai_chatbot_loan import Chatbot
from loan_crm import LoanCRM
from loan_report import LoanReport


def resource_path(relative_path):
    """Ottiene il percorso assoluto delle risorse, sia in modalità development che in eseguibile"""
    try:
        # PyInstaller crea una cartella temporanea e memorizza il percorso in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Se non siamo in un bundle PyInstaller, usa il percorso corrente
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Costruisci il percorso completo considerando la sottocartella assets
    full_path = os.path.join(base_path, 'assets', relative_path)
    
    # Verifica se il file esiste
    if not os.path.exists(full_path):
        print(f"WARN: Resource not found: {full_path}")
        # Prova a cercare direttamente nella cartella assets accanto all'eseguibile
        alternative_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', relative_path)
        if os.path.exists(alternative_path):
            return alternative_path
        else:
            print(f"ERROR: Resource not found in alternative path: {alternative_path}")
    
    return full_path

class LoanCommand:
    """"Classe per la gestione degli undo e redo delle operazioni"""
    def __init__(self, do_action, undo_action, description):
        self.do_action = do_action
        self.undo_action = undo_action
        self.description = description

    def execute(self):
        self.do_action()

    def undo(self):
        self.undo_action()

class FluentStylesheet:
    """Classe per la gestione degli stili CSS"""
    @staticmethod
    def get_base_stylesheet():
        return """
            QWidget {
                font-size: 11.5pt;
            }
            
            QMainWindow {
                background-color: #ffffff;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 11pt;
                min-width: 60px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
            }
             
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px 20px;
                font-size: 11pt;
                min-width: 60px;
            }
            
            QPushButton:hover {
                background-color: #106ebe;
            }
            
            QPushButton:pressed {
                background-color: #005a9e;
            }
            
            QPushButton:disabled {
                background-color: #cccccc;
                
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 1px solid #d0d0d0;
                border-radius: 12px;
                padding: 6px 12px;
                background-color: #ffffff;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #0078d4;
            }
            
            QComboBox::drop-down {
                border: none;
                border-radius: 0px;
            }
            
            QCheckBox {
                spacing: 8px;
            }
            
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                border-radius: 8px 8px 0 0;
                padding: 6px 12px;
            }

        """

class ThemeManager:
    """Classe per la gestione dei temi"""
    def __init__(self):
        self.current_theme = "light"
        self._themes = {
            "light": {
                "base": """
                    QWidget {
                        font-size: 12pt;
                        background-color: #ffffff;
                        color: #000000;
                    }
                """,
                "ribbon": """
                    QWidget#ribbon {
                        background-color: #f8f8f8;
                        border-bottom: 1px solid #e0e0e0;
                    }
                    
                    CollapsibleRibbonGroup {
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                    }
                    
                    /* Stile per i titoli dei gruppi */
                    CollapsibleRibbonGroup QLabel[groupTitle="true"] {
                        color: #616161;
                        font-size: 16pt;  /* Aumentato per i titoli dei gruppi */
                        font-weight: bold;
                    }
                    
                    /* Stile per i bottoni */
                    AdaptiveRibbonButton {
                        border: none;
                        border-radius: 3px;
                        background-color: transparent;
                        color: #616161;
                        font-size: 11pt;  /* Ridotto per i bottoni */
                        padding: 4px;
                    }
                    
                    AdaptiveRibbonButton:hover {
                        background-color: #f0f0f0;
                    }
                    
                    AdaptiveRibbonButton:pressed {
                        background-color: #e0e0e0;
                    }
                    
                    /* Stile per le tab */
                    QTabWidget::tab-bar {
                        font-size: 11pt;  /* Ridotto per le tab */
                    }
                    
                    QTabBar::tab {
                        font-size: 11pt;  /* Ridotto per le tab */
                        padding: 8px 16px;
                    }
                    
                    /* Altri label nel ribbon */
                    QLabel {
                        color: #616161;
                        font-size: 11pt;
                    }
                """,
                "main_area": """
                    QListWidget {
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                        font-size: 12pt;
                    }
                    
                    QListWidget::item {
                        height: 30px;
                        padding: 5px;
                    }
                    
                    QListWidget::item:selected {
                        background-color: #e5f3ff;
                        color: #000000;
                    }
                """
            },
            "dark": {
                "base": """
                    QWidget {
                        font-size: 12pt;
                        background-color: #1f1f1f;
                        color: #ffffff;
                    }
                """,
                "ribbon": """
                    QWidget#ribbon {
                        background-color: #2d2d2d;
                        border-bottom: 1px solid #3d3d3d;
                    }
                    
                    CollapsibleRibbonGroup {
                        background-color: #2d2d2d;
                        border: 1px solid #3d3d3d;
                        border-radius: 4px;
                    }
                    
                    /* Stile per i titoli dei gruppi */
                    CollapsibleRibbonGroup QLabel[groupTitle="true"] {
                        color: #ffffff;
                        font-size: 16pt;  /* Aumentato per i titoli dei gruppi */
                        font-weight: bold;
                    }
                    
                    /* Stile per i bottoni */
                    AdaptiveRibbonButton {
                        border: none;
                        border-radius: 3px;
                        background-color: transparent;
                        color: #ffffff;
                        font-size: 11pt;  /* Ridotto per i bottoni */
                        padding: 4px;
                    }
                    
                    AdaptiveRibbonButton:hover {
                        background-color: #3d3d3d;
                    }
                    
                    AdaptiveRibbonButton:pressed {
                        background-color: #4d4d4d;
                    }
                    
                    /* Stile per le tab */
                    QTabWidget::tab-bar {
                        font-size: 11pt;  /* Ridotto per le tab */
                    }
                    
                    QTabBar::tab {
                        font-size: 11pt;  /* Ridotto per le tab */
                        padding: 8px 16px;
                    }
                    
                    /* Altri label nel ribbon */
                    QLabel {
                        color: #ffffff;
                        font-size: 11pt;
                    }
                """,
                "main_area": """
                    QListWidget {
                        background-color: #2d2d2d;
                        border: 1px solid #3d3d3d;
                        border-radius: 4px;
                        font-size: 12pt;
                    }
                    
                    QListWidget::item {
                        height: 30px;
                        padding: 5px;
                    }
                    
                    QListWidget::item:selected {
                        background-color: #0078d4;
                        color: #ffffff;
                    }
                """
            }
        }

    def get_stylesheet(self, theme_name=None):
        """Restituisce il foglio di stile per il tema corrente"""
        theme = theme_name or self.current_theme
        theme_dict = self._themes[theme]
        return "\n".join(theme_dict.values())

    def toggle_theme(self):
        
        """Cambia il tema corrente tra chiaro e scuro"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        return self.get_stylesheet()

    def get_current_theme(self):
        """Restituisce il nome del tema corrente"""
        return self.current_theme

    def apply_theme_to_widget(self, widget, widget_type):
        """Applica stili specifici per tipo di widget"""
        theme = self._themes[self.current_theme]
        if widget_type in theme:
            widget.setStyleSheet(theme[widget_type])

class CollapsibleRibbonGroup(QWidget):
    """Classe per la gestione dei gruppi espandibili"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.is_expanded = True
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(1)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        
        # Header
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(2, 2, 2, 2)
        
        # Title label
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #616161;
                font-size: 11.5pt;
                font-weight: bold;
            }
        """)
        
        # Toggle button
        self.toggle_button = QToolButton()
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.clicked.connect(self.toggle_content)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                background: transparent;
            }
        """)
        
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.toggle_button)
        
        # Content container
        self.content = QWidget()
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setSpacing(4)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add header and content to main layout
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content)
        
        # Style
        self.setStyleSheet("""
            CollapsibleRibbonGroup {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

    def toggle_content(self):
        
        self.is_expanded = not self.is_expanded
        self.content.setVisible(self.is_expanded)
        self.toggle_button.setArrowType(Qt.DownArrow if self.is_expanded else Qt.RightArrow)
        self.adjustSize()

    def add_button(self, button):
        self.content_layout.addWidget(button)

class AdaptiveRibbonTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll area for horizontal scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container for groups
        self.groups_container = QWidget()
        self.groups_layout = QHBoxLayout(self.groups_container)
        self.groups_layout.setSpacing(2)
        self.groups_layout.setContentsMargins(2, 2, 2, 2)
        
        self.scroll_area.setWidget(self.groups_container)
        self.layout.addWidget(self.scroll_area)

    def add_group(self, group):
        self.groups_layout.addWidget(group)

class AdaptiveRibbonButton(QToolButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(icon_path))
        
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(24, 24))
        
        # Make the button adapt to available space
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.setMinimumWidth(48)
        self.setMaximumHeight(60)
        
        self.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 3px;
                background-color: transparent;
                color: #616161;
                font-size: 10px;
                padding: 2px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
        """)

class FluentRibbonTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.groups_container = QWidget()
        self.groups_layout = QHBoxLayout(self.groups_container)
        self.groups_layout.setSpacing(2)
        self.groups_layout.setContentsMargins(2, 2, 2, 2)
        
        self.layout.addWidget(self.groups_container)

class FluentRibbonGroup(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(4, 4, 4, 4)
        
        self.setStyleSheet("""
            FluentRibbonGroup {
                background-color: #ffffff;
                border: none;
                border-radius: 4px;
            }
        """)
        
        self.buttons_widget = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_widget)
        self.buttons_layout.setSpacing(4)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #616161;
                font-size: 11px;
                padding-top: 4px;
            }
        """)
        
        self.layout.addWidget(self.buttons_widget)
        self.layout.addWidget(self.title_label)

class FluentRibbonButton(QToolButton):
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        if icon_path:
            self.setIcon(QIcon(resource_path(icon_path)))
        
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setIconSize(QSize(32, 32))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumSize(QSize(60, 60))
        
        self.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 4px;
                background-color: transparent;
                color: #616161;
                font-size: 11px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #f0f0f0;
            }
            QToolButton:pressed {
                background-color: #e0e0e0;
            }
        """)

class FluentDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(FluentStylesheet.get_base_stylesheet())
        
        # Imposta layout principale
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Contenitore per i pulsanti
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Aggiungi il contenitore dei pulsanti al layout principale
        self.main_layout.addWidget(self.button_container)


class LoginDialog(QDialog):
    """ Apre la finestra di login """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LoanManager Pro - Login")
        
        # Icona e dimensioni della finestra
        self.setWindowIcon(QIcon(resource_path('loan_icon.ico')))
        self.setFixedSize(400, 500)
        
        # Memorizza i parametri di accesso se corretti
        self.db_params = None  
        
        # Inizializza l'interfaccia
        self.init_ui()     

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout per i campi di input
        form_layout = QFormLayout()
        
        # Campi di input con valori predefiniti per host, porta e database
        self.host_input = QLineEdit("localhost")
        self.port_input = QLineEdit("5432")
        self.db_name_input = QLineEdit("loanmanager")
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        # Aggiunta dei campi al layout del form
        form_layout.addRow("Host:", self.host_input)
        form_layout.addRow("Porta:", self.port_input)
        form_layout.addRow("Nome Database:", self.db_name_input)
        form_layout.addRow("Utente:", self.user_input)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Pulsante di login
        self.login_button = QPushButton("Accedi")
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)

        # Icona utente
        image_label = QLabel(self)
        pixmap = QPixmap(resource_path('user.png'))
        pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

    def handle_login(self):
        # Recupera i parametri dal form
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        db_name = self.db_name_input.text().strip()
        user = self.user_input.text().strip()
        password = self.password_input.text().strip()

        # Prova la connessione al database con psycopg2
        try:
            conn = psycopg2.connect(
                dbname=db_name, user=user, password=password, host=host, port=port
            )
            conn.close()
            # Se la connessione ha successo, salva i parametri di accesso
            self.db_params = {
                "dbname": db_name,
                "user": user,
                "password": password,
                "host": host,
                "port": port
            }
            self.accept()
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Errore di Connessione", f"Errore durante la connessione: {e}")
            self.db_params = None
 
    def get_db_params(self):
        return self.db_params


class LoanDialog(FluentDialog):
    def __init__(self, parent=None):
        super().__init__("New Loan", parent)
        self.setMinimumWidth(400)
        
        # Form layout
        form = QFormLayout()
        form.setSpacing(10)
        

        # Rate type selection (fixed or variable)
        self.rate_type_combobox = QComboBox()
        self.rate_type_combobox.addItems(["fixed", "variable"])
        self.rate_type_combobox.currentTextChanged.connect(self.on_rate_type_changed)
        form.addRow("Rate Type:", self.rate_type_combobox)
        
        # Use Euribor checkbox (visible only for variable rate)
        self.use_euribor_checkbox = QCheckBox("Use Euribor rates")
        self.use_euribor_checkbox.setChecked(False)
        self.use_euribor_checkbox.setVisible(False)
        self.use_euribor_checkbox.stateChanged.connect(self.on_use_euribor_changed)
        form.addRow("", self.use_euribor_checkbox)
        
        # Euribor spread input (visible only when using Euribor)
        self.euribor_spread_entry = QDoubleSpinBox()
        self.euribor_spread_entry.setRange(0, 10)
        self.euribor_spread_entry.setDecimals(3)
        self.euribor_spread_entry.setSingleStep(0.125)
        self.euribor_spread_entry.setSuffix("%")
        self.euribor_spread_entry.setVisible(False)
        form.addRow("Euribor Spread (%):", self.euribor_spread_entry)
        
        # Euribor update frequency (visible only when using Euribor)
        self.update_frequency_combobox = QComboBox()
        self.update_frequency_combobox.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        self.update_frequency_combobox.setVisible(False)
        form.addRow("Rate Update Frequency:", self.update_frequency_combobox)

        # Rate input
        self.rate_entry = QDoubleSpinBox()
        self.rate_entry.setRange(0, 100)
        self.rate_entry.setDecimals(6)
        self.rate_entry.setSingleStep(0.005)
        form.addRow("Interest Rate (%):", self.rate_entry)
        
        # Term input
        self.term_entry = QSpinBox()
        self.term_entry.setRange(1, 100)
        form.addRow("Term (years):", self.term_entry)
        
        # Loan amount input
        self.pv_entry = QDoubleSpinBox()
        self.pv_entry.setRange(0, 100000000)
        self.pv_entry.setPrefix("€ ")
        form.addRow("Loan Amount:", self.pv_entry)
        
        # Downpayment input
        self.downpayment_entry = QDoubleSpinBox()
        self.downpayment_entry.setRange(0, 100)
        self.downpayment_entry.setSuffix("%")
        form.addRow("Downpayment:", self.downpayment_entry)
        
        # Amortization type
        self.amortization_combobox = QComboBox()
        self.amortization_combobox.addItems(["French", "Italian"])
        form.addRow("Amortization Type:", self.amortization_combobox)
        
        # Payment frequency
        self.frequency_combobox = QComboBox()
        self.frequency_combobox.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        form.addRow("Payment Frequency:", self.frequency_combobox)
        
        self.main_layout.insertLayout(0, form)

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        # Personalizza lo stile del calendario
        self.start_date.setStyleSheet("""
            QDateEdit {
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 6px 12px;
            }
            QCalendarWidget QToolButton {
                height: 30px;
                width: 100px;
                color: white;
                background-color: #0078D4;
                border-radius: 2px;
            }
            QCalendarWidget QMenu {
                width: 150px;
                left: 20px;
                color: white;
                background-color: #0078D4;
            }
            QCalendarWidget QSpinBox {
                width: 100px;
                color: white;
                background-color: #0078D4;
                selection-background-color: #0078D4;
                selection-color: white;
            }
            QCalendarWidget QTableView {
                selection-background-color: #0078D4;
                selection-color: white;
            }
        """)
        form.addRow("Start Date:", self.start_date)
        
        # Additional costs button
        self.additional_costs_button = QPushButton("Add Additional Costs")
        self.additional_costs_button.clicked.connect(self.open_additional_costs_dialog)
        self.main_layout.insertWidget(1, self.additional_costs_button)
        
        # Create and Cancel buttons
        self.create_button = QPushButton("Create Loan")
        self.create_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.create_button)
        
        self.additional_costs = {}
        self.periodic_expenses = {}

    def on_rate_type_changed(self, text):
        """Mostra/nasconde opzioni per tassi variabili"""
        is_variable = (text == "variable")
        self.use_euribor_checkbox.setVisible(is_variable)
        
        # Se si passa da variabile a fisso, nascondi gli altri controlli
        if not is_variable:
            self.euribor_spread_entry.setVisible(False)
            self.update_frequency_combobox.setVisible(False)

    def on_use_euribor_changed(self, state):
        """Mostra/nasconde opzioni per tassi Euribor"""
        use_euribor = (state == Qt.Checked)
        self.euribor_spread_entry.setVisible(use_euribor)
        self.update_frequency_combobox.setVisible(use_euribor)
        
        # Se si usa Euribor, modifica l'etichetta del campo tasso
        if use_euribor:
            # Il tasso ora rappresenta lo spread sopra l'Euribor
            self.rate_entry.setPrefix("Euribor + ")
            # Mostra un messaggio di informazione
            QMessageBox.information(self, "Euribor Rate", 
                                   "When using Euribor rates, the current Euribor rate will be automatically " +
                                   "retrieved and added to the specified spread.")
        else:
            # Il tasso ora rappresenta il tasso fisso
            self.rate_entry.setPrefix("")


    def open_additional_costs_dialog(self):
        dialog = AdditionalCostsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            costs = dialog.get_costs()
            self.additional_costs = costs['additional_costs']
            self.periodic_expenses = costs['periodic_expenses']
            
    def get_loan_data(self):
        return {
            "rate": self.rate_entry.value(),
            "term": self.term_entry.value(),
            "loan_amount": self.pv_entry.value(),
            "downpayment_percent": self.downpayment_entry.value(),
            "amortization_type": self.amortization_combobox.currentText(),
            "frequency": self.frequency_combobox.currentText(),
            "rate_type": self.rate_type_combobox.currentText(),
            "use_euribor": self.use_euribor_checkbox.isChecked(),
            "euribor_spread": self.euribor_spread_entry.value(),
            "additional_costs": self.additional_costs or {},
            "periodic_expenses": self.periodic_expenses or {},
            "start": self.start_date.date().toString("yyyy-MM-dd")  # Aggiungi questa riga
        }
    

class AdditionalCostsDialog(FluentDialog):
    def __init__(self, parent=None):
        super().__init__("Additional Costs", parent)
        self.setMinimumWidth(400)
        
        self.costs_layout = QFormLayout()
        self.costs_layout.setSpacing(10)
        
        self.cost_entries = []
        self.add_cost_field()
        
        self.main_layout.insertLayout(0, self.costs_layout)
        
        # Add another cost button
        add_button = QPushButton("Add Another Cost")
        add_button.clicked.connect(self.add_cost_field)
        self.main_layout.insertWidget(1, add_button)
        
        # Periodic costs
        self.periodic_cost_entry = QDoubleSpinBox()
        self.periodic_cost_entry.setRange(0, 1000000)
        self.periodic_cost_entry.setPrefix("€ ")
        self.costs_layout.addRow("Periodic Costs:", self.periodic_cost_entry)
        
        # Save and Cancel buttons
        self.save_button = QPushButton("Save Costs")
        self.save_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)

    def add_cost_field(self):
        cost_name = QLineEdit()
        cost_value = QDoubleSpinBox()
        cost_value.setRange(0, 1000000)
        cost_value.setPrefix("€ ")
        
        self.costs_layout.addRow("Cost Name:", cost_name)
        self.costs_layout.addRow("Cost Amount:", cost_value)
        self.cost_entries.append((cost_name, cost_value))

    def get_costs(self):
        one_time_costs = {}
        periodic_costs = {}
        
        # Raccogliere i costi una tantum
        for name_entry, value_entry in self.cost_entries:
            name = name_entry.text().strip()
            value = value_entry.value()
            if name and value > 0:
                one_time_costs[name] = value
        
        # Raccogliere i costi periodici
        periodic_value = self.periodic_cost_entry.value()
        if periodic_value > 0:
            periodic_costs["Regular Payment Fee"] = periodic_value
            
        return {
            'additional_costs': one_time_costs,
            'periodic_expenses': periodic_costs
        }
    


class LoanPaymentAnalysisDialog(FluentDialog):
    """Finestra per l'analisi dei pagamenti"""
    def __init__(self, loan, parent=None):
        super().__init__("Payment Analysis", parent)
        self.setMinimumWidth(500)
        self.loan = loan
        
        # Create tabs for different analyses
        tab_widget = QTabWidget()
        
        # Early Payment Tab
        early_payment_widget = QWidget()
        early_layout = QVBoxLayout(early_payment_widget)
        
        # Extra payment input 
        early_form = QFormLayout()
        self.extra_payment = QDoubleSpinBox()
        self.extra_payment.setRange(0, 1000000)
        self.extra_payment.setPrefix("€ ")
        self.extra_payment.setSingleStep(50)
        early_form.addRow("Extra Monthly Payment:", self.extra_payment)
        
        # Results display
        self.early_results = QTextEdit()
        self.early_results.setReadOnly(True)
        self.early_results.setMinimumHeight(100)
        
        # Calculate button
        calculate_early_btn = QPushButton("Calculate Early Payoff")
        calculate_early_btn.clicked.connect(self.calculate_early_payment)
        
        early_layout.addLayout(early_form)
        early_layout.addWidget(calculate_early_btn)
        early_layout.addWidget(self.early_results)
        
        # Faster Payment Tab
        faster_payment_widget = QWidget()
        faster_layout = QVBoxLayout(faster_payment_widget)

        
        # Years input
        faster_form = QFormLayout()
        self.years_to_payoff = QDoubleSpinBox()
        self.years_to_payoff.setRange(1, self.loan.initial_term)
        self.years_to_payoff.setValue(self.loan.initial_term / 2)  # Default to half the current term
        self.years_to_payoff.setSingleStep(0.5)
        self.years_to_payoff.setSuffix(" years")
        faster_form.addRow("Desired Years to Pay Off:", self.years_to_payoff)
        
        # Results display
        self.faster_results = QTextEdit()
        self.faster_results.setReadOnly(True)
        self.faster_results.setMinimumHeight(100)
        
        # Calculate button
        calculate_faster_btn = QPushButton("Calculate Required Payment")
        calculate_faster_btn.clicked.connect(self.calculate_faster_payment)
        
        faster_layout.addLayout(faster_form)
        faster_layout.addWidget(calculate_faster_btn)
        faster_layout.addWidget(self.faster_results)



        # Add tabs
        tab_widget.addTab(early_payment_widget, "Early Payoff Analysis")
        tab_widget.addTab(faster_payment_widget, "Faster Payoff Analysis")
        self.main_layout.insertWidget(0, tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)
    
    def calculate_early_payment(self):
        extra_amt = self.extra_payment.value()
        result = self.loan.pay_early(extra_amt)
        self.early_results.setText(result)
    
    def calculate_faster_payment(self):
        years = self.years_to_payoff.value()
        result = self.loan.pay_faster(years)
        self.faster_results.setText(result)


class AmortizationDialog(FluentDialog):
    def __init__(self, table_data, parent=None):
        super().__init__("Amortization Table", parent)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Create table
        table_widget = QTableWidget()
        table_widget.setRowCount(len(table_data))
        table_widget.setColumnCount(len(table_data.columns))
        table_widget.setHorizontalHeaderLabels(table_data.columns)
        
        for row in range(len(table_data)):
            for col in range(len(table_data.columns)):
                value = table_data.iat[row, col]
                if pd.isnull(value):
                    value = "N/A"  # Default fallback
                item = QTableWidgetItem(str(value))
                table_widget.setItem(row, col, item)

        
        # Style the table
        table_widget.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 6px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
            }
        """)
        
        self.main_layout.insertWidget(0, table_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class TAEGCalculationDialog(FluentDialog):
    def __init__(self, loan, parent=None):
        super().__init__("TAEG Calculations", parent)
        self.setMinimumWidth(400)
        
        self.loan = loan
        
        # Results labels
        self.taeg_periodic_label = QLabel("Calculated TAEG Periodic: N/A")
        self.taeg_annualized_label = QLabel("Calculated TAEG Annualized: N/A")
        self.main_layout.insertWidget(0, self.taeg_periodic_label)
        self.main_layout.insertWidget(1, self.taeg_annualized_label)
        
        # Calculate button
        calculate_button = QPushButton("Calculate TAEG")
        calculate_button.clicked.connect(self.calculate_taeg)
        self.main_layout.insertWidget(2, calculate_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

    def calculate_taeg(self):
        taeg_result = self.loan.calculate_taeg()
        if taeg_result is not None:
            self.taeg_periodic_label.setText(f"Calculated TAEG Periodic: {self.loan.taeg_periodic:.4f}%")
            self.taeg_annualized_label.setText(f"Calculated TAEG Annualized: {self.loan.taeg_annualized:.4f}%")
        else:
            QMessageBox.warning(self, "Error", "TAEG calculation failed.")

class LoanComparisonDialog(FluentDialog):
    def __init__(self, comparison_text, parent=None):
        super().__init__("Loan Comparison", parent)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Results text area
        comparison_results = QTextEdit()
        comparison_results.setReadOnly(True)
        comparison_results.setText(comparison_text)
        comparison_results.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                background-color: white;
            }
        """)
        
        self.main_layout.insertWidget(0, comparison_results)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class EditLoanDialog(FluentDialog):
    def __init__(self, loan, parent=None):
        super().__init__("Edit Loan", parent)
        self.setMinimumWidth(400)
        
        form = QFormLayout()
        form.setSpacing(10)

        # Rate type selection
        self.rate_type_combobox = QComboBox()
        self.rate_type_combobox.addItems(["fixed", "variable"])
        self.rate_type_combobox.setCurrentText(loan.rate_type)
        self.rate_type_combobox.currentTextChanged.connect(self.on_rate_type_changed)
        form.addRow("Rate Type:", self.rate_type_combobox)
        
        # Use Euribor checkbox
        self.use_euribor_checkbox = QCheckBox("Use Euribor rates")
        self.use_euribor_checkbox.setChecked(loan.use_euribor)
        self.use_euribor_checkbox.setVisible(loan.rate_type == "variable")
        self.use_euribor_checkbox.stateChanged.connect(self.on_use_euribor_changed)
        form.addRow("", self.use_euribor_checkbox)
        
        # Euribor spread input
        self.euribor_spread_entry = QDoubleSpinBox()
        self.euribor_spread_entry.setRange(0, 10)
        self.euribor_spread_entry.setDecimals(3)
        self.euribor_spread_entry.setSingleStep(0.125)
        self.euribor_spread_entry.setSuffix("%")
        self.euribor_spread_entry.setValue(loan.euribor_spread * 100)  # Convert to percentage
        self.euribor_spread_entry.setVisible(loan.rate_type == "variable" and loan.use_euribor)
        form.addRow("Euribor Spread (%):", self.euribor_spread_entry)
        
        # Euribor update frequency
        self.update_frequency_combobox = QComboBox()
        self.update_frequency_combobox.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        self.update_frequency_combobox.setCurrentText(loan.update_frequency or "monthly")
        self.update_frequency_combobox.setVisible(loan.rate_type == "variable" and loan.use_euribor)
        form.addRow("Rate Update Frequency:", self.update_frequency_combobox)
        
        # Rate input
        self.rate_entry = QDoubleSpinBox()
        self.rate_entry.setRange(0, 100)
        self.rate_entry.setDecimals(6)
        self.rate_entry.setSingleStep(0.001)
        self.rate_entry.setValue(loan.initial_rate)
        form.addRow("Interest Rate (%):", self.rate_entry)
        
        # Term input
        self.term_entry = QSpinBox()
        self.term_entry.setRange(1, 100)
        self.term_entry.setValue(loan.initial_term)
        form.addRow("Term (years):", self.term_entry)
        
        # Loan amount input
        self.pv_entry = QDoubleSpinBox()
        self.pv_entry.setRange(0, 100000000)
        self.pv_entry.setPrefix("€ ")
        self.pv_entry.setValue(loan.loan_amount)
        form.addRow("Loan Amount:", self.pv_entry)
        
        # Downpayment input
        self.downpayment_entry = QDoubleSpinBox()
        self.downpayment_entry.setRange(0, 100)
        self.downpayment_entry.setSuffix("%")
        self.downpayment_entry.setValue(loan.downpayment_percent)
        form.addRow("Downpayment:", self.downpayment_entry)
        
        # Amortization type
        self.amortization_combobox = QComboBox()
        self.amortization_combobox.addItems(["French", "Italian"])
        self.amortization_combobox.setCurrentText(loan.amortization_type)
        form.addRow("Amortization Type:", self.amortization_combobox)
        
        # Payment frequency
        self.frequency_combobox = QComboBox()
        self.frequency_combobox.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        self.frequency_combobox.setCurrentText(loan.frequency)
        form.addRow("Payment Frequency:", self.frequency_combobox)
        
        self.main_layout.insertLayout(0, form)
        
        # Update and Cancel buttons
        update_button = QPushButton("Update Loan")
        update_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(update_button)

    def on_rate_type_changed(self, text):
        """Mostra/nasconde opzioni per tassi variabili"""
        is_variable = (text == "variable")
        self.use_euribor_checkbox.setVisible(is_variable)
        
        # Se si passa da variabile a fisso, nascondi gli altri controlli
        if not is_variable:
            self.euribor_spread_entry.setVisible(False)
            self.update_frequency_combobox.setVisible(False)
            self.rate_entry.setPrefix("")

    def on_use_euribor_changed(self, state):
        """Mostra/nasconde opzioni per tassi Euribor"""
        use_euribor = (state == Qt.Checked)
        self.euribor_spread_entry.setVisible(use_euribor)
        self.update_frequency_combobox.setVisible(use_euribor)
        
        # Se si usa Euribor, modifica l'etichetta del campo tasso
        if use_euribor:
            self.rate_entry.setPrefix("Euribor + ")


    def get_updated_loan_data(self):
        return {
            "new_rate": self.rate_entry.value(),
            "new_term": self.term_entry.value(),
            "new_loan_amount": self.pv_entry.value(),
            "new_downpayment_percent": self.downpayment_entry.value(),
            "new_amortization_type": self.amortization_combobox.currentText(),
            "new_frequency": self.frequency_combobox.currentText()
        }

class PlotDialog(FluentDialog):
    def __init__(self, loan, parent=None):
        """
        Initialize the plot dialog for loan visualization.
        
        Args:
            loan: The loan object containing the data to plot
            parent: The parent widget (default: None)
        """
        super().__init__("Loan Analysis Plot", parent)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.loan = loan

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        # Create matplotlib toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Customize toolbar appearance
        self.toolbar.setStyleSheet("""
            QToolBar {
                border: none;
                background: transparent;
                spacing: 8px;
                padding: 4px;
            }
            QToolBar QToolButton {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
            }
            QToolBar QToolButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #e0e0e0;
            }
            QToolBar QToolButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        
        # Remove matplotlib text/logo and add custom logo
        self.customize_toolbar()
        
        # Create main layout and add widgets
        self.setup_layout()
        
        # Create the actual plot
        self.create_plot()
        
        # Add close button
        self.add_close_button()

    def customize_toolbar(self):
        """Remove matplotlib text/logo and add custom app logo to toolbar."""
        # Remove matplotlib text
        for action in self.toolbar.actions():
            if action.text() in ['Subplots', 'Customize']:
                self.toolbar.removeAction(action)
        
        # Try to add custom logo
        try:
            logo_path = resource_path('loan_icon.ico')
            if os.path.exists(logo_path):
                # Create logo label
                logo_label = QLabel()
                logo_pixmap = QPixmap(logo_path).scaled(
                    24, 24, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                logo_label.setPixmap(logo_pixmap)
                
                # Add spacer and logo to right side of toolbar
                spacer = QWidget()
                spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.toolbar.addWidget(spacer)
                self.toolbar.addWidget(logo_label)
        except Exception as e:
            print(f"Could not add logo to toolbar: {e}")

    def setup_layout(self):
        """Set up the dialog layout with toolbar and canvas."""
        # Add widgets to main layout
        self.main_layout.insertWidget(0, self.toolbar)
        self.main_layout.insertWidget(1, self.canvas)
        
        # Add stretch to make plot expand
        self.main_layout.addStretch(1)

    def create_plot(self):
        """Create the loan analysis plot."""
        # Clear any existing plots
        self.figure.clear()
        
        # Get loan amortization table
        amort = self.loan.table
        
        # Create subplot with grid
        ax = self.figure.add_subplot(111)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Plot balance and cumulative interest
        balance_line = ax.plot(
            amort.index, 
            amort.Balance, 
            label='Balance (€)', 
            linewidth=2,
            color='#0078D4'  # Use app's theme color
        )
        
        interest_line = ax.plot(
            amort.index, 
            amort.Interest.cumsum(), 
            label='Interest Paid (€)', 
            linewidth=2,
            color='#107C10'  # Complementary green color
        )
        
        # Set title based on amortization type
        title = f"{self.loan.amortization_type} Amortization Analysis"
        ax.set_title(title, pad=20, fontsize=12, fontweight='bold')
        
        # Customize axes
        ax.set_xlabel('Date', fontsize=10)
        ax.set_ylabel('Amount (€)', fontsize=10)
        
        # Format y-axis with euro symbol
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(
                lambda x, p: f'€{x:,.0f}'
            )
        )
        
        # Rotate and align x-axis labels
        self.figure.autofmt_xdate()
        
        # Add legend with custom style
        ax.legend(
            loc='upper right',
            fancybox=True,
            shadow=True,
            framealpha=0.9
        )
        
        # Set tight layout
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()

    def add_close_button(self):
        """Add a close button to the dialog."""
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        close_button.setMinimumWidth(100)
        self.button_layout.addWidget(close_button)
        
    def resizeEvent(self, event):
        """Handle dialog resize events."""
        super().resizeEvent(event)
        self.figure.tight_layout()  # Adjust plot layout when dialog is resized
        self.canvas.draw_idle()     # Redraw canvas efficiently


class SidebarWidget(QWidget):
    """Widget per la sidebar ridimensionabile dell'applicazione."""
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.collapsed = False
        self.toggle_button = None
        self.content_widget = None
        self.animation = None
        self.resize_handle = None
        self.is_resizing = False
        self.start_x = 0
        self.start_width = 0
        self.expanded_width = 250  # Larghezza quando espanso
        self.init_ui()

    def init_ui(self):
        # Layout principale
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Contenitore per il contenuto della sidebar
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 10, 5, 10)
        self.content_layout.setSpacing(10)
        
        # Bottone hamburger per collassare/espandere in stile Instagram
        self.toggle_button = QPushButton()
        self.toggle_button.setFixedSize(32, 32)
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        self.toggle_button.setCursor(Qt.PointingHandCursor)  # Cambia il cursore per un feedback migliore
        
        # Stile per il menu hamburger
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0;
            }
            QPushButton::hover {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 16px;
            }
        """)
        
        # Imposta l'icona hamburger
        self.update_hamburger_icon()
        
        # Layout per il bottone (allineato in alto a destra)
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(0, 5, 5, 0)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_button)
        
        # Aggiungi i layout al layout principale
        main_layout.addLayout(toggle_layout)
        main_layout.addWidget(self.content_widget)
        main_layout.addStretch()
        
        # Crea il resize handle (maniglia di ridimensionamento)
        self.resize_handle = QFrame(self)
        self.resize_handle.setFrameShape(QFrame.VLine)
        self.resize_handle.setFrameShadow(QFrame.Sunken)
        self.resize_handle.setCursor(Qt.SizeHorCursor)
        self.resize_handle.setFixedWidth(4)
        self.resize_handle.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
            QFrame:hover {
                background-color: rgba(0, 120, 212, 0.3);
            }
        """)
        
        # Posiziona il resize handle sul bordo destro
        self.resize_handle.setGeometry(self.width() - 4, 0, 4, self.height())
        
        # Stile iniziale
        self.setMinimumWidth(50)  # Larghezza minima quando collassato
        self.setMaximumWidth(500)  # Imposta una larghezza massima ragionevole
        self.setFixedWidth(self.expanded_width)  # Larghezza iniziale
        self.update_style()
    
    def update_hamburger_icon(self):
        """Aggiorna l'icona del menu hamburger basata sullo stato"""
        # Crea un'icona "hamburger" usando il disegno manuale
        icon_size = QSize(18, 18)
        hamburger_icon = QPixmap(icon_size)
        hamburger_icon.fill(Qt.transparent)
        
        painter = QPainter(hamburger_icon)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Usa un colore basato sul tema corrente
        if self.theme_manager and self.theme_manager.get_current_theme() == "dark":
            painter.setPen(QPen(Qt.white, 2))
        else:
            painter.setPen(QPen(Qt.black, 2))
        
        # Disegna tre linee orizzontali per creare il menu hamburger
        if not self.collapsed:
            # Tre linee parallele del menu hamburger
            y_offset = 4
            for i in range(3):
                painter.drawLine(3, y_offset, 15, y_offset)
                y_offset += 5
        else:
            # X per indicare chiusura quando è collassato
            painter.drawLine(5, 5, 13, 13)
            painter.drawLine(13, 5, 5, 13)
        
        painter.end()
        
        self.toggle_button.setIcon(QIcon(hamburger_icon))
        self.toggle_button.setIconSize(icon_size)
    
    def add_widget(self, widget):
        """Aggiungi un widget alla sidebar."""
        self.content_layout.addWidget(widget)
    
    def toggle_sidebar(self):
        """Espandi/collassa la sidebar."""
        self.collapsed = not self.collapsed
        target_width = 50 if self.collapsed else self.expanded_width
        
        # Aggiorna l'icona invece di cambiare il testo
        self.update_hamburger_icon()
        
        # Animazione di transizione
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.start()
        
        # Imposta anche la larghezza massima durante l'animazione
        self.setFixedWidth(target_width)
        
        # Nascondi/mostra il contenuto durante l'animazione
        self.content_widget.setVisible(not self.collapsed)
    
    def update_style(self):
        """Aggiorna lo stile in base al tema corrente."""
        if self.theme_manager:
            theme = self.theme_manager.get_current_theme()
            if theme == "light":
                self.setStyleSheet("""
                    QWidget {
                        background-color: #f5f5f5;
                        border-right: 1px solid #e0e0e0;
                    }
                    QPushButton {
                        background-color: #ffffff;
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                    }
                    QPushButton:hover {
                        background-color: #f0f0f0;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QWidget {
                        background-color: #333333;
                        border-right: 1px solid #444444;
                    }
                    QPushButton {
                        background-color: #444444;
                        border: 1px solid #555555;
                        border-radius: 4px;
                        color: #ffffff;
                    }
                    QPushButton:hover {
                        background-color: #555555;
                    }
                """)
            
            # Aggiorna anche l'icona perché potrebbe essere cambiato il tema
            self.update_hamburger_icon()
    
    def resizeEvent(self, event):
        """Gestisce il ridimensionamento del widget."""
        super().resizeEvent(event)
        # Aggiorna la posizione del resize handle
        if self.resize_handle:
            self.resize_handle.setGeometry(self.width() - 4, 0, 4, self.height())
    
    def mousePressEvent(self, event):
        """Gestisce l'evento di pressione del mouse."""
        if self.resize_handle.geometry().contains(event.pos()):
            self.is_resizing = True
            self.start_x = event.globalX()
            self.start_width = self.width()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Gestisce l'evento di movimento del mouse."""
        if self.is_resizing:
            # Calcola la nuova larghezza
            delta = event.globalX() - self.start_x
            new_width = max(self.minimumWidth(), min(self.start_width + delta, self.maximumWidth()))
            
            # Se non è collassato, aggiorna la larghezza quando espanso
            if not self.collapsed and new_width > 50:
                self.expanded_width = new_width
            
            # Imposta la nuova larghezza
            self.setFixedWidth(new_width)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Gestisce l'evento di rilascio del mouse."""
        if self.is_resizing:
            self.is_resizing = False
            
            # Se la larghezza è molto piccola, considera collassato
            if self.width() < 60:
                self.collapsed = True
                self.setFixedWidth(50)
                self.content_widget.setVisible(False)
                self.update_hamburger_icon()
            # Se è stato espanso da collassato, aggiorna lo stato
            elif self.collapsed and self.width() > 50:
                self.collapsed = False
                self.content_widget.setVisible(True)
                self.update_hamburger_icon()
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class CRMWidget(QWidget):
    """Widget principale per la gestione del CRM."""
    def __init__(self, crm_manager, parent=None, theme_manager=None):
        super().__init__(parent)
        self.crm_manager = crm_manager
        self.theme_manager = theme_manager
        self.current_client = None
        self.current_corporation = None
        self.init_ui()
        self.load_clients()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Titolo
        title_label = QLabel("Client Manager")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Tab widget to switch between Individual and Corporate clients
        self.tabs = QTabWidget()
        individual_tab = QWidget()
        corporate_tab = QWidget()
        
        # Setup individual clients tab
        individual_layout = QVBoxLayout(individual_tab)
        
        # Barra azioni per clienti individuali
        individual_action_layout = QHBoxLayout()
        self.add_client_btn = QPushButton("Add Client")
        self.add_client_btn.clicked.connect(self.add_client)
        self.refresh_clients_btn = QPushButton("Refresh")
        self.refresh_clients_btn.clicked.connect(self.load_clients)
        individual_action_layout.addWidget(self.add_client_btn)
        individual_action_layout.addWidget(self.refresh_clients_btn)
        individual_layout.addLayout(individual_action_layout)
        
        # Lista clients individuali
        self.clients_list = QListWidget()
        self.clients_list.itemClicked.connect(self.on_client_selected)
        individual_layout.addWidget(self.clients_list)
        
        # Bottoni per le operazioni sul client selezionato
        client_actions = QHBoxLayout()
        self.view_details_btn = QPushButton("View Details")
        self.view_details_btn.clicked.connect(self.view_client_details)
        self.edit_client_btn = QPushButton("Edit Client")
        self.edit_client_btn.clicked.connect(self.edit_client)
        self.delete_client_btn = QPushButton("Delete Client")
        self.delete_client_btn.clicked.connect(self.delete_client)
        client_actions.addWidget(self.view_details_btn)
        client_actions.addWidget(self.edit_client_btn)
        client_actions.addWidget(self.delete_client_btn)
        individual_layout.addLayout(client_actions)
        
        # Bottoni per le interazioni
        interaction_actions = QHBoxLayout()
        self.add_interaction_btn = QPushButton("Add Interaction")
        self.add_interaction_btn.clicked.connect(self.add_interaction)
        self.view_interactions_btn = QPushButton("View Interactions")
        self.view_interactions_btn.clicked.connect(self.view_interactions)
        interaction_actions.addWidget(self.add_interaction_btn)
        interaction_actions.addWidget(self.view_interactions_btn)
        individual_layout.addLayout(interaction_actions)
        
        # Bottone per associare prestito
        self.assign_loan_btn = QPushButton("Assign Loan")
        self.assign_loan_btn.clicked.connect(self.assign_loan)
        individual_layout.addWidget(self.assign_loan_btn)
        
        # Setup corporate clients tab
        corporate_layout = QVBoxLayout(corporate_tab)
        
        # Barra azioni per clienti corporate
        corporate_action_layout = QHBoxLayout()
        self.add_corporation_btn = QPushButton("Add Corporation")
        self.add_corporation_btn.clicked.connect(self.add_corporation)
        self.refresh_corporations_btn = QPushButton("Refresh")
        self.refresh_corporations_btn.clicked.connect(self.load_corporations)
        corporate_action_layout.addWidget(self.add_corporation_btn)
        corporate_action_layout.addWidget(self.refresh_corporations_btn)
        corporate_layout.addLayout(corporate_action_layout)
        
        # Lista corporations
        self.corporations_list = QListWidget()
        self.corporations_list.itemClicked.connect(self.on_corporation_selected)
        corporate_layout.addWidget(self.corporations_list)
        
        # Bottoni per le operazioni sulla corporation selezionata
        corporation_actions = QHBoxLayout()
        self.view_corporation_details_btn = QPushButton("View Details")
        self.view_corporation_details_btn.clicked.connect(self.view_corporation_details)
        self.edit_corporation_btn = QPushButton("Edit Corporation")
        self.edit_corporation_btn.clicked.connect(self.edit_corporation)
        self.delete_corporation_btn = QPushButton("Delete Corporation")
        self.delete_corporation_btn.clicked.connect(self.delete_corporation)
        corporation_actions.addWidget(self.view_corporation_details_btn)
        corporation_actions.addWidget(self.edit_corporation_btn)
        corporation_actions.addWidget(self.delete_corporation_btn)
        corporate_layout.addLayout(corporation_actions)
        
        # Bottoni per le interazioni con corporation
        corporation_interaction_actions = QHBoxLayout()
        self.add_corporation_interaction_btn = QPushButton("Add Interaction")
        self.add_corporation_interaction_btn.clicked.connect(self.add_corporation_interaction)
        self.view_corporation_interactions_btn = QPushButton("View Interactions")
        self.view_corporation_interactions_btn.clicked.connect(self.view_corporation_interactions)
        corporation_interaction_actions.addWidget(self.add_corporation_interaction_btn)
        corporation_interaction_actions.addWidget(self.view_corporation_interactions_btn)
        corporate_layout.addLayout(corporation_interaction_actions)
        
        # Bottone per associare prestito a corporation
        self.assign_corporation_loan_btn = QPushButton("Assign Loan")
        self.assign_corporation_loan_btn.clicked.connect(self.assign_corporation_loan)
        corporate_layout.addWidget(self.assign_corporation_loan_btn)
        
        # Add tabs to tab widget
        self.tabs.addTab(individual_tab, "Individual Clients")
        self.tabs.addTab(corporate_tab, "Corporate Clients")
        main_layout.addWidget(self.tabs)
        
        # Disabilita i pulsanti che richiedono un client selezionato
        self.toggle_client_buttons(False)
        self.toggle_corporation_buttons(False)
        
        # Connect tab change signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Applica stile
        self.update_style()
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        if index == 0:  # Individual clients tab
            self.load_clients()
        else:  # Corporate clients tab
            self.load_corporations()
            
    def update_style(self):
        """Aggiorna lo stile in base al tema corrente."""
        if self.theme_manager:
            # Lo stile sarà applicato automaticamente dall'app principale
            pass
    
    def toggle_client_buttons(self, enabled):
        """Attiva/disattiva i bottoni che richiedono un client selezionato."""
        self.view_details_btn.setEnabled(enabled)
        self.edit_client_btn.setEnabled(enabled)
        self.delete_client_btn.setEnabled(enabled)
        self.add_interaction_btn.setEnabled(enabled)
        self.view_interactions_btn.setEnabled(enabled)
        self.assign_loan_btn.setEnabled(enabled)
    
    def toggle_corporation_buttons(self, enabled):
        """Attiva/disattiva i bottoni che richiedono una corporation selezionata."""
        self.view_corporation_details_btn.setEnabled(enabled)
        self.edit_corporation_btn.setEnabled(enabled)
        self.delete_corporation_btn.setEnabled(enabled)
        self.add_corporation_interaction_btn.setEnabled(enabled)
        self.view_corporation_interactions_btn.setEnabled(enabled)
        self.assign_corporation_loan_btn.setEnabled(enabled)
    
    # Individual client methods
    def load_clients(self):
        """Carica la lista dei clienti dal CRM."""
        try:
            clients = self.crm_manager.list_clients()
            self.clients_list.clear()
            
            if not clients:
                self.clients_list.addItem("No clients found")
                return
                
            for client in clients:
                item_text = f"{client['first_name']} {client['last_name']}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, client['client_id'])
                self.clients_list.addItem(item)
                
            self.current_client = None
            self.toggle_client_buttons(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load clients: {str(e)}")
    
    def on_client_selected(self, item):
        """Gestisce la selezione di un client dalla lista."""
        self.current_client = item.data(Qt.UserRole)
        self.toggle_client_buttons(True)
    
    def add_client(self):
        """Apre il dialogo per aggiungere un nuovo cliente."""
        dialog = ClientDialog(self.crm_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_clients()
    
    def edit_client(self):
        """Apre il dialogo per modificare un cliente esistente."""
        if not self.current_client:
            return
            
        client_data = self.crm_manager.get_client(self.current_client)
        if not client_data:
            QMessageBox.warning(self, "Warning", "Client not found")
            return
            
        dialog = ClientDialog(self.crm_manager, client_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_clients()
    
    def delete_client(self):
        """Elimina il cliente selezionato."""
        if not self.current_client:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this client?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.crm_manager.delete_client(self.current_client)
                self.load_clients()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete client: {str(e)}")
    
    def view_client_details(self):
        """Mostra i dettagli del cliente selezionato."""
        if not self.current_client:
            return
            
        client_data = self.crm_manager.get_client(self.current_client)
        if not client_data:
            QMessageBox.warning(self, "Warning", "Client not found")
            return
            
        dialog = ClientDetailsDialog(client_data, self.crm_manager, parent=self)
        dialog.exec_()
    
    def add_interaction(self):
        """Aggiunge una nuova interazione col cliente."""
        if not self.current_client:
            return
            
        dialog = InteractionDialog(self.current_client, self.crm_manager, parent=self)
        dialog.exec_()
    
    def view_interactions(self):
        """Visualizza le interazioni del cliente selezionato."""
        if not self.current_client:
            return
            
        interactions = self.crm_manager.get_interactions(self.current_client)
        dialog = InteractionsListDialog(interactions, parent=self)
        dialog.exec_()
    
    def assign_loan(self):
        """Assegna un prestito al cliente selezionato."""
        if not self.current_client:
            return
            
        # Ottieni la lista dei prestiti disponibili dall'app principale
        parent_window = self.window()
        if not hasattr(parent_window, 'loans') or not parent_window.loans:
            QMessageBox.warning(self, "Warning", "No loans available")
            return
            
        dialog = AssignLoanDialog(
            self.current_client, 
            parent_window.loans,
            self.crm_manager,
            parent=self
        )
        dialog.exec_()
    
    # Corporate client methods
    def load_corporations(self):
        """Carica la lista delle aziende dal CRM."""
        try:
            corporations = self.crm_manager.list_corporations()
            self.corporations_list.clear()
            
            if not corporations:
                self.corporations_list.addItem("No corporations found")
                return
                
            for corporation in corporations:
                item_text = corporation['company_name']
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, corporation['corporation_id'])
                self.corporations_list.addItem(item)
                
            self.current_corporation = None
            self.toggle_corporation_buttons(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load corporations: {str(e)}")
    
    def on_corporation_selected(self, item):
        """Gestisce la selezione di un'azienda dalla lista."""
        self.current_corporation = item.data(Qt.UserRole)
        self.toggle_corporation_buttons(True)
    
    def add_corporation(self):
        """Apre il dialogo per aggiungere una nuova azienda."""
        dialog = CorporationDialog(self.crm_manager, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_corporations()
    
    def edit_corporation(self):
        """Apre il dialogo per modificare un'azienda esistente."""
        if not self.current_corporation:
            return
            
        corporation_data = self.crm_manager.get_corporation(self.current_corporation)
        if not corporation_data:
            QMessageBox.warning(self, "Warning", "Corporation not found")
            return
            
        dialog = CorporationDialog(self.crm_manager, corporation_data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_corporations()
    
    def delete_corporation(self):
        """Elimina l'azienda selezionata."""
        if not self.current_corporation:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this corporation?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.crm_manager.delete_corporation(self.current_corporation)
                self.load_corporations()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete corporation: {str(e)}")
    
    def view_corporation_details(self):
        """Mostra i dettagli dell'azienda selezionata."""
        if not self.current_corporation:
            return
            
        corporation_data = self.crm_manager.get_corporation(self.current_corporation)
        if not corporation_data:
            QMessageBox.warning(self, "Warning", "Corporation not found")
            return
            
        dialog = CorporationDetailsDialog(corporation_data, self.crm_manager, parent=self)
        dialog.exec_()
    
    def add_corporation_interaction(self):
        """Aggiunge una nuova interazione con l'azienda."""
        if not self.current_corporation:
            return
            
        dialog = CorporationInteractionDialog(self.current_corporation, self.crm_manager, parent=self)
        dialog.exec_()
    
    def view_corporation_interactions(self):
        """Visualizza le interazioni dell'azienda selezionata."""
        if not self.current_corporation:
            return
            
        interactions = self.crm_manager.get_corporation_interactions(self.current_corporation)
        dialog = CorporationInteractionsListDialog(interactions, parent=self)
        dialog.exec_()
    
    def assign_corporation_loan(self):
        """Assegna un prestito all'azienda selezionata."""
        if not self.current_corporation:
            return
            
        # Ottieni la lista dei prestiti disponibili dall'app principale
        parent_window = self.window()
        if not hasattr(parent_window, 'loans') or not parent_window.loans:
            QMessageBox.warning(self, "Warning", "No loans available")
            return
            
        dialog = AssignCorporationLoanDialog(
            self.current_corporation, 
            parent_window.loans,
            self.crm_manager,
            parent=self
        )
        dialog.exec_()

class ClientDialog(FluentDialog):
    """Dialogo per la creazione/modifica di un cliente."""
    def __init__(self, crm_manager, client_data=None, parent=None):
        title = "Edit Client" if client_data else "Add New Client"
        super().__init__(title, parent)
        self.crm_manager = crm_manager
        self.client_data = client_data or {}
        self.client_id = client_data.get("client_id") if client_data else None
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # First Name
        self.first_name = QLineEdit()
        self.first_name.setText(self.client_data.get("first_name", ""))
        form_layout.addRow("First Name:", self.first_name)
        
        # Last Name
        self.last_name = QLineEdit()
        self.last_name.setText(self.client_data.get("last_name", ""))
        form_layout.addRow("Last Name:", self.last_name)
        
        # Birth Date
        self.birth_date = QLineEdit()
        if "birth_date" in self.client_data and self.client_data["birth_date"]:
            self.birth_date.setText(self.client_data["birth_date"].strftime("%Y-%m-%d"))
        form_layout.addRow("Birth Date (YYYY-MM-DD):", self.birth_date)
        
        # Address
        self.address = QLineEdit()
        self.address.setText(self.client_data.get("address", ""))
        form_layout.addRow("Address:", self.address)
        
        # City
        self.city = QLineEdit()
        self.city.setText(self.client_data.get("city", ""))
        form_layout.addRow("City:", self.city)
        
        # State
        self.state = QLineEdit()
        self.state.setText(self.client_data.get("state", ""))
        form_layout.addRow("State:", self.state)
        
        # ZIP Code
        self.zip_code = QLineEdit()
        self.zip_code.setText(self.client_data.get("zip_code", ""))
        form_layout.addRow("ZIP Code:", self.zip_code)
        
        # Country
        self.country = QLineEdit()
        self.country.setText(self.client_data.get("country", ""))
        form_layout.addRow("Country:", self.country)
        
        # Phone
        self.phone = QLineEdit()
        self.phone.setText(self.client_data.get("phone", ""))
        form_layout.addRow("Phone:", self.phone)
        
        # Email
        self.email = QLineEdit()
        self.email.setText(self.client_data.get("email", ""))
        form_layout.addRow("Email:", self.email)
        
        # Occupation
        self.occupation = QLineEdit()
        self.occupation.setText(self.client_data.get("occupation", ""))
        form_layout.addRow("Occupation:", self.occupation)
        
        # Employer
        self.employer = QLineEdit()
        self.employer.setText(self.client_data.get("employer", ""))
        form_layout.addRow("Employer:", self.employer)
        
        # Income
        self.income = QDoubleSpinBox()
        self.income.setRange(0, 10000000)
        self.income.setPrefix("€ ")
        if "income" in self.client_data:
            self.income.setValue(float(self.client_data["income"]) if self.client_data["income"] else 0)
        form_layout.addRow("Income:", self.income)
        
        # Credit Score
        self.credit_score = QSpinBox()
        self.credit_score.setRange(300, 850)
        if "credit_score" in self.client_data:
            self.credit_score.setValue(self.client_data["credit_score"] if self.client_data["credit_score"] else 300)
        form_layout.addRow("Credit Score:", self.credit_score)
        
        self.main_layout.insertLayout(0, form_layout)
        
        # Save and Cancel buttons
        self.save_button = QPushButton("Save Client")
        self.save_button.clicked.connect(self.save_client)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
    
    def save_client(self):
        """Salva i dati del cliente."""
        try:
            # Validazione dei campi obbligatori
            if not self.first_name.text().strip() or not self.last_name.text().strip():
                QMessageBox.warning(self, "Validation Error", "First name and last name are required")
                return
            
            # Prepara i dati del cliente
            client_data = {
                "first_name": self.first_name.text().strip(),
                "last_name": self.last_name.text().strip(),
                "address": self.address.text().strip(),
                "city": self.city.text().strip(),
                "state": self.state.text().strip(),
                "zip_code": self.zip_code.text().strip(),
                "country": self.country.text().strip(),
                "phone": self.phone.text().strip(),
                "email": self.email.text().strip(),
                "occupation": self.occupation.text().strip(),
                "employer": self.employer.text().strip(),
                "income": self.income.value(),
                "credit_score": self.credit_score.value()
            }
            
            # Gestione della data di nascita
            if self.birth_date.text().strip():
                try:
                    from datetime import datetime
                    client_data["birth_date"] = datetime.strptime(
                        self.birth_date.text().strip(), 
                        "%Y-%m-%d"
                    ).date()
                except ValueError:
                    QMessageBox.warning(
                        self, 
                        "Validation Error", 
                        "Invalid birth date format. Please use YYYY-MM-DD"
                    )
                    return
            
            # Aggiorna o crea il cliente
            if self.client_id:
                self.crm_manager.update_client(self.client_id, client_data)
            else:
                self.crm_manager.add_client(client_data)
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save client: {str(e)}")


class ClientDetailsDialog(FluentDialog):
    """Dialogo per la visualizzazione dei dettagli di un cliente."""
    def __init__(self, client_data, crm_manager, parent=None):
        super().__init__(f"Client Details: {client_data['first_name']} {client_data['last_name']}", parent)
        self.client_data = client_data
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        # Crea un widget di testo per mostrare i dettagli
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        
        # Formatta i dettagli del cliente
        details = f"""<h2>{self.client_data['first_name']} {self.client_data['last_name']}</h2>
        <p><b>Client ID:</b> {self.client_data['client_id']}</p>
        <p><b>Birth Date:</b> {self.client_data.get('birth_date', 'Not provided')}</p>
        <p><b>Contact:</b><br>
        Phone: {self.client_data.get('phone', 'Not provided')}<br>
        Email: {self.client_data.get('email', 'Not provided')}</p>
        <p><b>Address:</b><br>
        {self.client_data.get('address', '')}<br>
        {self.client_data.get('city', '')}, {self.client_data.get('state', '')} {self.client_data.get('zip_code', '')}<br>
        {self.client_data.get('country', '')}</p>
        <p><b>Employment:</b><br>
        Occupation: {self.client_data.get('occupation', 'Not provided')}<br>
        Employer: {self.client_data.get('employer', 'Not provided')}</p>
        <p><b>Financial Information:</b><br>
        Income: €{float(self.client_data.get('income', 0)):,.2f}<br>
        Credit Score: {self.client_data.get('credit_score', 'Not provided')}</p>
        <p><b>Created:</b> {self.client_data.get('created_at', '')}<br>
        <b>Last Updated:</b> {self.client_data.get('updated_at', '')}</p>
        """
        
        details_text.setHtml(details)
        self.main_layout.insertWidget(0, details_text)
        
        # Ottieni e mostra i prestiti associati
        loans_label = QLabel("<b>Associated Loans:</b>")
        loans_list = QListWidget()
        
        try:
            client_loans = self.crm_manager.get_client_loans(self.client_data['client_id'])
            if client_loans:
                for loan_data in client_loans:
                    item_text = f"Loan {loan_data['loan_id']} - €{float(loan_data['loan_amount']):,.2f}"
                    loans_list.addItem(item_text)
            else:
                loans_list.addItem("No loans associated with this client")
        except Exception as e:
            loans_list.addItem(f"Error loading loans: {str(e)}")
            
        self.main_layout.insertWidget(1, loans_label)
        self.main_layout.insertWidget(2, loans_list)
        
        # Pulsante per chiudere
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class CorporationDialog(FluentDialog):
    """Dialogo per la creazione/modifica di un'azienda."""
    def __init__(self, crm_manager, corporation_data=None, parent=None):
        title = "Edit Corporation" if corporation_data else "Add New Corporation"
        super().__init__(title, parent)
        self.crm_manager = crm_manager
        self.corporation_data = corporation_data or {}
        self.corporation_id = corporation_data.get("corporation_id") if corporation_data else None
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Company Name
        self.company_name = QLineEdit()
        self.company_name.setText(self.corporation_data.get("company_name", ""))
        form_layout.addRow("Company Name:", self.company_name)
        
        # Business Type
        self.business_type = QLineEdit()
        self.business_type.setText(self.corporation_data.get("business_type", ""))
        form_layout.addRow("Business Type:", self.business_type)
        
        # Incorporation Date
        self.incorporation_date = QLineEdit()
        if "incorporation_date" in self.corporation_data and self.corporation_data["incorporation_date"]:
            self.incorporation_date.setText(self.corporation_data["incorporation_date"].strftime("%Y-%m-%d"))
        form_layout.addRow("Incorporation Date (YYYY-MM-DD):", self.incorporation_date)
        
        # Registration Number
        self.registration_number = QLineEdit()
        self.registration_number.setText(self.corporation_data.get("registration_number", ""))
        form_layout.addRow("Registration Number:", self.registration_number)
        
        # Tax ID
        self.tax_id = QLineEdit()
        self.tax_id.setText(self.corporation_data.get("tax_id", ""))
        form_layout.addRow("Tax ID:", self.tax_id)
        
        # Industry
        self.industry = QLineEdit()
        self.industry.setText(self.corporation_data.get("industry", ""))
        form_layout.addRow("Industry:", self.industry)
        
        # Annual Revenue
        self.annual_revenue = QDoubleSpinBox()
        self.annual_revenue.setRange(0, 1000000000)
        self.annual_revenue.setPrefix("€ ")
        if "annual_revenue" in self.corporation_data:
            self.annual_revenue.setValue(float(self.corporation_data["annual_revenue"]) if self.corporation_data["annual_revenue"] else 0)
        form_layout.addRow("Annual Revenue:", self.annual_revenue)
        
        # Number of Employees
        self.number_of_employees = QSpinBox()
        self.number_of_employees.setRange(0, 1000000)
        if "number_of_employees" in self.corporation_data:
            self.number_of_employees.setValue(self.corporation_data["number_of_employees"] if self.corporation_data["number_of_employees"] else 0)
        form_layout.addRow("Number of Employees:", self.number_of_employees)
        
        # Headquarters Address
        self.headquarters_address = QLineEdit()
        self.headquarters_address.setText(self.corporation_data.get("headquarters_address", ""))
        form_layout.addRow("Headquarters Address:", self.headquarters_address)
        
        # City
        self.city = QLineEdit()
        self.city.setText(self.corporation_data.get("city", ""))
        form_layout.addRow("City:", self.city)
        
        # State
        self.state = QLineEdit()
        self.state.setText(self.corporation_data.get("state", ""))
        form_layout.addRow("State:", self.state)
        
        # ZIP Code
        self.zip_code = QLineEdit()
        self.zip_code.setText(self.corporation_data.get("zip_code", ""))
        form_layout.addRow("ZIP Code:", self.zip_code)
        
        # Country
        self.country = QLineEdit()
        self.country.setText(self.corporation_data.get("country", ""))
        form_layout.addRow("Country:", self.country)
        
        # Phone
        self.phone = QLineEdit()
        self.phone.setText(self.corporation_data.get("phone", ""))
        form_layout.addRow("Phone:", self.phone)
        
        # Email
        self.email = QLineEdit()
        self.email.setText(self.corporation_data.get("email", ""))
        form_layout.addRow("Email:", self.email)
        
        # Website
        self.website = QLineEdit()
        self.website.setText(self.corporation_data.get("website", ""))
        form_layout.addRow("Website:", self.website)
        
        # Primary Contact Name
        self.primary_contact_name = QLineEdit()
        self.primary_contact_name.setText(self.corporation_data.get("primary_contact_name", ""))
        form_layout.addRow("Primary Contact Name:", self.primary_contact_name)
        
        # Primary Contact Role
        self.primary_contact_role = QLineEdit()
        self.primary_contact_role.setText(self.corporation_data.get("primary_contact_role", ""))
        form_layout.addRow("Primary Contact Role:", self.primary_contact_role)
        
        self.main_layout.insertLayout(0, form_layout)
        
        # Save and Cancel buttons
        self.save_button = QPushButton("Save Corporation")
        self.save_button.clicked.connect(self.save_corporation)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
    
    def save_corporation(self):
        """Salva i dati dell'azienda."""
        try:
            # Validazione dei campi obbligatori
            if not self.company_name.text().strip():
                QMessageBox.warning(self, "Validation Error", "Company name is required")
                return
            
            # Prepara i dati dell'azienda
            corporation_data = {
                "company_name": self.company_name.text().strip(),
                "business_type": self.business_type.text().strip(),
                "registration_number": self.registration_number.text().strip(),
                "tax_id": self.tax_id.text().strip(),
                "industry": self.industry.text().strip(),
                "annual_revenue": self.annual_revenue.value(),
                "number_of_employees": self.number_of_employees.value(),
                "headquarters_address": self.headquarters_address.text().strip(),
                "city": self.city.text().strip(),
                "state": self.state.text().strip(),
                "zip_code": self.zip_code.text().strip(),
                "country": self.country.text().strip(),
                "phone": self.phone.text().strip(),
                "email": self.email.text().strip(),
                "website": self.website.text().strip(),
                "primary_contact_name": self.primary_contact_name.text().strip(),
                "primary_contact_role": self.primary_contact_role.text().strip()
            }
            
            # Gestione della data di incorporazione
            if self.incorporation_date.text().strip():
                try:
                    from datetime import datetime
                    corporation_data["incorporation_date"] = datetime.strptime(
                        self.incorporation_date.text().strip(), 
                        "%Y-%m-%d"
                    ).date()
                except ValueError:
                    QMessageBox.warning(
                        self, 
                        "Validation Error", 
                        "Invalid incorporation date format. Please use YYYY-MM-DD"
                    )
                    return
            
            # Aggiorna o crea l'azienda
            if self.corporation_id:
                self.crm_manager.update_corporation(self.corporation_id, corporation_data)
            else:
                self.crm_manager.add_corporation(corporation_data)
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save corporation: {str(e)}")

class CorporationDetailsDialog(FluentDialog):
    """Dialogo per la visualizzazione dei dettagli di un'azienda."""
    def __init__(self, corporation_data, crm_manager, parent=None):
        super().__init__(f"Corporation Details: {corporation_data['company_name']}", parent)
        self.corporation_data = corporation_data
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        # Crea un widget di testo per mostrare i dettagli
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        
        # Formatta i dettagli dell'azienda
        details = f"""<h2>{self.corporation_data['company_name']}</h2>
        <p><b>Corporation ID:</b> {self.corporation_data['corporation_id']}</p>
        <p><b>Business Type:</b> {self.corporation_data.get('business_type', 'Not provided')}</p>
        <p><b>Incorporation Date:</b> {self.corporation_data.get('incorporation_date', 'Not provided')}</p>
        <p><b>Registration Number:</b> {self.corporation_data.get('registration_number', 'Not provided')}</p>
        <p><b>Tax ID:</b> {self.corporation_data.get('tax_id', 'Not provided')}</p>
        <p><b>Industry:</b> {self.corporation_data.get('industry', 'Not provided')}</p>
        <p><b>Financial Information:</b><br>
        Annual Revenue: €{float(self.corporation_data.get('annual_revenue', 0)):,.2f}<br>
        Number of Employees: {self.corporation_data.get('number_of_employees', 'Not provided')}</p>
        <p><b>Contact:</b><br>
        Phone: {self.corporation_data.get('phone', 'Not provided')}<br>
        Email: {self.corporation_data.get('email', 'Not provided')}<br>
        Website: {self.corporation_data.get('website', 'Not provided')}</p>
        <p><b>Address:</b><br>
        {self.corporation_data.get('headquarters_address', '')}<br>
        {self.corporation_data.get('city', '')}, {self.corporation_data.get('state', '')} {self.corporation_data.get('zip_code', '')}<br>
        {self.corporation_data.get('country', '')}</p>
        <p><b>Primary Contact:</b><br>
        Name: {self.corporation_data.get('primary_contact_name', 'Not provided')}<br>
        Role: {self.corporation_data.get('primary_contact_role', 'Not provided')}</p>
        <p><b>Created:</b> {self.corporation_data.get('created_at', '')}<br>
        <b>Last Updated:</b> {self.corporation_data.get('updated_at', '')}</p>
        """
        
        details_text.setHtml(details)
        self.main_layout.insertWidget(0, details_text)
        
        # Ottieni e mostra i prestiti associati
        loans_label = QLabel("<b>Associated Loans:</b>")
        loans_list = QListWidget()
        
        try:
            corporation_loans = self.crm_manager.get_corporation_loans(self.corporation_data['corporation_id'])
            if corporation_loans:
                for loan_data in corporation_loans:
                    item_text = f"Loan {loan_data['loan_id']} - €{float(loan_data['loan_amount']):,.2f}"
                    loans_list.addItem(item_text)
            else:
                loans_list.addItem("No loans associated with this corporation")
        except Exception as e:
            loans_list.addItem(f"Error loading loans: {str(e)}")
            
        self.main_layout.insertWidget(1, loans_label)
        self.main_layout.insertWidget(2, loans_list)
        
        # Pulsante per chiudere
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class CorporationInteractionDialog(FluentDialog):
    """Dialogo per aggiungere un'interazione con un'azienda."""
    def __init__(self, corporation_id, crm_manager, parent=None):
        super().__init__("Add Corporation Interaction", parent)
        self.corporation_id = corporation_id
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Tipo di interazione
        self.interaction_type = QComboBox()
        self.interaction_type.addItems([
            "phone", "email", "meeting", "visit", "social", "videoconference", "other"
        ])
        form_layout.addRow("Interaction Type:", self.interaction_type)
        
        # Note sull'interazione
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Enter interaction details here...")
        form_layout.addRow("Notes:", self.notes)
        
        self.main_layout.insertLayout(0, form_layout)
        
        # Pulsanti
        save_button = QPushButton("Save Interaction")
        save_button.clicked.connect(self.save_interaction)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(save_button)
    
    def save_interaction(self):
        """Salva l'interazione con l'azienda."""
        try:
            interaction_type = self.interaction_type.currentText()
            notes = self.notes.toPlainText().strip()
            
            if not notes:
                QMessageBox.warning(self, "Validation Error", "Notes cannot be empty")
                return
                
            self.crm_manager.record_corporation_interaction(
                self.corporation_id,
                interaction_type,
                notes
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save interaction: {str(e)}")
            
class CorporationDialog(FluentDialog):
    """Dialogo per la creazione/modifica di un'azienda."""
    def __init__(self, crm_manager, corporation_data=None, parent=None):
        title = "Edit Corporation" if corporation_data else "Add New Corporation"
        super().__init__(title, parent)
        self.crm_manager = crm_manager
        self.corporation_data = corporation_data or {}
        self.corporation_id = corporation_data.get("corporation_id") if corporation_data else None
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Company Name
        self.company_name = QLineEdit()
        self.company_name.setText(self.corporation_data.get("company_name", ""))
        form_layout.addRow("Company Name:", self.company_name)
        
        # Business Type
        self.business_type = QLineEdit()
        self.business_type.setText(self.corporation_data.get("business_type", ""))
        form_layout.addRow("Business Type:", self.business_type)
        
        # Incorporation Date
        self.incorporation_date = QLineEdit()
        if "incorporation_date" in self.corporation_data and self.corporation_data["incorporation_date"]:
            self.incorporation_date.setText(self.corporation_data["incorporation_date"].strftime("%Y-%m-%d"))
        form_layout.addRow("Incorporation Date (YYYY-MM-DD):", self.incorporation_date)
        
        # Registration Number
        self.registration_number = QLineEdit()
        self.registration_number.setText(self.corporation_data.get("registration_number", ""))
        form_layout.addRow("Registration Number:", self.registration_number)
        
        # Tax ID
        self.tax_id = QLineEdit()
        self.tax_id.setText(self.corporation_data.get("tax_id", ""))
        form_layout.addRow("Tax ID:", self.tax_id)
        
        # Industry
        self.industry = QLineEdit()
        self.industry.setText(self.corporation_data.get("industry", ""))
        form_layout.addRow("Industry:", self.industry)
        
        # Annual Revenue
        self.annual_revenue = QDoubleSpinBox()
        self.annual_revenue.setRange(0, 1000000000)
        self.annual_revenue.setPrefix("€ ")
        if "annual_revenue" in self.corporation_data:
            self.annual_revenue.setValue(float(self.corporation_data["annual_revenue"]) if self.corporation_data["annual_revenue"] else 0)
        form_layout.addRow("Annual Revenue:", self.annual_revenue)
        
        # Number of Employees
        self.number_of_employees = QSpinBox()
        self.number_of_employees.setRange(0, 1000000)
        if "number_of_employees" in self.corporation_data:
            self.number_of_employees.setValue(self.corporation_data["number_of_employees"] if self.corporation_data["number_of_employees"] else 0)
        form_layout.addRow("Number of Employees:", self.number_of_employees)
        
        # Headquarters Address
        self.headquarters_address = QLineEdit()
        self.headquarters_address.setText(self.corporation_data.get("headquarters_address", ""))
        form_layout.addRow("Headquarters Address:", self.headquarters_address)
        
        # City
        self.city = QLineEdit()
        self.city.setText(self.corporation_data.get("city", ""))
        form_layout.addRow("City:", self.city)
        
        # State
        self.state = QLineEdit()
        self.state.setText(self.corporation_data.get("state", ""))
        form_layout.addRow("State:", self.state)
        
        # ZIP Code
        self.zip_code = QLineEdit()
        self.zip_code.setText(self.corporation_data.get("zip_code", ""))
        form_layout.addRow("ZIP Code:", self.zip_code)
        
        # Country
        self.country = QLineEdit()
        self.country.setText(self.corporation_data.get("country", ""))
        form_layout.addRow("Country:", self.country)
        
        # Phone
        self.phone = QLineEdit()
        self.phone.setText(self.corporation_data.get("phone", ""))
        form_layout.addRow("Phone:", self.phone)
        
        # Email
        self.email = QLineEdit()
        self.email.setText(self.corporation_data.get("email", ""))
        form_layout.addRow("Email:", self.email)
        
        # Website
        self.website = QLineEdit()
        self.website.setText(self.corporation_data.get("website", ""))
        form_layout.addRow("Website:", self.website)
        
        # Primary Contact Name
        self.primary_contact_name = QLineEdit()
        self.primary_contact_name.setText(self.corporation_data.get("primary_contact_name", ""))
        form_layout.addRow("Primary Contact Name:", self.primary_contact_name)
        
        # Primary Contact Role
        self.primary_contact_role = QLineEdit()
        self.primary_contact_role.setText(self.corporation_data.get("primary_contact_role", ""))
        form_layout.addRow("Primary Contact Role:", self.primary_contact_role)
        
        self.main_layout.insertLayout(0, form_layout)
        
        # Save and Cancel buttons
        self.save_button = QPushButton("Save Corporation")
        self.save_button.clicked.connect(self.save_corporation)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.save_button)
    
    def save_corporation(self):
        """Salva i dati dell'azienda."""
        try:
            # Validazione dei campi obbligatori
            if not self.company_name.text().strip():
                QMessageBox.warning(self, "Validation Error", "Company name is required")
                return
            
            # Prepara i dati dell'azienda
            corporation_data = {
                "company_name": self.company_name.text().strip(),
                "business_type": self.business_type.text().strip(),
                "registration_number": self.registration_number.text().strip(),
                "tax_id": self.tax_id.text().strip(),
                "industry": self.industry.text().strip(),
                "annual_revenue": self.annual_revenue.value(),
                "number_of_employees": self.number_of_employees.value(),
                "headquarters_address": self.headquarters_address.text().strip(),
                "city": self.city.text().strip(),
                "state": self.state.text().strip(),
                "zip_code": self.zip_code.text().strip(),
                "country": self.country.text().strip(),
                "phone": self.phone.text().strip(),
                "email": self.email.text().strip(),
                "website": self.website.text().strip(),
                "primary_contact_name": self.primary_contact_name.text().strip(),
                "primary_contact_role": self.primary_contact_role.text().strip()
            }
            
            # Gestione della data di incorporazione
            if self.incorporation_date.text().strip():
                try:
                    from datetime import datetime
                    corporation_data["incorporation_date"] = datetime.strptime(
                        self.incorporation_date.text().strip(), 
                        "%Y-%m-%d"
                    ).date()
                except ValueError:
                    QMessageBox.warning(
                        self, 
                        "Validation Error", 
                        "Invalid incorporation date format. Please use YYYY-MM-DD"
                    )
                    return
            
            # Aggiorna o crea l'azienda
            if self.corporation_id:
                self.crm_manager.update_corporation(self.corporation_id, corporation_data)
            else:
                self.crm_manager.add_corporation(corporation_data)
                
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save corporation: {str(e)}")

class CorporationDetailsDialog(FluentDialog):
    """Dialogo per la visualizzazione dei dettagli di un'azienda."""
    def __init__(self, corporation_data, crm_manager, parent=None):
        super().__init__(f"Corporation Details: {corporation_data['company_name']}", parent)
        self.corporation_data = corporation_data
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        # Crea un widget di testo per mostrare i dettagli
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        
        # Formatta i dettagli dell'azienda
        details = f"""<h2>{self.corporation_data['company_name']}</h2>
        <p><b>Corporation ID:</b> {self.corporation_data['corporation_id']}</p>
        <p><b>Business Type:</b> {self.corporation_data.get('business_type', 'Not provided')}</p>
        <p><b>Incorporation Date:</b> {self.corporation_data.get('incorporation_date', 'Not provided')}</p>
        <p><b>Registration Number:</b> {self.corporation_data.get('registration_number', 'Not provided')}</p>
        <p><b>Tax ID:</b> {self.corporation_data.get('tax_id', 'Not provided')}</p>
        <p><b>Industry:</b> {self.corporation_data.get('industry', 'Not provided')}</p>
        <p><b>Financial Information:</b><br>
        Annual Revenue: €{float(self.corporation_data.get('annual_revenue', 0)):,.2f}<br>
        Number of Employees: {self.corporation_data.get('number_of_employees', 'Not provided')}</p>
        <p><b>Contact:</b><br>
        Phone: {self.corporation_data.get('phone', 'Not provided')}<br>
        Email: {self.corporation_data.get('email', 'Not provided')}<br>
        Website: {self.corporation_data.get('website', 'Not provided')}</p>
        <p><b>Address:</b><br>
        {self.corporation_data.get('headquarters_address', '')}<br>
        {self.corporation_data.get('city', '')}, {self.corporation_data.get('state', '')} {self.corporation_data.get('zip_code', '')}<br>
        {self.corporation_data.get('country', '')}</p>
        <p><b>Primary Contact:</b><br>
        Name: {self.corporation_data.get('primary_contact_name', 'Not provided')}<br>
        Role: {self.corporation_data.get('primary_contact_role', 'Not provided')}</p>
        <p><b>Created:</b> {self.corporation_data.get('created_at', '')}<br>
        <b>Last Updated:</b> {self.corporation_data.get('updated_at', '')}</p>
        """
        
        details_text.setHtml(details)
        self.main_layout.insertWidget(0, details_text)
        
        # Ottieni e mostra i prestiti associati
        loans_label = QLabel("<b>Associated Loans:</b>")
        loans_list = QListWidget()
        
        try:
            corporation_loans = self.crm_manager.get_corporation_loans(self.corporation_data['corporation_id'])
            if corporation_loans:
                for loan_data in corporation_loans:
                    item_text = f"Loan {loan_data['loan_id']} - €{float(loan_data['loan_amount']):,.2f}"
                    loans_list.addItem(item_text)
            else:
                loans_list.addItem("No loans associated with this corporation")
        except Exception as e:
            loans_list.addItem(f"Error loading loans: {str(e)}")
            
        self.main_layout.insertWidget(1, loans_label)
        self.main_layout.insertWidget(2, loans_list)
        
        # Pulsante per chiudere
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class CorporationInteractionsListDialog(FluentDialog):
    """Dialogo per visualizzare la lista delle interazioni con un'azienda."""
    def __init__(self, interactions, parent=None):
        super().__init__("Corporation Interactions", parent)
        self.interactions = interactions
        self.init_ui()
        
    def init_ui(self):
        # Crea una tabella per le interazioni
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Type", "Notes", "Interaction ID"])
        
        # Popola la tabella con le interazioni
        table.setRowCount(len(self.interactions))
        
        for row, interaction in enumerate(self.interactions):
            # Data
            date_item = QTableWidgetItem(str(interaction.get('interaction_date', '')))
            table.setItem(row, 0, date_item)
            
            # Tipo
            type_item = QTableWidgetItem(str(interaction.get('interaction_type', '')))
            table.setItem(row, 1, type_item)
            
            # Note
            notes_item = QTableWidgetItem(str(interaction.get('notes', '')))
            table.setItem(row, 2, notes_item)
            
            # ID interazione
            id_item = QTableWidgetItem(str(interaction.get('interaction_id', '')))
            table.setItem(row, 3, id_item)
        
        # Imposta le dimensioni delle colonne
        table.setColumnWidth(0, 150)  # Data
        table.setColumnWidth(1, 100)  # Tipo
        table.setColumnWidth(2, 300)  # Note
        table.resizeRowsToContents()
        
        self.main_layout.insertWidget(0, table)
        
        # Pulsante per chiudere
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)

class AssignCorporationLoanDialog(FluentDialog):
    """Dialogo per assegnare un prestito a un'azienda."""
    def __init__(self, corporation_id, available_loans, crm_manager, parent=None):
        super().__init__("Assign Loan to Corporation", parent)
        self.corporation_id = corporation_id
        self.available_loans = available_loans
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Crea una dropdown con i prestiti disponibili
        self.loan_combo = QComboBox()
        for i, loan in enumerate(self.available_loans):
            loan_text = f"Loan {i+1} - {loan.loan_id} - €{loan.loan_amount:,.2f}"
            self.loan_combo.addItem(loan_text, loan.loan_id)
            
        form_layout.addRow("Select Loan:", self.loan_combo)
        self.main_layout.insertLayout(0, form_layout)
        
        # Pulsanti
        assign_button = QPushButton("Assign Loan")
        assign_button.clicked.connect(self.assign_loan)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(assign_button)
    
    def assign_loan(self):
        """Assegna il prestito selezionato all'azienda."""
        if self.loan_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warning", "Please select a loan")
            return
            
        try:
            loan_id = self.loan_combo.currentData()
            self.crm_manager.assign_loan_to_corporation(self.corporation_id, loan_id)
            QMessageBox.information(
                self, 
                "Success", 
                "Loan successfully assigned to corporation"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to assign loan: {str(e)}"
            )

class InteractionDialog(FluentDialog):
    """Dialogo per aggiungere un'interazione con un cliente."""
    def __init__(self, client_id, crm_manager, parent=None):
        super().__init__("Add Interaction", parent)
        self.client_id = client_id
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Tipo di interazione
        self.interaction_type = QComboBox()
        self.interaction_type.addItems([
            "phone", "email", "meeting", "visit", "social", "other"
        ])
        form_layout.addRow("Interaction Type:", self.interaction_type)
        
        # Note sull'interazione
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Enter interaction details here...")
        form_layout.addRow("Notes:", self.notes)
        
        self.main_layout.insertLayout(0, form_layout)
        
        # Pulsanti
        save_button = QPushButton("Save Interaction")
        save_button.clicked.connect(self.save_interaction)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(save_button)
    
    def save_interaction(self):
        """Salva l'interazione con il cliente."""
        try:
            interaction_type = self.interaction_type.currentText()
            notes = self.notes.toPlainText().strip()
            
            if not notes:
                QMessageBox.warning(self, "Validation Error", "Notes cannot be empty")
                return
                
            self.crm_manager.record_interaction(
                self.client_id,
                interaction_type,
                notes
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save interaction: {str(e)}")


class InteractionsListDialog(FluentDialog):
    """Dialogo per visualizzare la lista delle interazioni con un cliente."""
    def __init__(self, interactions, parent=None):
        super().__init__("Client Interactions", parent)
        self.interactions = interactions
        self.init_ui()
        
    def init_ui(self):
        # Crea una tabella per le interazioni
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Type", "Notes", "Interaction ID"])
        
        # Popola la tabella con le interazioni
        table.setRowCount(len(self.interactions))
        
        for row, interaction in enumerate(self.interactions):
            # Data
            date_item = QTableWidgetItem(str(interaction.get('interaction_date', '')))
            table.setItem(row, 0, date_item)
            
            # Tipo
            type_item = QTableWidgetItem(str(interaction.get('interaction_type', '')))
            table.setItem(row, 1, type_item)
            
            # Note
            notes_item = QTableWidgetItem(str(interaction.get('notes', '')))
            table.setItem(row, 2, notes_item)
            
            # ID interazione
            id_item = QTableWidgetItem(str(interaction.get('interaction_id', '')))
            table.setItem(row, 3, id_item)
        
        # Imposta le dimensioni delle colonne
        table.setColumnWidth(0, 150)  # Data
        table.setColumnWidth(1, 100)  # Tipo
        table.setColumnWidth(2, 300)  # Note
        table.resizeRowsToContents()
        
        self.main_layout.insertWidget(0, table)
        
        # Pulsante per chiudere
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)


class AssignLoanDialog(FluentDialog):
    """Dialogo per assegnare un prestito a un cliente."""
    def __init__(self, client_id, available_loans, crm_manager, parent=None):
        super().__init__("Assign Loan to Client", parent)
        self.client_id = client_id
        self.available_loans = available_loans
        self.crm_manager = crm_manager
        self.init_ui()
        
    def init_ui(self):
        form_layout = QFormLayout()
        
        # Crea una dropdown con i prestiti disponibili
        self.loan_combo = QComboBox()
        for i, loan in enumerate(self.available_loans):
            loan_text = f"Loan {i+1} - {loan.loan_id} - €{loan.loan_amount:,.2f}"
            self.loan_combo.addItem(loan_text, loan.loan_id)
            
        form_layout.addRow("Select Loan:", self.loan_combo)
        self.main_layout.insertLayout(0, form_layout)
        
        # Pulsanti
        assign_button = QPushButton("Assign Loan")
        assign_button.clicked.connect(self.assign_loan)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(assign_button)
    
    def assign_loan(self):
        """Assegna il prestito selezionato al cliente."""
        if self.loan_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warning", "Please select a loan")
            return
            
        try:
            loan_id = self.loan_combo.currentData()
            self.crm_manager.assign_loan_to_client(self.client_id, loan_id)
            QMessageBox.information(
                self, 
                "Success", 
                "Loan successfully assigned to client"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to assign loan: {str(e)}"
            )



class LoanApp(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        # Aggiungi l'evento di chiusura
        self.closeEvent = self.on_close
        self.db_manager = db_manager
        self.setWindowTitle("LoanManager Pro")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowIcon(QIcon(resource_path('loan_icon.ico')))
    
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        self.setStyleSheet(self.theme_manager.get_stylesheet())
    
        # Initialize database schema
        self.db_manager.create_db()

        self.crm_manager = LoanCRM(self.db_manager)

        if not self.db_manager.check_connection():
            QMessageBox.critical(self, "Database Error", "Impossibile connettersi al database.")
            return


        # Initialize state variables
        self.loans = []
        self.selected_loan = None
        self.undo_stack = []
        self.redo_stack = []
        
        # Set up central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

    # Crea la sidebar
        self.sidebar = SidebarWidget(parent=self, theme_manager=self.theme_manager)
        
        # Crea il widget CRM
        self.crm_widget = CRMWidget(self.crm_manager, parent=self, theme_manager=self.theme_manager)
        
        # Aggiungi un bottone per aprire il CRM nella sidebar
        crm_button = QPushButton("Customers")
        crm_button.setIcon(QIcon(resource_path("crm.png")))
        crm_button.clicked.connect(self.toggle_crm_widget)
        self.sidebar.add_widget(crm_button)
        
        reports_button = QPushButton("Reports")
        reports_button.setIcon(QIcon(resource_path("report.png")))
        reports_button.clicked.connect(self.open_reports)
        self.sidebar.add_widget(reports_button)
        
        # Inizialmente nascondi il widget CRM
        self.crm_widget.hide()
        self.sidebar.add_widget(self.crm_widget)
    
        # Create UI components in the correct order
        self.create_menu_bar()
        self.create_ribbon()
        self.create_main_area()  # This creates self.loan_listbox
        
        # Apply initial theme
        self.apply_initial_theme()
        
        # Carica i prestiti esistenti dopo aver creato l'UI
        self.load_existing_loans()

        self.setup_shortcuts()

    def create_menu_bar(self):
        menubar = self.menuBar()
    
        # View menu
        view_menu = menubar.addMenu('View')
    
        # Theme action
        theme_action = QAction('Toggle Theme', self)
        theme_action.triggered.connect(self.toggle_theme)
        theme_action.setShortcut('Ctrl+T')
        view_menu.addAction(theme_action)

    def create_ribbon(self):
        ribbon_widget = QWidget()
        ribbon_widget.setObjectName("ribbon")
        ribbon_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f8f8;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        ribbon_layout = QVBoxLayout(ribbon_widget)
        ribbon_layout.setSpacing(0)
        ribbon_layout.setContentsMargins(0, 0, 0, 0)

        # Set fixed height for ribbon
        ribbon_widget.setFixedHeight(80)

        # Create adaptive ribbon tab
        ribbon_tab = AdaptiveRibbonTab()

        # Loan Operations Group
        loan_group = CollapsibleRibbonGroup("Loan Operations")
        new_loan_btn = AdaptiveRibbonButton("New Loan", resource_path("add_icon.png"))
        new_loan_btn.clicked.connect(self.new_loan)
        edit_loan_btn = AdaptiveRibbonButton("Edit Loan", resource_path("edit.png"))
        edit_loan_btn.clicked.connect(self.edit_loan)
        delete_loan_btn = AdaptiveRibbonButton("Delete Loan", resource_path("delete_icon.png"))
        delete_loan_btn.clicked.connect(self.delete_loan)
        loan_group.add_button(new_loan_btn)
        loan_group.add_button(edit_loan_btn)
        loan_group.add_button(delete_loan_btn)

        # Analysis Group
        analysis_group = CollapsibleRibbonGroup("Analysis")
        payment_btn = AdaptiveRibbonButton("Payment", resource_path("payment.png"))
        payment_btn.clicked.connect(self.pmt)
        amort_btn = AdaptiveRibbonButton("Amortization", resource_path("amort.png"))
        amort_btn.clicked.connect(self.amort)
        plot_btn = AdaptiveRibbonButton("Plot", resource_path("plot_balances.png"))
        plot_btn.clicked.connect(self.plot)
        payment_analysis_btn = AdaptiveRibbonButton("Payment Analysis", resource_path("analysis.png"))
        payment_analysis_btn.clicked.connect(self.open_payment_analysis)

        
        analysis_group.add_button(payment_btn)
        analysis_group.add_button(amort_btn)
        analysis_group.add_button(plot_btn)
        analysis_group.add_button(payment_analysis_btn)



        # Tools Group
        tools_group = CollapsibleRibbonGroup("Tools")
        compare_btn = AdaptiveRibbonButton("Compare", resource_path("compare.png"))
        compare_btn.clicked.connect(self.compare_loans)
        consolidate_btn = AdaptiveRibbonButton("Consolidate", resource_path("consolidate.png"))
        consolidate_btn.clicked.connect(self.consolidate_loans)
        taeg_btn = AdaptiveRibbonButton("TAEG", resource_path("taeg.png"))
        taeg_btn.clicked.connect(self.open_taeg_dialog)

        prob_pricing_btn = AdaptiveRibbonButton("Probabilistic Pricing", resource_path("pricing.png"))
        prob_pricing_btn.clicked.connect(self.open_probabilistic_pricing)
        analysis_group.add_button(prob_pricing_btn)
        tools_group.add_button(compare_btn)
        tools_group.add_button(consolidate_btn)
        tools_group.add_button(taeg_btn)

        # AI Assistant Group
        ai_group = CollapsibleRibbonGroup("AI Assistant")
        assistant_btn = AdaptiveRibbonButton(
            "AI Assistant",
            resource_path("chatbot_icon.png")
        )
        assistant_btn.clicked.connect(self.open_ai_assistant)
        ai_group.add_button(assistant_btn)
            

        # Add groups to ribbon tab
        ribbon_tab.add_group(loan_group)
        ribbon_tab.add_group(analysis_group)
        ribbon_tab.add_group(tools_group)
        ribbon_tab.add_group(ai_group) 

        ribbon_layout.addWidget(ribbon_tab)
        self.main_layout.addWidget(ribbon_widget)

    def create_main_area(self):

        # Container per sidebar e area principale
        content_container = QWidget()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
          
        # Main container with stretch
        main_container = QWidget()
        main_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(20, 20, 20, 20)
    
        # Loans list with stretch
        self.loan_listbox = QListWidget()
        self.loan_listbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.loan_listbox.itemSelectionChanged.connect(self.select_loan)
        main_layout.addWidget(self.loan_listbox)
    
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(main_container)
        self.main_layout.addWidget(content_container)  # Questa è la riga corretta

    def toggle_crm_widget(self):
        """Toggle visibility of CRM widget"""
        if self.crm_widget.isVisible():
            self.crm_widget.hide()
        else:
            # Aggiorna la lista dei clienti prima di mostrare
            self.crm_widget.load_clients()
            self.crm_widget.show()

    def apply_initial_theme(self):
        """Applica gli stili del tema iniziale a tutti i componenti"""
        # Applica stili di base
        self.setStyleSheet(self.theme_manager.get_stylesheet())

        # Applica stili specifici per il ribbon
        ribbon_widget = self.findChild(QWidget, "ribbon")
        if ribbon_widget:
            self.theme_manager.apply_theme_to_widget(ribbon_widget, "ribbon")

        # Applica stili ai gruppi del ribbon
        for group in self.findChildren(CollapsibleRibbonGroup):
            self.theme_manager.apply_theme_to_widget(group, "ribbon")

        # Applica stili ai bottoni del ribbon
        for button in self.findChildren(AdaptiveRibbonButton):
            self.theme_manager.apply_theme_to_widget(button, "ribbon")

        # Applica stili alla main area
        if self.loan_listbox:
            self.theme_manager.apply_theme_to_widget(self.loan_listbox, "main_area")
            
        # Applica stili alla sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.update_style()
            
        # Applica stili al widget CRM
        if hasattr(self, 'crm_widget'):
            self.crm_widget.update_style()


    def load_existing_loans(self):
        """Carica i prestiti dal database e li mostra nella UI."""
        self.loans = []  # Puliamo la lista dei prestiti
        self.loan_listbox.clear()

        loans_from_db = self.db_manager.load_all_loans_from_db()  # Recuperiamo i dati

        if not loans_from_db:
            print("DEBUG: Nessun prestito trovato nel database.")  
            QMessageBox.information(self, "Info", "Nessun prestito trovato nel database.")
            return

        for loan_data in loans_from_db:
            try:
                loan_id = str(loan_data[0])
                # Carica prima i costi aggiuntivi e le spese periodiche
                additional_costs = self.db_manager.load_additional_costs(loan_id)
                periodic_expenses = self.db_manager.load_periodic_expenses(loan_id)
                
                # Crea nuovo prestito con tutti i dati
                loan = Loan(
                    db_manager=self.db_manager,
                    rate=float(loan_data[1]),
                    term=int(loan_data[2]),
                    loan_amount=float(loan_data[3]),
                    amortization_type=loan_data[4],
                    frequency=loan_data[5],
                    rate_type=loan_data[6],
                    use_euribor=loan_data[7],
                    update_frequency=loan_data[8],
                    downpayment_percent=float(loan_data[9]),
                    start=loan_data[10].isoformat(),
                    loan_id=loan_id,
                    additional_costs=additional_costs,  # Aggiungi i costi qui
                    periodic_expenses=periodic_expenses,  # Aggiungi le spese qui
                    should_save=False  # Importante: evita il doppio salvataggio
                )
                
                self.loans.append(loan)

                # Mostra il prestito nella UI
                loan_text = f"Loan {loan_id} - €{loan_data[3]:,.2f} ({loan_data[4]})"
                self.loan_listbox.addItem(loan_text)

            except Exception as e:
                print(f"Error loading loan {loan_data[0]}: {str(e)}")
                continue

        print(f"DEBUG: Prestiti caricati nella lista ({len(self.loans)})")      

    def on_close(self, event):
        """Save all loans before closing"""
        try:
            for loan in self.loans:
                loan.update_db()
            event.accept()
        except Exception as e:
            reply = QMessageBox.question(
                self, 'Error',
                f"Error saving loans: {str(e)}\nExit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
            """Gestisce il salvataggio dei dati prima della chiusura"""
            try:
                # Verifica la connessione al database
                if not self.db_manager.check_connection():
                    raise Exception("Database connection lost")
                    
                # Salva tutti i prestiti nel database
                for loan in self.loans:
                    try:
                        loan.update_db()
                    except Exception as e:
                        raise Exception(f"Error saving loan {loan.loan_id}: {str(e)}")
                        
                event.accept()
                
            except Exception as e:
                reply = QMessageBox.question(
                    self, 
                    'Error',
                    f"Error saving loans: {str(e)}\n\n"
                    "Do you want to exit anyway? Unsaved changes will be lost.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    event.accept()
                else:
                    event.ignore()
                    
    def toggle_theme(self):
        # Aggiorna il tema nel theme manager
        new_stylesheet = self.theme_manager.toggle_theme()

        # Applica gli stili di base
        self.setStyleSheet(new_stylesheet)

        # Applica stili specifici per il ribbon
        ribbon_widget = self.findChild(QWidget, "ribbon")
        if ribbon_widget:
            self.theme_manager.apply_theme_to_widget(ribbon_widget, "ribbon")

        # Applica stili ai gruppi del ribbon
        for group in self.findChildren(CollapsibleRibbonGroup):
            self.theme_manager.apply_theme_to_widget(group, "ribbon")

        # Applica stili ai bottoni del ribbon
        for button in self.findChildren(AdaptiveRibbonButton):
            self.theme_manager.apply_theme_to_widget(button, "ribbon")

        # Applica stili alla main area
        if self.loan_listbox:
            self.theme_manager.apply_theme_to_widget(self.loan_listbox, "main_area")
            
        # Aggiorna gli stili della sidebar e CRM
        if hasattr(self, 'sidebar'):
            self.sidebar.update_style()
            
        if hasattr(self, 'crm_widget'):
            self.crm_widget.update_style()

        # Mostra feedback all'utente
        theme_name = self.theme_manager.get_current_theme().capitalize()
        QMessageBox.information(self, "Theme Changed", f"Switched to {theme_name} theme")
        
    def new_loan(self):
        """Create a new loan and save it to database"""
        dialog = LoanDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                # Get loan data from dialog
                loan_data = dialog.get_loan_data()
                
                # Create new loan with auto-save enabled
                loan = Loan(
                    db_manager=self.db_manager,
                    rate=loan_data["rate"] / 100,  # Convert from percentage
                    term=loan_data["term"],
                    loan_amount=loan_data["loan_amount"],
                    amortization_type=loan_data["amortization_type"],
                    frequency=loan_data["frequency"],
                    downpayment_percent=loan_data["downpayment_percent"],
                    additional_costs=loan_data["additional_costs"],
                    periodic_expenses=loan_data.get("periodic_expenses", {}),
                    should_save=True  # Enable auto-save for new loans
                )
                
                # Create command for undo/redo functionality
                command = LoanCommand(
                    do_action=lambda: self._add_loan(loan),
                    undo_action=lambda: self._remove_loan(loan),
                    description=f"Create loan {loan.loan_id}"
                )
                
                # Execute command (this will add the loan to self.loans)
                self.add_command(command)
                
                # Update UI
                self.update_loan_listbox()
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Loan created successfully!\nMonthly payment: {loan.pmt_str}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create loan: {str(e)}"
                )
                print(f"Error creating loan: {str(e)}")
                            
    def delete_loan(self, loan_id):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this loan?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Get the loan_id from selected loan
                loan_id = self.selected_loan.loan_id
                # Use the db_manager instance method to delete
                self.selected_loan.delete_from_db()
                # Remove from loans list
                self.loans.remove(self.selected_loan)
                self.selected_loan = None
                self.update_loan_listbox()
                QMessageBox.information(self, "Success", "Loan deleted successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete loan: {str(e)}")
                print(f"Error deleting loan: {str(e)}")
                
                            
    def update_loan_listbox(self):
        self.loan_listbox.clear()
        for i, loan in enumerate(self.loans, 1):
            item_text = f"Loan {i} - {loan.loan_id} - {loan.amortization_type} amortization"
            self.loan_listbox.addItem(item_text)


    def select_loan(self):
        """Seleziona un prestito dalla lista e lo imposta come attivo."""
        index = self.loan_listbox.currentRow()

        # Controlliamo se ci sono prestiti disponibili
        if not self.loans:
            print("DEBUG: Nessun prestito in self.loans")
            QMessageBox.warning(self, "Errore", "Nessun prestito disponibile.")
            return

        # Controlliamo se l'indice è valido
        if index < 0 or index >= len(self.loans):
            print(f"DEBUG: Indice {index} fuori dal range (0-{len(self.loans)-1})")
            QMessageBox.warning(self, "Errore", "Selezione non valida.")
            return  

        # Selezioniamo il prestito come oggetto Loan
        self.selected_loan = self.loans[index]
        print(f"DEBUG: Prestito selezionato: {self.selected_loan.loan_id}")  # Ora funziona!


    def pmt(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
        
        payment_info = (f"Monthly Payment: {self.selected_loan.pmt_str}" if self.selected_loan.amortization_type == "French"
                       else f"Initial Payment: €{self.selected_loan.table['Payment'].iloc[0]:,.2f}")
        QMessageBox.information(self, "Payment Information", payment_info)

    def open_payment_analysis(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
    
        dialog = LoanPaymentAnalysisDialog(self.selected_loan, self)
        dialog.exec_()

    def amort(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
    
        if self.selected_loan.table.isnull().values.any():
            QMessageBox.warning(self, "Error", "The amortization table contains invalid values.")
            return
    
        dialog = AmortizationDialog(self.selected_loan.table, self)
        dialog.exec_()


    def plot(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
    
        plot_dialog = PlotDialog(self.selected_loan, self)
        plot_dialog.exec_()

    def compare_loans(self):
        if len(self.loans) < 2:
            QMessageBox.warning(self, "Error", "Please create at least two loans to compare")
            return
        
        comparison_text = Loan.compare_loans(self.loans)
        dialog = LoanComparisonDialog(comparison_text, self)
        dialog.exec_()

    def consolidate_loans(self):
        if len(self.loans) < 2:
            QMessageBox.warning(self, "Error", "Please create at least two loans to consolidate")
            return
        
        dialog = ConsolidateLoansDialog(self.loans, self)
        if dialog.exec_() == QDialog.Accepted and dialog.consolidated_loan:
            self.loans.append(dialog.consolidated_loan)
            self.update_loan_listbox()

    def open_taeg_dialog(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
        
        dialog = TAEGCalculationDialog(self.selected_loan, self)
        dialog.exec_()

    def open_probabilistic_pricing(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return
            
        dialog = ProbabilisticPricingDialog(self.selected_loan, self)
        dialog.exec_()


    def open_ai_assistant(self):
        """Opens the AI assistant dialog"""
        dialog = ChatAssistantDialog(self)
        dialog.db_manager = self.db_manager  # This is the db_manager from login
        dialog.exec_()

    def open_reports(self):
        """Opens the reports dialog"""
        dialog = ReportsDialog(self.db_manager, self.crm_manager, self.loans, self)
        dialog.exec_()

    def setup_shortcuts(self):
        """Configura le scorciatoie da tastiera per do/undo"""
        from PyQt5.QtGui import QKeySequence
        from PyQt5.QtWidgets import QShortcut
    
        # Crea shortcut per Undo (Ctrl+Z)
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_action)
    
        # Crea shortcut per Redo (Ctrl+Y)
        self.redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        self.redo_shortcut.activated.connect(self.redo_action)

    def add_command(self, command):
        """Aggiunge un comando allo stack e lo esegue"""
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()  # Pulisce lo stack di redo quando viene eseguita una nuova azione

    def undo_action(self):
        """Annulla l'ultima azione"""
        if self.undo_stack:
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self.update_loan_listbox()

    def redo_action(self):
        """Ripete l'ultima azione annullata"""
        if self.redo_stack:
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            self.update_loan_listbox()

# 3. Modifica i metodi che gestiscono le azioni sui prestiti per utilizzare i comandi

    def new_loan(self):
        dialog = LoanDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            loan_data = dialog.get_loan_data()
            try:
                loan = Loan(**loan_data)
                command = LoanCommand(
                    do_action=lambda: self._add_loan(loan),
                    undo_action=lambda: self._remove_loan(loan),
                    description="Create new loan"
                )
                self.add_command(command)
                QMessageBox.information(self, "Success", "Loan created successfully")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))


    def new_loan(self):
        dialog = LoanDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            loan_data = dialog.get_loan_data()
            try:
                loan = Loan(db_manager=self.db_manager, **loan_data)
                command = LoanCommand(
                    do_action=lambda: self._add_loan(loan),
                    undo_action=lambda: self._remove_loan(loan),
                    description="Create new loan"
                )
                self.add_command(command)
                QMessageBox.information(self, "Success", "Loan created successfully")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))


    def _add_loan(self, loan):
        """Add loan to both memory and database"""
        try:
            # Add to memory list
            self.loans.append(loan)
            
            # Save to database
            loan.save_to_db()
            
            # Update UI
            self.update_loan_listbox()
            
            # Show success message
            QMessageBox.information(
                self, 
                "Success", 
                f"Loan {loan.loan_id} successfully saved"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to save loan: {str(e)}"
            )
            # Remove from memory if database save failed
            if loan in self.loans:
                self.loans.remove(loan)
                
    def _remove_loan(self, loan):
        try:
            index = self.loans.index(loan)
            if index >= 0:
                # Remove from the list
                del self.loans[index]
                # Update the UI
                self.update_loan_listbox()
                # Reset selected loan if it was the one removed
                if self.selected_loan == loan:
                    self.selected_loan = None
        except ValueError:
            QMessageBox.warning(self, "Error", "Could not find loan to remove")
            return False
        return True

    def edit_loan(self):
        if not self.selected_loan:
            QMessageBox.warning(self, "Error", "Please select a loan first")
            return

        # Ensure the selected loan has a valid db_manager
        if self.selected_loan.db_manager is None:
            self.selected_loan.db_manager = self.db_manager
            print(f"Repaired db_manager for loan {self.selected_loan.loan_id}")

        dialog = EditLoanDialog(self.selected_loan, self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                loan_data = dialog.get_updated_loan_data()
                
                # Store old data for undo functionality
                old_data = {
                    "new_rate": self.selected_loan.initial_rate * 100,  # Convert to percentage
                    "new_term": self.selected_loan.initial_term,
                    "new_loan_amount": self.selected_loan.loan_amount,
                    "new_downpayment_percent": self.selected_loan.downpayment_percent,
                    "new_amortization_type": self.selected_loan.amortization_type,
                    "new_frequency": self.selected_loan.frequency
                }
                
                # Create and execute command
                command = LoanCommand(
                    do_action=lambda: self._update_loan(self.selected_loan, loan_data),
                    undo_action=lambda: self._update_loan(self.selected_loan, old_data),
                    description=f"Edit loan {self.selected_loan.loan_id}"
                )
                
                self.add_command(command)
                QMessageBox.information(self, "Success", "Loan updated successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update loan: {str(e)}")


    def _update_loan(self, loan, data):
        """Helper method to update a loan and save to database"""
        try:
            # Update loan attributes and save to database
            loan.edit_loan(
                new_rate=data['new_rate'],
                new_term=data['new_term'],
                new_loan_amount=data['new_loan_amount'],
                new_amortization_type=data['new_amortization_type'],
                new_frequency=data['new_frequency'],
                new_downpayment_percent=data['new_downpayment_percent']
            )
            
            # Update UI
            self.update_loan_listbox()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update loan: {str(e)}"
            )
            raise
        # Initialize chatbot

        self.chatbot = Chatbot("intents.json")
        
    def display_loans(self):
        """Returns a formatted string of all loans for the chatbot"""
        if not self.loans:
            return "No loans found."
            
        loans_info = ["Current Loans:"]
        for loan in self.loans:
            loans_info.append(
                f"\nLoan ID: {loan.loan_id}"
                f"\nAmount: €{loan.loan_amount:,.2f}"
                f"\nRate: {loan.initial_rate * 100:.2f}%"
                f"\nType: {loan.amortization_type}"
                f"\n---"
            )
        return "\n".join(loans_info)

class ConsolidateLoansDialog(FluentDialog):
    def __init__(self, loans, parent=None):
        super().__init__("Consolidate Loans", parent)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.loans = loans
        self.selected_loans = []
        self.consolidated_loan = None
        
        # Create loan selection list
        self.loan_list = QListWidget()
        self.loan_list.setSelectionMode(QListWidget.MultiSelection)
        for loan in loans:
            item_text = f"Loan ID: {loan.loan_id}, Amount: €{loan.loan_amount:,.2f}, Rate: {loan.initial_rate * 100:.2f}%"
            self.loan_list.addItem(item_text)
        
        # Create frequency selection
        frequency_layout = QHBoxLayout()
        frequency_label = QLabel("Payment Frequency:")
        self.frequency_combobox = QComboBox()
        self.frequency_combobox.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        frequency_layout.addWidget(frequency_label)
        frequency_layout.addWidget(self.frequency_combobox)
        
        # Add widgets to main layout
        self.main_layout.insertWidget(0, self.loan_list)
        self.main_layout.insertLayout(1, frequency_layout)
        
        # Create buttons
        consolidate_button = QPushButton("Consolidate Loans")
        consolidate_button.clicked.connect(self.consolidate_loans)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                color: black;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        self.button_layout.addWidget(cancel_button)
        self.button_layout.addWidget(consolidate_button)

    def consolidate_loans(self):
        selected_items = self.loan_list.selectedItems()
        selected_indices = [self.loan_list.row(item) for item in selected_items]
        self.selected_loans = [self.loans[i] for i in selected_indices]
        
        if len(self.selected_loans) < 2:
            QMessageBox.warning(self, "Error", "Please select at least two loans to consolidate")
            return
        
        frequency = self.frequency_combobox.currentText()
        try:
            self.consolidated_loan = Loan.consolidate_loans(self.selected_loans, frequency)
            QMessageBox.information(self, "Success", "Loans consolidated successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Consolidation failed: {str(e)}")

class ProbabilisticPricingDialog(FluentDialog):
    def __init__(self, loan, parent=None):
        super().__init__("Probabilistic Loan Pricing", parent)
        self.loan = loan
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()
        self.apply_styles()

        
    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create scrollable area
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        
        # Parameters section
        params_group = QWidget()
        form = QFormLayout(params_group)
        form.setSpacing(10)
        
        # Section headers
        params_label = QLabel("Model Parameters")
        params_label.setProperty("class", "section-header")
        
        # Initialize inputs with styling
        self.initial_default = self.create_double_spinbox(0.2)
        self.default_decay = self.create_double_spinbox(0.9)
        self.final_default = self.create_double_spinbox(0.4)
        self.recovery_rate = self.create_double_spinbox(0.4)
        self.iterations = self.create_spinbox(100, 10, 100000)
        
        # Add tooltips
        self.initial_default.setToolTip("Initial probability of default (0-1)")
        self.default_decay.setToolTip("Rate at which default probability decays")
        
        # Lists section
        lists_label = QLabel("Simulation Parameters")
        lists_label.setProperty("class", "section-header")
        
        self.loan_lives = self.create_line_edit("5,10,20")
        self.interest_rates = self.create_line_edit("0.30,0.35,0.40")
        self.default_probs = self.create_line_edit("0.1,0.2,0.3")
        
        # Add form rows with consistent spacing
        form.addRow(params_label)
        form.addRow(self.create_label("Initial Default:"), self.initial_default)
        form.addRow(self.create_label("Default Decay:"), self.default_decay)
        form.addRow(self.create_label("Final Default:"), self.final_default)
        form.addRow(self.create_label("Recovery Rate:"), self.recovery_rate)
        form.addRow(self.create_label("Iterations:"), self.iterations)
        
        form.addRow(lists_label)
        form.addRow(self.create_label("Loan Lives (years):"), self.loan_lives)
        form.addRow(self.create_label("Interest Rates:"), self.interest_rates)
        form.addRow(self.create_label("Default Probabilities:"), self.default_probs)
        
        # Results view
        self.results_view = QTextEdit()
        self.results_view.setReadOnly(True)
        self.results_view.setMinimumHeight(300)
        
        # Button layout
        button_layout = QHBoxLayout()
        calculate_btn = QPushButton("Calculate Pricing")
        calculate_btn.setProperty("class", "primary-button")
        calculate_btn.clicked.connect(self.calculate_pricing)
        button_layout.addStretch()
        button_layout.addWidget(calculate_btn)
        
        # Assemble layout
        main_layout.addWidget(params_group)
        main_layout.addWidget(self.results_view)
        main_layout.addLayout(button_layout) 
        
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll)
    
    def clear_layout(self):
        """Rimuove tutti i widget dal layout"""
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
    def show_results(self, data):
        # Pulisci il layout esistente
        self.clear_layout()
        
    def create_double_spinbox(self, default_value):
        spinbox = QDoubleSpinBox()
        spinbox.setRange(0, 1)
        spinbox.setValue(default_value)
        spinbox.setDecimals(2)
        spinbox.setSingleStep(0.05)
        spinbox.setProperty("class", "spinbox")
        return spinbox
    
    def create_spinbox(self, default_value, min_val, max_val):
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_value)
        spinbox.setSingleStep(10)
        spinbox.setProperty("class", "spinbox")
        return spinbox
    
    def create_line_edit(self, placeholder):
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setProperty("class", "line-edit")
        return line_edit
    
    def create_label(self, text):
        label = QLabel(text)
        label.setProperty("class", "form-label")
        return label
    
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            .section-header {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px 0;
            }
            .form-label {
                color: #34495e;
                font-weight: 500;
            }
            .spinbox, .line-edit {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
            .primary-button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            .primary-button:hover {
                background-color: #2980b9;
            }
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
            }
        """)

    def parse_comma_list(self, text, convert_type=float):
        """Parse comma-separated values into list"""
        try:
            return [convert_type(x.strip()) for x in text.split(',') if x.strip()]
        except ValueError:
            raise ValueError(f"Invalid format. Expected comma-separated {convert_type.__name__} values")
    
    def calculate_pricing(self):
        try:
            # Parse input lists
            loan_lives = self.parse_comma_list(self.loan_lives.text(), int) if self.loan_lives.text() else None
            interest_rates = np.array(self.parse_comma_list(self.interest_rates.text())) if self.interest_rates.text() else None
            default_probs = self.parse_comma_list(self.default_probs.text()) if self.default_probs.text() else None
            
            # Calculate results
            results = self.loan.calculate_probabilistic_pricing(
                initial_default=self.initial_default.value(),
                default_decay=self.default_decay.value(),
                final_default=self.final_default.value(),
                recovery_rate=self.recovery_rate.value(),
                num_iterations=self.iterations.value(),
                loan_lives=loan_lives,
                interest_rates=interest_rates,
                default_probabilities=default_probs
            )
            
            # Convert styled DataFrame to HTML and display
            self.results_view.setHtml(results.to_html())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to calculate pricing: {str(e)}")


class LoanSelectionDialog(FluentDialog):
    def __init__(self, loans, multi_select=False, parent=None):
        super().__init__("Select Loan(s)", parent)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.selected_loans = []
        
        # Main layout
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Search bar
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 10)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search loans...")
        self.search_input.textChanged.connect(self.filter_loans)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #0078D4;
                background-color: #ffffff;
            }
        """)
        search_layout.addWidget(self.search_input)
        
        # Loans list
        self.loans_list = QListWidget()
        self.loans_list.setSelectionMode(
            QListWidget.MultiSelection if multi_select else QListWidget.SingleSelection
        )
        self.loans_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e5f3ff;
                color: #000000;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        
        # Populate loans
        self.loans = loans
        self.populate_loans()
        
        # Add widgets to layout
        layout.addWidget(search_container)
        layout.addWidget(self.loans_list)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidget(main_widget)
        scroll.setWidgetResizable(True)
        self.main_layout.insertWidget(0, scroll)
        
        # Buttons
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        self.button_layout.addWidget(cancel_btn)
        self.button_layout.addWidget(select_btn)

    def filter_loans(self):
        filter_text = self.search_input.text()
        self.populate_loans(filter_text)
        
    def populate_loans(self, filter_text=""):
        """Popola la lista dei prestiti con filtro opzionale"""
        self.loans_list.clear()
        for loan in self.loans:
            # Crea il testo dell'item
            item_text = (f"Loan {loan.loan_id}\n"
                        f"Amount: €{loan.loan_amount:,.2f}\n"
                        f"Rate: {loan.initial_rate * 100:.2f}%\n"
                        f"Type: {loan.amortization_type}")
            
            # Applica il filtro se presente
            if filter_text.lower() in item_text.lower():
                # Crea l'item
                item = QListWidgetItem(item_text)
                # Salva il riferimento al prestito nell'item
                item.setData(Qt.UserRole, loan)
                # Aggiungi l'item alla lista
                self.loans_list.addItem(item)

    def get_selected_loans(self):
        """Restituisce i prestiti selezionati"""
        selected_items = self.loans_list.selectedItems()
        return [item.data(Qt.UserRole) for item in selected_items]

class  ChatAssistantDialog(QDialog):

    def __init__(self, loan_app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LoanManager AI Assistant")
        self.loan_app = loan_app
        self.db_manager = loan_app.db_manager
        # Aggiungi l'icona della finestra
        self.setWindowIcon(QIcon(resource_path('loan_icon.ico')))
        # Costruiamo il percorso assoluto al file degli intent
        intents_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'intents.json')
        self.chatbot = Chatbot("intents.json", db_manager=self.db_manager)
        # Sostituisci la conferma operatore con una versione GUI
        self.chatbot.operator_confirmation = lambda prompt: self.gui_operator_confirmation(prompt)
        self.main_layout = QVBoxLayout(self)
        # Stato della conversazione per gestire i flussi
        self.current_conversation_state = None
        self.conversation_data = {}
        self.setup_ui()
        self.setup_styles()
        
    def setup_ui(self):
        # Imposta dimensione minima e background
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        # Container principale per la chat
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setSpacing(0)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QWidget()
        header.setObjectName("chatHeader")
        header_layout = QHBoxLayout(header)
        
        # Avatar dell'assistente
        avatar_label = QLabel()
        avatar_pixmap = QPixmap(resource_path("chatbot_icon.png")).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        avatar_label.setPixmap(avatar_pixmap)
        
        # Nome e stato dell'assistente
        name_status = QVBoxLayout()
        name_label = QLabel("LoanManager Assistant")
        name_label.setObjectName("assistantName")
        status_label = QLabel("Online")
        status_label.setObjectName("assistantStatus")
        name_status.addWidget(name_label)
        name_status.addWidget(status_label)
        
        header_layout.addWidget(avatar_label)
        header_layout.addLayout(name_status)
        header_layout.addStretch()
        
        # Area di chat con background personalizzato
        chat_bg = QWidget()
        chat_bg.setObjectName("chatBackground")
        chat_bg_layout = QVBoxLayout(chat_bg)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setFrameShape(QFrame.NoFrame)
        chat_bg_layout.addWidget(self.chat_history)
        
        # Area di input del messaggio
        input_container = QWidget()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 15, 15, 15)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setObjectName("messageInput")
        self.message_input.returnPressed.connect(self.send_message)
        
        send_button = QPushButton()
        send_button.setObjectName("sendButton")
        send_button.setIcon(QIcon(resource_path("send_icon.png")))
        send_button.setIconSize(QSize(20, 20))
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        
        # Aggiungi i componenti al layout principale
        chat_layout.addWidget(header)
        chat_layout.addWidget(chat_bg)
        chat_layout.addWidget(input_container)
        self.main_layout.insertWidget(0, chat_container)
        
        # Messaggio di benvenuto con animazione di digitazione
        QTimer.singleShot(500, lambda: self.animate_typing(
            "Assistant", 
            "Hello! I'm your LoanManager AI Assistant. How can I help you today? 👋"
        ))
    
    def setup_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            #chatHeader {
                background-color: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
                padding: 15px;
                min-height: 60px;
            }
            
            #assistantName {
                color: #212529;
                font-size: 16px;
                font-weight: bold;
            }
            
            #assistantStatus {
                color: #28a745;
                font-size: 12px;
            }
            
            #chatBackground {
                background-color: #f8f9fa;
            }
            
            #chatHistory {
                background-color: transparent;
                border: none;
                padding: 20px;
                font-size: 14px;
            }
            
            #inputContainer {
                background-color: #ffffff;
                border-top: 1px solid #e9ecef;
            }
            
            #messageInput {
                border: 1px solid #e9ecef;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                min-height: 40px;
                background-color: #f8f9fa;
            }
            
            #messageInput:focus {
                border-color: #0078D4;
                background-color: #ffffff;
            }
            
            #sendButton {
                background-color: #0078D4;
                border-radius: 20px;
                min-width: 40px;
                min-height: 40px;
                margin-left: 10px;
            }
            
            #sendButton:hover {
                background-color: #106EBE;
            }
            
            QScrollBar:vertical {
                border: none;
                background-color: #f8f9fa;
                width: 10px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                min-height: 30px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
    
    def animate_typing(self, sender, message):
        """Anima l'indicatore di digitazione prima di mostrare il messaggio"""
        typing_indicator = "Typing..."
        self.append_message(sender, typing_indicator, is_typing=True)
        QTimer.singleShot(1500, lambda: self.replace_last_message(sender, message))
    
    def replace_last_message(self, sender, message):
        """Sostituisce l'ultimo messaggio nella cronologia della chat"""
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.StartOfBlock, cursor.KeepAnchor)
        cursor.removeSelectedText()
        self.append_message(sender, message)
        
    def send_message(self):
        """Gestisce l'invio di messaggi e il flusso della conversazione"""
        user_message = self.message_input.text().strip()
        if not user_message:
            return

        self.append_message("User", user_message)
        self.message_input.clear()

        # Usa QTimer.singleShot per gestire la risposta in modo asincrono
        QTimer.singleShot(0, lambda: self.process_message(user_message))


    def start_crm_conversation(self, intent_type):
        """Avvia una conversazione CRM basata sul tipo di intent"""
        self.current_conversation_state = f"crm_{intent_type}"
        self.conversation_data = {"intent": intent_type}
        
        # Imposta il messaggio iniziale in base al tipo di intent
        if intent_type == "add_client":
            self.append_message("Assistant", "Let's add a new client. What's the client's first name?")
        elif intent_type == "update_client":
            self.append_message("Assistant", "Please enter the ID of the client you want to update:")
        elif intent_type == "delete_client":
            self.append_message("Assistant", "Please enter the ID of the client you want to delete:")
        elif intent_type == "get_client":
            self.append_message("Assistant", "Please enter the ID of the client you want to view:")
        elif intent_type == "assign_loan_to_client":
            self.append_message("Assistant", "Please enter the ID of the client you want to assign a loan to:")
        elif intent_type == "record_client_interaction":
            self.append_message("Assistant", "Please enter the ID of the client you want to record an interaction for:")
        elif intent_type == "get_client_interactions":
            self.append_message("Assistant", "Please enter the ID of the client to view their interactions:")
        elif intent_type == "get_client_loans":
            self.append_message("Assistant", "Please enter the ID of the client to view their loans:")
        elif intent_type == "get_client_details":
            self.append_message("Assistant", "Please enter the ID of the client to view their complete profile:")
        elif intent_type == "add_corporation":
            self.append_message("Assistant", "Let's add a new corporation. What's the company name?")
        elif intent_type == "update_corporation":
            self.append_message("Assistant", "Please enter the ID of the corporation you want to update:")
        elif intent_type == "delete_corporation":
            self.append_message("Assistant", "Please enter the ID of the corporation you want to delete:")
        elif intent_type == "get_corporation":
            self.append_message("Assistant", "Please enter the ID of the corporation you want to view:")
        elif intent_type == "assign_loan_to_corporation":
            self.append_message("Assistant", "Please enter the ID of the corporation you want to assign a loan to:")
        elif intent_type == "record_corporation_interaction":
            self.append_message("Assistant", "Please enter the ID of the corporation you want to record an interaction for:")
        elif intent_type == "get_corporation_interactions":
            self.append_message("Assistant", "Please enter the ID of the corporation to view their interactions:")
        elif intent_type == "get_corporation_loans":
            self.append_message("Assistant", "Please enter the ID of the corporation to view their loans:")
        elif intent_type == "get_corporation_details":
            self.append_message("Assistant", "Please enter the ID of the corporation to view their complete profile:")


    def process_message(self, user_message):
        """Processa il messaggio in modo asincrono"""
        try:
            # Se siamo in uno stato di conversazione, gestiamo quello
            if self.current_conversation_state:
                if self.current_conversation_state.startswith("create_loan"):
                    self.handle_create_loan_conversation(user_message)
                elif self.current_conversation_state.startswith("update_loan"):
                    self.handle_update_loan_conversation(user_message)
                elif self.current_conversation_state.startswith("pricing"):
                    self.handle_pricing_conversation(user_message)
                elif self.current_conversation_state.startswith("payment"):
                    self.handle_payment_conversation(user_message)
                elif self.current_conversation_state.startswith("crm_"):
                    self.handle_crm_conversation(user_message)
                return

            # Altrimenti procediamo con il normale flusso di intent
            intent = self.chatbot.get_intent(user_message)
            
            # Verifica la validità del contesto
            is_valid, error_message = self.chatbot.validate_context(
                intent, 
                self.loan_app.selected_loan
            )
            
            if not is_valid:
                self.append_message("Assistant", error_message)
                return
                
            # Gestisci gli intent speciali in modo asincrono
            if intent in ["create_loan", "update_loan", "pricing_analysis", "payment_analysis"]:
                self.handle_special_intent(intent)
            else:
                # Gestisci gli intent standard
                self.handle_standard_intent(intent)

        except Exception as e:
            self.append_message("Assistant", f"An error occurred: {str(e)}")

        
    def handle_special_intent(self, intent):
        """Gestisce gli intent speciali che richiedono dialoghi"""
        if intent == "create_loan":
            self.current_conversation_state = "create_loan_amount"
            self.conversation_data = {}
            self.append_message("Assistant", "Let's create a new loan. What's the loan amount?")
            
        elif intent == "update_loan":
            if not self.loan_app.selected_loan:
                self.append_message("Assistant", "Please select a loan first using the main interface.")
                return
            self.current_conversation_state = "update_loan_field"
            self.conversation_data = {"loan": self.loan_app.selected_loan}
            self.append_message("Assistant", 
                "What would you like to update?\n" +
                "1. Interest rate\n" +
                "2. Term\n" +
                "3. Loan amount\n" +
                "4. Payment frequency")
                
        elif intent == "pricing_analysis":
            if not self.loan_app.selected_loan:
                self.append_message("Assistant", "Please select a loan first using the main interface.")
                return
            self.current_conversation_state = "pricing_initial_default"
            self.conversation_data = {"loan": self.loan_app.selected_loan}
            self.append_message("Assistant", "What's the initial default probability? (0-1)")
            
        elif intent == "payment_analysis":
            if not self.loan_app.selected_loan:
                self.append_message("Assistant", "Please select a loan first using the main interface.")
                return
            self.current_conversation_state = "payment_type"
            self.conversation_data = {"loan": self.loan_app.selected_loan}
            self.append_message("Assistant", 
                "How would you like to analyze payments?\n" +
                "1. Early payoff with extra payments\n" +
                "2. Faster payoff in fewer years")

    def handle_standard_intent(self, intent):
        """Gestisce gli intent standard che non richiedono dialoghi"""
        base_intent_actions = {
            "greeting": lambda: self.append_message("Assistant", 
                                    np.random.choice([
                                        "Hi! How can I help you with your loans?",
                                        "Hello! I'm here to help you manage your loans.",
                                        "Good day! What can I do for you today?"
                                    ])),
            "thanks": lambda: self.append_message("Assistant",
                                    np.random.choice([
                                        "You're welcome!",
                                        "No problem!",
                                        "Glad to help!"
                                    ])),
            "display_loans": lambda: self.show_loans(allow_selection=True),
            "amortization_schedule": lambda: self._handle_amortization(),
            "calculate_taeg": lambda: self._handle_taeg(),
            "compare_loans": lambda: self._handle_compare_loans(),
            "plot_graph": lambda: self._handle_plot()
        }

        # Aggiunta Intent CRM per clienti
        client_intent_actions = {
            "add_client": lambda: self.start_crm_conversation("add_client"),
            "update_client": lambda: self.start_crm_conversation("update_client"),
            "delete_client": lambda: self.start_crm_conversation("delete_client"),
            "get_client": lambda: self.start_crm_conversation("get_client"),
            "list_clients": lambda: self._handle_list_clients(),
            "assign_loan_to_client": lambda: self.start_crm_conversation("assign_loan_to_client"),
            "record_client_interaction": lambda: self.start_crm_conversation("record_client_interaction"),
            "get_client_interactions": lambda: self.start_crm_conversation("get_client_interactions"),
            "get_client_loans": lambda: self.start_crm_conversation("get_client_loans"),
            "get_client_details": lambda: self.start_crm_conversation("get_client_details")
        }
        
        # Aggiunta Intent CRM per aziende
        corporation_intent_actions = {
            "add_corporation": lambda: self.start_crm_conversation("add_corporation"),
            "update_corporation": lambda: self.start_crm_conversation("update_corporation"),
            "delete_corporation": lambda: self.start_crm_conversation("delete_corporation"),
            "get_corporation": lambda: self.start_crm_conversation("get_corporation"),
            "list_corporations": lambda: self._handle_list_corporations(),
            "assign_loan_to_corporation": lambda: self.start_crm_conversation("assign_loan_to_corporation"),
            "record_corporation_interaction": lambda: self.start_crm_conversation("record_corporation_interaction"),
            "get_corporation_interactions": lambda: self.start_crm_conversation("get_corporation_interactions"),
            "get_corporation_loans": lambda: self.start_crm_conversation("get_corporation_loans"),
            "get_corporation_details": lambda: self.start_crm_conversation("get_corporation_details")
        }

        # Combina tutti gli intent
        intent_actions = {**base_intent_actions, **client_intent_actions, **corporation_intent_actions}

        if intent in intent_actions:
            intent_actions[intent]()
        else:
            self.append_message("Assistant", 
                "I apologize, but I don't understand that request. Here are some things I can help you with:\n" +
                "- Create a new loan\n" +
                "- Delete a loan\n" +
                "- Update loan details\n" +
                "- Show amortization schedule\n" +
                "- Compare loans\n" +
                "- Calculate TAEG\n" +
                "- Analyze loan pricing\n" +
                "- Show all loans"
            )

    def _handle_compare_loans(self):
        """Gestisce la comparazione dei prestiti"""
        # Verifica che ci siano almeno 2 prestiti da confrontare
        if len(self.loan_app.loans) < 2:
            self.append_message(
                "Assistant", 
                "You need at least two loans to make a comparison. Please create more loans first."
            )
            return
            
        try:
            # Genera la comparazione usando il metodo statico della classe Loan
            comparison_text = Loan.compare_loans(self.loan_app.loans)
            
            # Mostra il dialog di comparazione
            dialog = LoanComparisonDialog(comparison_text, self)
            
            if dialog.exec_() == QDialog.Accepted:
                # Formatta il testo della comparazione per la chat
                formatted_text = (
                    "Here's the loan comparison:\n\n"
                    f"{comparison_text}\n\n"
                    "Key findings:\n"
                    "- The loans have been compared based on their total cost and payment structure\n"
                    "- Consider the different terms and rates when making your decision\n"
                    "- Remember to factor in any additional costs or fees"
                )
                self.append_message("Assistant", formatted_text)
            else:
                self.append_message("Assistant", "Comparison view cancelled.")
                
        except Exception as e:
            self.append_message(
                "Assistant", 
                f"Error generating loan comparison: {str(e)}\n"
                "Please make sure all loans have valid data."
            )


    def show_loans(self, allow_selection=True, multi_select=False):
        """Shows loans and optionally allows selection"""
        if not self.loan_app.loans:
            self.append_message("Assistant", "No loans found in the system.")
            return None

        if allow_selection:
            dialog = LoanSelectionDialog(self.loan_app.loans, multi_select=multi_select, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                selected_loans = dialog.get_selected_loans()
                if selected_loans:
                    if multi_select:
                        summary = "Selected loans:\n"
                        for loan in selected_loans:
                            summary += f"- Loan {loan.loan_id}: €{loan.loan_amount:,.2f}\n"
                    else:
                        loan = selected_loans[0]
                        # Imposta il prestito selezionato nell'applicazione principale
                        self.loan_app.selected_loan = loan
                        summary = (f"Selected loan {loan.loan_id}:\n"
                                f"Amount: €{loan.loan_amount:,.2f}\n"
                                f"Rate: {loan.initial_rate * 100:.2f}%\n"
                                f"Type: {loan.amortization_type}")
                    self.append_message("Assistant", summary)
                    return selected_loans
                else:
                    self.append_message("Assistant", "No loans selected.")
                    return None
            else:
                self.append_message("Assistant", "Selection cancelled.")
                return None
        else:
            # Just show the loans without selection
            loans_info = "Available loans:\n\n"
            for loan in self.loan_app.loans:
                loans_info += (f"Loan {loan.loan_id}\n"
                            f"Amount: €{loan.loan_amount:,.2f}\n"
                            f"Rate: {loan.initial_rate * 100:.2f}%\n"
                            f"Type: {loan.amortization_type}\n"
                            f"{'─' * 30}\n")
            self.append_message("Assistant", loans_info)
            return None

    def _handle_plot(self):
        """Gestisce la visualizzazione del grafico"""
        if not self.loan_app.selected_loan:
            self.append_message("Assistant", "Please select a loan first using the main interface.")
            return
            
        try:
            dialog = PlotDialog(self.loan_app.selected_loan, self)
            if dialog.exec_() == QDialog.Accepted:
                self.append_message("Assistant", 
                    "Plot generated successfully!\n\n"
                    "The plot shows:\n"
                    "- Loan balance over time\n" 
                    "- Cumulative interest paid\n"
                    "- Important loan milestones\n\n"
                    "You can use the toolbar to:\n"
                    "- Zoom in/out\n"
                    "- Pan across the plot\n" 
                    "- Save the plot as an image")
            else:
                self.append_message("Assistant", "Plot view cancelled.")
                
        except Exception as e:
            self.append_message("Assistant", 
                f"Error generating plot: {str(e)}\n"
                "Please make sure the loan data is valid.")
            print(f"Debug - Plot error: {str(e)}")  # Per debug


    def _handle_amortization(self):
        """Gestisce la visualizzazione del piano di ammortamento"""
        if not self.loan_app.selected_loan:
            self.append_message("Assistant", "Please select a loan first using the main interface.")
            return
            
        try:
            selected_loan = self.loan_app.selected_loan
            
            # Verifica che la tabella esista e abbia dati
            if selected_loan.table is None or selected_loan.table.empty:
                self.append_message("Assistant", "Unable to generate amortization schedule. The loan table is empty.")
                return
                
            # Crea e mostra il dialog con la tabella
            dialog = AmortizationDialog(selected_loan.table, self)
            
            # Mostra il dialog come modale
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Formatta e mostra il riepilogo
                summary = (
                    "Amortization schedule displayed successfully.\n"
                    f"Total payments: {len(selected_loan.table)} installments\n"
                    f"Total interest: €{selected_loan.table['Interest'].sum():,.2f}\n"
                    f"Total amount paid: €{selected_loan.table['Payment'].sum():,.2f}"
                )
                self.append_message("Assistant", summary)
            else:
                self.append_message("Assistant", "Amortization schedule view cancelled.")
                
        except Exception as e:
            error_msg = f"Error showing amortization schedule: {str(e)}"
            self.append_message("Assistant", error_msg)
            print(f"Debug - Amortization error: {str(e)}")  # Per debug
            
    def _handle_taeg(self):
        """Gestisce il calcolo del TAEG"""
        if not self.loan_app.selected_loan:
            self.append_message("Assistant", "Please select a loan first using the main interface.")
            return
            
        try:
            dialog = TAEGCalculationDialog(self.loan_app.selected_loan, self)
            if dialog.exec_() == QDialog.Accepted:
                periodic = self.loan_app.selected_loan.taeg_periodic
                annualized = self.loan_app.selected_loan.taeg_annualized
                self.append_message("Assistant", 
                    f"TAEG calculation completed successfully!\n" +
                    f"Periodic TAEG: {periodic:.4f}%\n" +
                    f"Annualized TAEG: {annualized:.4f}%"
                )
            else:
                self.append_message("Assistant", "TAEG calculation cancelled.")
        except Exception as e:
            self.append_message("Assistant", f"Error calculating TAEG: {str(e)}")
            
    def handle_pricing_conversation(self, user_input):
        """Gestisce il flusso di conversazione per l'analisi di pricing"""
        try:
            if self.current_conversation_state == "pricing_initial_default":
                initial_default = float(user_input)
                if not 0 <= initial_default <= 1:
                    raise ValueError("Initial default must be between 0 and 1")
                
                self.conversation_data["initial_default"] = initial_default
                self.current_conversation_state = "pricing_decay"
                self.append_message("Assistant", 
                    "What's the default decay rate? (0-1)")
                    
            elif self.current_conversation_state == "pricing_decay":
                decay = float(user_input)
                if not 0 <= decay <= 1:
                    raise ValueError("Decay rate must be between 0 and 1")
                    
                self.conversation_data["decay"] = decay
                self.current_conversation_state = "pricing_recovery"
                self.append_message("Assistant", 
                    "What's the recovery rate? (0-1)")
                    
            elif self.current_conversation_state == "pricing_recovery":
                recovery = float(user_input)
                if not 0 <= recovery <= 1:
                    raise ValueError("Recovery rate must be between 0 and 1")
                    
                # Show confirmation dialog
                dialog = ProbabilisticPricingDialog(self.conversation_data["loan"], self)
                dialog.initial_default.setValue(self.conversation_data["initial_default"])
                dialog.default_decay.setValue(self.conversation_data["decay"])
                dialog.recovery_rate.setValue(recovery)
                
                if dialog.exec_() == QDialog.Accepted:
                    results = dialog.results_view.toPlainText()
                    self.append_message("Assistant", f"Pricing Analysis Results:\n{results}")
                else:
                    self.append_message("Assistant", "Analysis cancelled.")
                    
                self.current_conversation_state = None
                self.conversation_data = {}
                
        except ValueError as e:
            self.append_message("Assistant", f"Invalid input: {str(e)}. Please try again.")

    def handle_payment_conversation(self, user_input):
        """Gestisce il flusso di conversazione per l'analisi dei pagamenti"""
        try:
            if self.current_conversation_state == "payment_type":
                if user_input not in ["1", "2"]:
                    raise ValueError("Please enter 1 for early payoff or 2 for faster payoff")
                    
                self.conversation_data["analysis_type"] = user_input
                if user_input == "1":
                    self.current_conversation_state = "payment_extra_amount"
                    self.append_message("Assistant", 
                        "How much extra would you like to pay monthly? (€)")
                else:
                    self.current_conversation_state = "payment_years"
                    self.append_message("Assistant", 
                        "In how many years would you like to pay off the loan?")
                    
            elif self.current_conversation_state == "payment_extra_amount":
                extra = float(user_input)
                if extra < 0:
                    raise ValueError("Extra payment must be positive")
                    
                dialog = LoanPaymentAnalysisDialog(self.conversation_data["loan"], self)
                dialog.extra_payment.setValue(extra)
                
                if dialog.exec_() == QDialog.Accepted:
                    result = dialog.early_results.toPlainText()
                    self.append_message("Assistant", f"Payment Analysis Results:\n{result}")
                else:
                    self.append_message("Assistant", "Analysis cancelled.")
                    
                self.current_conversation_state = None
                self.conversation_data = {}
                
            elif self.current_conversation_state == "payment_years":
                years = float(user_input)
                if not 1 <= years <= self.conversation_data["loan"].initial_term:
                    raise ValueError(f"Years must be between 1 and {self.conversation_data['loan'].initial_term}")
                    
                dialog = LoanPaymentAnalysisDialog(self.conversation_data["loan"], self)
                dialog.years_to_payoff.setValue(years)
                
                if dialog.exec_() == QDialog.Accepted:
                    result = dialog.faster_results.toPlainText()
                    self.append_message("Assistant", f"Payment Analysis Results:\n{result}")
                else:
                    self.append_message("Assistant", "Analysis cancelled.")
                    
                self.current_conversation_state = None
                self.conversation_data = {}
                
        except ValueError as e:
            self.append_message("Assistant", f"Invalid input: {str(e)}. Please try again.")

    def handle_create_loan_conversation(self, user_input):
        """Gestisce il flusso di conversazione per la creazione di un nuovo prestito"""
        try:
            if self.current_conversation_state == "create_loan_amount":
                amount = float(user_input)
                if amount <= 0:
                    raise ValueError("Loan amount must be positive")
                self.conversation_data["loan_amount"] = amount
                self.current_conversation_state = "create_loan_rate"
                self.append_message("Assistant", "What's the interest rate (as %)?")

            elif self.current_conversation_state == "create_loan_rate":
                rate = float(user_input)
                if not 0 <= rate <= 100:
                    raise ValueError("Interest rate must be between 0 and 100")
                self.conversation_data["rate"] = rate
                self.current_conversation_state = "create_loan_rate_type"
                self.append_message("Assistant", 
                    "Select rate type:\n" +
                    "1. Fixed\n" +
                    "2. Variable")

            elif self.current_conversation_state == "create_loan_rate_type":
                if user_input not in ["1", "2"]:
                    raise ValueError("Please enter 1 for Fixed or 2 for Variable")
                self.conversation_data["rate_type"] = "fixed" if user_input == "1" else "variable"
                
                if user_input == "2":  # Se tasso variabile, chiedi info Euribor
                    self.current_conversation_state = "create_loan_euribor"
                    self.append_message("Assistant", "Use Euribor rates? (yes/no)")
                else:
                    self.current_conversation_state = "create_loan_term"
                    self.append_message("Assistant", "What's the loan term in years?")

            elif self.current_conversation_state == "create_loan_euribor":
                use_euribor = user_input.lower() in ["yes", "y"]
                self.conversation_data["use_euribor"] = use_euribor
                if use_euribor:
                    self.current_conversation_state = "create_loan_update_frequency"
                    self.append_message("Assistant", 
                        "Select rate update frequency:\n" +
                        "1. Monthly\n" +
                        "2. Quarterly\n" +
                        "3. Semi-annual\n" +
                        "4. Annual")
                else:
                    self.current_conversation_state = "create_loan_term"
                    self.append_message("Assistant", "What's the loan term in years?")

            elif self.current_conversation_state == "create_loan_update_frequency":
                freq_map = {"1": "monthly", "2": "quarterly", "3": "semi-annual", "4": "annual"}
                if user_input not in freq_map:
                    raise ValueError("Please select a number between 1 and 4")
                self.conversation_data["update_frequency"] = freq_map[user_input]
                self.current_conversation_state = "create_loan_term"
                self.append_message("Assistant", "What's the loan term in years?")

            elif self.current_conversation_state == "create_loan_term":
                term = int(user_input)
                if term <= 0:
                    raise ValueError("Term must be positive")
                self.conversation_data["term"] = term
                self.current_conversation_state = "create_loan_type"
                self.append_message("Assistant", 
                    "What type of amortization?\n" +
                    "1. French (constant payment)\n" +
                    "2. Italian (declining payment)")

            elif self.current_conversation_state == "create_loan_type":
                if user_input not in ["1", "2"]:
                    raise ValueError("Please enter 1 for French or 2 for Italian")
                self.conversation_data["amortization_type"] = "French" if user_input == "1" else "Italian"
                self.current_conversation_state = "create_loan_frequency"
                self.append_message("Assistant", 
                    "Select payment frequency:\n" +
                    "1. Monthly\n" +
                    "2. Quarterly\n" +
                    "3. Semi-annual\n" +
                    "4. Annual")

            elif self.current_conversation_state == "create_loan_frequency":
                freq_map = {"1": "monthly", "2": "quarterly", "3": "semi-annual", "4": "annual"}
                if user_input not in freq_map:
                    raise ValueError("Please select a number between 1 and 4")
                self.conversation_data["frequency"] = freq_map[user_input]
                self.current_conversation_state = "create_loan_downpayment"
                self.append_message("Assistant", "Enter downpayment percentage (0-100):")

            elif self.current_conversation_state == "create_loan_downpayment":
                downpayment = float(user_input)
                if not 0 <= downpayment <= 100:
                    raise ValueError("Downpayment must be between 0 and 100")
                self.conversation_data["downpayment_percent"] = downpayment
                # Usa QTimer.singleShot per evitare loop di eventi annidati
                QTimer.singleShot(0, lambda: self._show_loan_form())

        except ValueError as e:
            self.append_message("Assistant", f"Invalid input: {str(e)}. Please try again.")
            
    def _show_loan_preview(self):
        """Mostra l'anteprima del prestito e gestisce la creazione"""
        preview_dialog = QMessageBox()
        preview_dialog.setWindowTitle("Create Loan Preview")
        
        # Prepara il testo dell'anteprima con tutti i parametri
        preview_text = (
            f"Amount: €{self.conversation_data['loan_amount']:,.2f}\n"
            f"Interest Rate: {self.conversation_data['rate']}%\n"
            f"Rate Type: {self.conversation_data['rate_type']}\n"
            f"Term: {self.conversation_data['term']} years\n"
            f"Type: {self.conversation_data['amortization_type']}\n"
            f"Payment Frequency: {self.conversation_data['frequency']}\n"
            f"Downpayment: {self.conversation_data['downpayment_percent']}%\n"
        )
        
        if self.conversation_data.get('use_euribor'):
            preview_text += f"Using Euribor rates\n"
            preview_text += f"Update Frequency: {self.conversation_data['update_frequency']}\n"
            
        if self.conversation_data.get('additional_costs'):
            preview_text += "\nAdditional Costs:\n"
            for name, amount in self.conversation_data['additional_costs'].items():
                preview_text += f"- {name}: €{amount:,.2f}\n"
        
        preview_dialog.setText(f"Please review the loan details:\n\n{preview_text}\n"
                            "Would you like to see the full creation dialog?")
        preview_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        preview_dialog.setDefaultButton(QMessageBox.Yes)
        
        response = preview_dialog.exec_()
        self._handle_preview_response(response)

    def _handle_preview_response(self, response):
        """Gestisce la risposta dell'utente all'anteprima"""
        if response == QMessageBox.Yes:
            self._show_full_dialog()
        elif response == QMessageBox.No:
            self._create_loan_directly()
        else:  # Cancel
            self.animate_typing("Assistant", "Loan creation cancelled.")
            
        self.current_conversation_state = None
        self.conversation_data = {}

    def _show_loan_form(self):
        """Mostra il form di creazione prestito precompilato"""
        try:
            # Crea e configura il dialog
            dialog = LoanDialog(self)
            
            # Precompila i campi con i dati della conversazione
            dialog.rate_entry.setValue(self.conversation_data["rate"])
            dialog.term_entry.setValue(self.conversation_data["term"])
            dialog.pv_entry.setValue(self.conversation_data["loan_amount"])
            dialog.amortization_combobox.setCurrentText(self.conversation_data["amortization_type"])
            dialog.frequency_combobox.setCurrentText(self.conversation_data["frequency"])
            dialog.downpayment_entry.setValue(self.conversation_data["downpayment_percent"])
            
            # Aggiungi parametri opzionali se presenti
            if "rate_type" in self.conversation_data:
                dialog.rate_type = self.conversation_data["rate_type"]
            if "use_euribor" in self.conversation_data:
                dialog.use_euribor = self.conversation_data["use_euribor"]
            if "update_frequency" in self.conversation_data:
                dialog.update_frequency = self.conversation_data["update_frequency"]
            
            # Mostra il dialog in modo non bloccante
            if dialog.exec_() == QDialog.Accepted:
                # Usa QTimer per gestire la creazione del prestito in modo asincrono
                QTimer.singleShot(0, lambda: self._handle_loan_creation(dialog))
            else:
                QTimer.singleShot(0, lambda: self.animate_typing("Assistant", "Loan creation cancelled."))
                
        except Exception as e:
            QTimer.singleShot(0, lambda: self.animate_typing("Assistant", f"Error showing loan form: {str(e)}"))
        finally:
            # Reset conversation state
            self.current_conversation_state = None
            self.conversation_data = {}

    def _handle_loan_creation(self, dialog):
        """Gestisce la creazione effettiva del prestito"""
        try:
            # Ottieni i dati dal dialog
            loan_data = dialog.get_loan_data()
            
            # Crea il prestito
            loan = Loan(db_manager=self.loan_app.db_manager, **loan_data)
            
            # Aggiungilo all'applicazione
            self.loan_app._add_loan(loan)
            
            # Mostra il riepilogo
            summary = (
                f"Loan created successfully!\n\n"
                f"Amount: €{loan.loan_amount:,.2f}\n"
                f"Rate: {loan.initial_rate * 100:.2f}%\n"
                f"Term: {loan.initial_term} years\n"
                f"Type: {loan.amortization_type}\n"
                f"Frequency: {loan.frequency}\n"
                f"Monthly Payment: {loan.pmt_str}"
            )
            self.animate_typing("Assistant", summary)
            
        except Exception as e:
            self.animate_typing("Assistant", f"Failed to create loan: {str(e)}")

    def _show_full_dialog(self):
        """Mostra la finestra di dialogo completa per la creazione del prestito"""
        dialog = LoanDialog(self)
        
        # Precompila i campi con i dati della conversazione
        dialog.rate_entry.setValue(self.conversation_data["rate"])
        dialog.term_entry.setValue(self.conversation_data["term"])
        dialog.pv_entry.setValue(self.conversation_data["loan_amount"])
        dialog.amortization_combobox.setCurrentText(self.conversation_data["amortization_type"])
        dialog.frequency_combobox.setCurrentText(self.conversation_data["frequency"])
        dialog.downpayment_entry.setValue(self.conversation_data["downpayment_percent"])
        
        # Se ci sono costi aggiuntivi, aggiungili
        if self.conversation_data.get("additional_costs"):
            dialog.additional_costs = self.conversation_data["additional_costs"]
            
        if dialog.exec_() == QDialog.Accepted:
            try:
                loan_data = dialog.get_loan_data()
                loan = Loan(db_manager=self.loan_app.db_manager, **loan_data)
                self.loan_app._add_loan(loan)
                self.animate_typing("Assistant", "Loan created successfully!")
            except Exception as e:
                self.animate_typing("Assistant", f"Failed to create loan: {str(e)}")

    def _create_loan_directly(self):
        """Crea il prestito direttamente con i dati della conversazione"""
        try:
            # Prepara i dati del prestito
            loan_data = {
                "rate": self.conversation_data["rate"] / 100,  # Converti da percentuale
                "term": self.conversation_data["term"],
                "loan_amount": self.conversation_data["loan_amount"],
                "amortization_type": self.conversation_data["amortization_type"],
                "frequency": self.conversation_data["frequency"],
                "downpayment_percent": self.conversation_data["downpayment_percent"]
            }
            
            # Aggiungi parametri opzionali se presenti
            if "rate_type" in self.conversation_data:
                loan_data["rate_type"] = self.conversation_data["rate_type"]
            if "use_euribor" in self.conversation_data:
                loan_data["use_euribor"] = self.conversation_data["use_euribor"]
            if "update_frequency" in self.conversation_data:
                loan_data["update_frequency"] = self.conversation_data["update_frequency"]
            if "additional_costs" in self.conversation_data:
                loan_data["additional_costs"] = self.conversation_data["additional_costs"]
                
            # Crea e aggiungi il prestito
            loan = Loan(db_manager=self.loan_app.db_manager, **loan_data)
            self.loan_app._add_loan(loan)
            
            # Mostra conferma con dettagli
            summary = (
                f"Loan created successfully!\n\n"
                f"Amount: €{loan.loan_amount:,.2f}\n"
                f"Rate: {loan.initial_rate * 100:.2f}%\n"
                f"Term: {loan.initial_term} years\n"
                f"Type: {loan.amortization_type}\n"
                f"Frequency: {loan.frequency}\n"
                f"Monthly Payment: {loan.pmt_str}"
            )
            self.animate_typing("Assistant", summary)
            
        except Exception as e:
            self.animate_typing("Assistant", f"Failed to create loan: {str(e)}")

    def handle_update_loan_conversation(self, user_input):
        """Gestisce il flusso di conversazione per l'aggiornamento di un prestito"""
        try:
            if self.current_conversation_state == "update_loan_field":
                field_map = {
                    "1": "rate",
                    "2": "term",
                    "3": "loan_amount",
                    "4": "frequency"
                }
                if user_input not in field_map:
                    raise ValueError("Please select a number between 1 and 4")
                    
                self.conversation_data["field"] = field_map[user_input]
                self.current_conversation_state = "update_loan_value"
                self.append_message("Assistant", f"Enter new value for {field_map[user_input]}:")
                
            elif self.current_conversation_state == "update_loan_value":
                # Show confirmation dialog
                dialog = EditLoanDialog(self.conversation_data["loan"], self)
                
                field = self.conversation_data["field"]
                value = float(user_input) if field != "frequency" else user_input
                
                if field == "rate":
                    dialog.rate_entry.setValue(value)
                elif field == "term":
                    dialog.term_entry.setValue(int(value))
                elif field == "loan_amount":
                    dialog.pv_entry.setValue(value)
                elif field == "frequency":
                    dialog.frequency_combobox.setCurrentText(value)
                    
                if dialog.exec_() == QDialog.Accepted:
                    updated_data = dialog.get_updated_loan_data()
                    self.loan_app._update_loan(self.conversation_data["loan"], updated_data)
                    self.append_message("Assistant", "Loan updated successfully!")
                else:
                    self.append_message("Assistant", "Update cancelled.")
                    
                self.current_conversation_state = None
                self.conversation_data = {}
                
        except ValueError as e:
            self.append_message("Assistant", f"Invalid input: {str(e)}. Please try again.")

    def handle_crm_conversation(self, user_input):
        """Gestisce i flussi di conversazione per le funzionalità CRM"""
        intent = self.conversation_data.get("intent", "")
        
        # Gestione Client
        if intent == "add_client":
            self._handle_add_client_conversation(user_input)
        elif intent == "update_client":
            self._handle_update_client_conversation(user_input)
        elif intent == "delete_client":
            self._handle_delete_client_conversation(user_input)
        elif intent == "get_client":
            self._handle_get_client_conversation(user_input)
        elif intent == "assign_loan_to_client":
            self._handle_assign_loan_to_client_conversation(user_input)
        elif intent == "record_client_interaction":
            self._handle_record_client_interaction_conversation(user_input)
        elif intent == "get_client_interactions":
            self._handle_get_client_interactions_conversation(user_input)
        elif intent == "get_client_loans":
            self._handle_get_client_loans_conversation(user_input)
        elif intent == "get_client_details":
            self._handle_get_client_details_conversation(user_input)
        
        # Gestione Corporation
        elif intent == "add_corporation":
            self._handle_add_corporation_conversation(user_input)
        elif intent == "update_corporation":
            self._handle_update_corporation_conversation(user_input)
        elif intent == "delete_corporation":
            self._handle_delete_corporation_conversation(user_input)
        elif intent == "get_corporation":
            self._handle_get_corporation_conversation(user_input)
        elif intent == "assign_loan_to_corporation":
            self._handle_assign_loan_to_corporation_conversation(user_input)
        elif intent == "record_corporation_interaction":
            self._handle_record_corporation_interaction_conversation(user_input)
        elif intent == "get_corporation_interactions":
            self._handle_get_corporation_interactions_conversation(user_input)
        elif intent == "get_corporation_loans":
            self._handle_get_corporation_loans_conversation(user_input)
        elif intent == "get_corporation_details":
            self._handle_get_corporation_details_conversation(user_input)

    def _handle_list_clients(self):
        """Gestisce la visualizzazione dell'elenco dei clienti"""
        try:
            clients = self.chatbot.crm.list_clients()
            
            if not clients or len(clients) == 0:
                self.append_message("Assistant", "No clients found in the system.")
                return
                
            # Crea un messaggio formattato con l'elenco dei clienti
            clients_list = "Clients in the system:\n\n"
            for i, client in enumerate(clients, 1):
                clients_list += (f"{i}. ID: {client.get('client_id')}\n"
                            f"Name: {client.get('first_name')} {client.get('last_name')}\n"
                            f"Email: {client.get('email')}\n"
                            f"Phone: {client.get('phone', 'N/A')}\n"
                            f"{'─' * 30}\n")
                
            self.append_message("Assistant", clients_list)
            
        except Exception as e:
            self.append_message("Assistant", f"Error retrieving clients: {str(e)}")

    def _handle_list_corporations(self):
        """Gestisce la visualizzazione dell'elenco delle aziende"""
        try:
            corporations = self.chatbot.crm.list_corporations()
            
            if not corporations or len(corporations) == 0:
                self.append_message("Assistant", "No corporations found in the system.")
                return
                
            # Crea un messaggio formattato con l'elenco delle aziende
            corporations_list = "Corporations in the system:\n\n"
            for i, corporation in enumerate(corporations, 1):
                corporations_list += (f"{i}. ID: {corporation.get('corporation_id')}\n"
                                f"Name: {corporation.get('company_name')}\n"
                                f"Industry: {corporation.get('industry', 'N/A')}\n"
                                f"Contact: {corporation.get('email')}\n"
                                f"{'─' * 30}\n")
                
            self.append_message("Assistant", corporations_list)
            
        except Exception as e:
            self.append_message("Assistant", f"Error retrieving corporations: {str(e)}")

    # IMPLEMENTAZIONE CONVERSAZIONI CLIENT

    def _handle_add_client_conversation(self, user_input):
        """Gestisce il flusso di conversazione per l'aggiunta di un cliente"""
        # Gestione dello stato della conversazione per la raccolta dei dati del cliente
        if "step" not in self.conversation_data:
            self.conversation_data["step"] = "first_name"
            self.conversation_data["client_data"] = {}
            
        step = self.conversation_data["step"]
        client_data = self.conversation_data["client_data"]
        
        # Processa l'input dell'utente in base allo step corrente
        if step == "first_name":
            client_data["first_name"] = user_input
            self.conversation_data["step"] = "last_name"
            self.append_message("Assistant", "What's the client's last name?")
            
        elif step == "last_name":
            client_data["last_name"] = user_input
            self.conversation_data["step"] = "email"
            self.append_message("Assistant", "What's their email address?")
            
        elif step == "email":
            client_data["email"] = user_input
            self.conversation_data["step"] = "phone"
            self.append_message("Assistant", "What's their phone number?")
            
        elif step == "phone":
            client_data["phone"] = user_input
            self.conversation_data["step"] = "birth_date"
            self.append_message("Assistant", "What's their birth date? (YYYY-MM-DD, or type 'skip' to leave empty)")
            
        elif step == "birth_date":
            if user_input.lower() != "skip":
                client_data["birth_date"] = user_input
            self.conversation_data["step"] = "address"
            self.append_message("Assistant", "What's their address? (or type 'skip' to leave empty)")
            
        elif step == "address":
            if user_input.lower() != "skip":
                client_data["address"] = user_input
            self.conversation_data["step"] = "city"
            self.append_message("Assistant", "What city do they live in? (or type 'skip' to leave empty)")
            
        elif step == "city":
            if user_input.lower() != "skip":
                client_data["city"] = user_input
            self.conversation_data["step"] = "state"
            self.append_message("Assistant", "What state/province? (or type 'skip' to leave empty)")
            
        elif step == "state":
            if user_input.lower() != "skip":
                client_data["state"] = user_input
            self.conversation_data["step"] = "zip_code"
            self.append_message("Assistant", "What's the ZIP/postal code? (or type 'skip' to leave empty)")
            
        elif step == "zip_code":
            if user_input.lower() != "skip":
                client_data["zip_code"] = user_input
            self.conversation_data["step"] = "country"
            self.append_message("Assistant", "What country do they live in? (or type 'skip' to leave empty)")
            
        elif step == "country":
            if user_input.lower() != "skip":
                client_data["country"] = user_input
            self.conversation_data["step"] = "occupation"
            self.append_message("Assistant", "What's their occupation? (or type 'skip' to leave empty)")
            
        elif step == "occupation":
            if user_input.lower() != "skip":
                client_data["occupation"] = user_input
            self.conversation_data["step"] = "employer"
            self.append_message("Assistant", "Who is their employer? (or type 'skip' to leave empty)")
            
        elif step == "employer":
            if user_input.lower() != "skip":
                client_data["employer"] = user_input
            self.conversation_data["step"] = "income"
            self.append_message("Assistant", "What's their annual income? (numeric value, or type 'skip' to leave empty)")
            
        elif step == "income":
            if user_input.lower() != "skip":
                try:
                    client_data["income"] = float(user_input)
                except ValueError:
                    self.append_message("Assistant", "Please enter a valid numeric value for income, or type 'skip' to leave empty.")
                    return
            self.conversation_data["step"] = "credit_score"
            self.append_message("Assistant", "What's their credit score? (numeric value, or type 'skip' to leave empty)")
            
        elif step == "credit_score":
            if user_input.lower() != "skip":
                try:
                    client_data["credit_score"] = int(user_input)
                except ValueError:
                    self.append_message("Assistant", "Please enter a valid numeric value for credit score, or type 'skip' to leave empty.")
                    return
            self.conversation_data["step"] = "confirmation"
            
            # Mostra riepilogo per conferma
            summary = "Client Information Summary:\n\n"
            for key, value in client_data.items():
                summary += f"{key.replace('_', ' ').title()}: {value}\n"
                
            self.append_message("Assistant", 
                f"{summary}\n\nDo you want to save this client? (yes/no)")
            
        elif step == "confirmation":
            if user_input.lower() in ["yes", "y"]:
                try:
                    # Salva il cliente
                    client_id = self.chatbot.crm.add_client(client_data)
                    self.append_message("Assistant", f"Client added successfully! Client ID: {client_id}")
                except Exception as e:
                    self.append_message("Assistant", f"Error adding client: {str(e)}")
            else:
                self.append_message("Assistant", "Client creation cancelled.")
                
            # Reset dello stato di conversazione
            self.current_conversation_state = None
            self.conversation_data = {}

    def _handle_update_client_conversation(self, user_input):
        """Gestisce il flusso di conversazione per l'aggiornamento di un cliente"""
        if "step" not in self.conversation_data:
            self.conversation_data["step"] = "client_id"
            self.conversation_data["updated_data"] = {}
            
        step = self.conversation_data["step"]
        
        if step == "client_id":
            # Cerca il cliente con l'ID fornito
            try:
                client_id = user_input.strip()
                client = self.chatbot.crm.get_client(client_id)
                
                if not client:
                    self.append_message("Assistant", "Client not found. Please check the ID and try again.")
                    self.current_conversation_state = None
                    self.conversation_data = {}
                    return
                    
                self.conversation_data["client_id"] = client_id
                self.conversation_data["client"] = client
                self.conversation_data["step"] = "field_selection"
                
                # Mostra i campi disponibili per la modifica
                self.append_message("Assistant", 
                    "What field would you like to update? Choose from:\n" +
                    "1. First Name\n" +
                    "2. Last Name\n" +
                    "3. Email\n" +
                    "4. Phone\n" +
                    "5. Address\n" +
                    "6. Occupation\n" +
                    "7. Employer\n" +
                    "8. Income\n" +
                    "9. Credit Score\n" +
                    "Or type 'done' to finish updating."
                )
            except Exception as e:
                self.append_message("Assistant", f"Error retrieving client: {str(e)}")
                self.current_conversation_state = None
                self.conversation_data = {}
                
        elif step == "field_selection":
            if user_input.lower() == "done":
                # Termina l'aggiornamento e salva le modifiche
                if not self.conversation_data["updated_data"]:
                    self.append_message("Assistant", "No changes were made to the client.")
                    self.current_conversation_state = None
                    self.conversation_data = {}
                    return
                    
                # Chiedi conferma
                summary = "You are about to update the following fields:\n\n"
                for key, value in self.conversation_data["updated_data"].items():
                    summary += f"{key.replace('_', ' ').title()}: {value}\n"
                    
                self.conversation_data["step"] = "confirmation"
                self.append_message("Assistant", f"{summary}\n\nDo you want to save these changes? (yes/no)")
                return
                
            # Mappa la selezione al campo corrispondente
            field_map = {
                "1": "first_name",
                "2": "last_name",
                "3": "email",
                "4": "phone",
                "5": "address",
                "6": "occupation",
                "7": "employer",
                "8": "income",
                "9": "credit_score"
            }
            
            if user_input not in field_map:
                self.append_message("Assistant", "Invalid selection. Please choose a number from 1-9 or type 'done'.")
                return
                
            self.conversation_data["current_field"] = field_map[user_input]
            self.conversation_data["step"] = "field_value"
            
            current_value = self.conversation_data["client"].get(field_map[user_input], "N/A")
            self.append_message("Assistant", f"Current value is: {current_value}\nEnter new value:")
            
        elif step == "field_value":
            current_field = self.conversation_data["current_field"]
            
            # Per i campi numerici, valida l'input
            if current_field == "income":
                try:
                    self.conversation_data["updated_data"][current_field] = float(user_input)
                except ValueError:
                    self.append_message("Assistant", "Please enter a valid numeric value for income.")
                    return
            elif current_field == "credit_score":
                try:
                    self.conversation_data["updated_data"][current_field] = int(user_input)
                except ValueError:
                    self.append_message("Assistant", "Please enter a valid numeric value for credit score.")
                    return
            else:
                self.conversation_data["updated_data"][current_field] = user_input
                
            self.conversation_data["step"] = "field_selection"
            self.append_message("Assistant", 
                f"Updated {current_field.replace('_', ' ').title()} to: {user_input}\n\n" +
                "What other field would you like to update? Choose from:\n" +
                "1. First Name\n" +
                "2. Last Name\n" +
                "3. Email\n" +
                "4. Phone\n" +
                "5. Address\n" +
                "6. Occupation\n" +
                "7. Employer\n" +
                "8. Income\n" +
                "9. Credit Score\n" +
                "Or type 'done' to finish updating."
            )
            
        elif step == "confirmation":
            if user_input.lower() in ["yes", "y"]:
                try:
                    # Aggiorna il cliente
                    client_id = self.conversation_data["client_id"]
                    updated_data = self.conversation_data["updated_data"]
                    
                    self.chatbot.crm.update_client(client_id, updated_data)
                    self.append_message("Assistant", "Client updated successfully!")
                except Exception as e:
                    self.append_message("Assistant", f"Error updating client: {str(e)}")
            else:
                self.append_message("Assistant", "Client update cancelled.")
                
            # Reset dello stato di conversazione
            self.current_conversation_state = None
            self.conversation_data = {}

    # Implementazione degli altri metodi di gestione delle conversazioni CRM
    # (per brevità mostro solo questi due esempi dettagliati)

    def _handle_delete_client_conversation(self, user_input):
        """Gestisce l'eliminazione di un cliente"""
        try:
            client_id = user_input.strip()
            client = self.chatbot.crm.get_client(client_id)
            
            if not client:
                self.append_message("Assistant", "Client not found. Please check the ID and try again.")
            else:
                # Chiedi conferma
                confirmation = QMessageBox.question(
                    self, 
                    "Confirm Deletion",
                    f"Are you sure you want to delete client {client.get('first_name')} {client.get('last_name')}?\n"
                    "This will also delete all interactions and loan associations.",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if confirmation == QMessageBox.Yes:
                    self.chatbot.crm.delete_client(client_id)
                    self.append_message("Assistant", "Client deleted successfully.")
                else:
                    self.append_message("Assistant", "Client deletion cancelled.")
        except Exception as e:
            self.append_message("Assistant", f"Error deleting client: {str(e)}")
        finally:
            # Reset dello stato di conversazione
            self.current_conversation_state = None
            self.conversation_data = {}

    def _handle_get_client_conversation(self, user_input):
        """Visualizza i dettagli di un cliente specifico"""
        try:
            client_id = user_input.strip()
            client = self.chatbot.crm.get_client(client_id)
            
            if not client:
                self.append_message("Assistant", "Client not found. Please check the ID and try again.")
            else:
                # Formatta i dettagli del cliente
                details = "Client Details:\n\n"
                for key, value in client.items():
                    if key != "documents":  # Escludiamo i documenti per semplicità
                        details += f"{key.replace('_', ' ').title()}: {value}\n"
                        
                self.append_message("Assistant", details)
        except Exception as e:
            self.append_message("Assistant", f"Error retrieving client details: {str(e)}")
        finally:
            # Reset dello stato di conversazione
            self.current_conversation_state = None
            self.conversation_data = {}

    def _handle_backend_action(self, action):
        """Esegue l'azione del backend"""
        try:
            # Usa solo GuiPrintManager per i messaggi
            with self.GuiPrintManager(self):
                action()
        except Exception as e:
            self.append_message("Assistant", 
                "I couldn't complete that action.\n" +
                f"Error details: {str(e)}\n\n" +
                "Please make sure you have selected a loan if required."
            )

    def gui_operator_confirmation(self, prompt):
        """Mostra un QMessageBox per chiedere conferma all'operatore"""
        reply = QMessageBox.question(self, "Conferma", prompt, QMessageBox.Yes | QMessageBox.No)
        return reply == QMessageBox.Yes
    
    class GuiPrintManager:
        """
        Context manager per intercettare le chiamate a print() e reindirizzare
        l'output nella cronologia della chat.
        """
        def __init__(self, parent):
            self.parent = parent
            self.original_print = __builtins__.print
        def __enter__(self):
            __builtins__.print = self.gui_print
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            __builtins__.print = self.original_print
        def gui_print(self, *args, **kwargs):
            sep = kwargs.get("sep", " ")
            message = sep.join(str(arg) for arg in args)
            self.parent.append_message("Assistant", message)
    
    def append_message(self, sender, message, is_typing=False):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        
        if sender == "User":
            align = "right"
            text_color = "#FFFFFF"
            bubble_color = "#0078D4"
            bubble_hover = "#106EBE"
            avatar = resource_path("user.png")
        else:
            align = "left" 
            text_color = "#000000"
            bubble_color = "#F0F0F0"
            bubble_hover = "#E8E8E8"
            avatar = resource_path("chatbot_icon.png")

        current_time = time.strftime("%H:%M")
        
        # Template HTML con bordi arrotondati e stile moderno
        html = f'''
            <div style="
                margin: 12px 0; 
                text-align: {align};
                animation: fadeIn 0.3s ease-out;
            ">
                <table style="
                    margin: {'0 0 0 auto' if sender == 'User' else '0 auto 0 0'}; 
                    max-width: 85%;
                    border-spacing: 0;
                ">
                    <tr>
                        <td style="
                            vertical-align: bottom; 
                            padding: 0 8px;
                            width: 40px;
                            {'display: none' if sender == 'User' else ''}
                        ">
                            <div style="
                                width: 35px;
                                height: 35px;
                                border-radius: 50%;
                                background-image: url('{avatar}');
                                background-size: cover;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            "></div>
                        </td>
                        <td style="padding: 0;">
                            <div class="message-bubble" style="
                                position: relative;
                                display: inline-block;
                                background-color: {bubble_color};
                                color: {text_color};
                                padding: 12px 18px;
                                border-radius: 24px;
                                margin: 2px 0;
                                max-width: 100%;
                                word-wrap: break-word;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                                transition: all 0.2s ease;
                                {'border-top-right-radius: 8px;' if sender == 'User' else 'border-top-left-radius: 8px;'}
                            ">
                                {message}
                            </div>
                            <div style="
                                font-size: 11px;
                                color: #999;
                                margin-top: 4px;
                                padding: 0 4px;
                                display: flex;
                                align-items: center;
                                gap: 4px;
                                {'justify-content: flex-end;' if sender == 'User' else ''}
                            ">
                                <span style="font-weight: 500; color: {'#0078D4' if sender == 'User' else '#666'};">
                                    {sender}
                                </span>
                                <span>·</span>
                                <span>{current_time}</span>
                                {'<span style="color: #34D399">✓✓</span>' if sender == 'User' else ''}
                            </div>
                        </td>
                        <td style="
                            vertical-align: bottom;
                            padding: 0 8px;
                            width: 40px;
                            {'display: none' if sender != 'User' else ''}
                        ">
                            <div style="
                                width: 35px;
                                height: 35px;
                                border-radius: 50%;
                                background-image: url('{avatar}');
                                background-size: cover;
                                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            "></div>
                        </td>
                    </tr>
                </table>
            </div>
        '''

        css = f'''
            <style>
                @keyframes fadeIn {{
                    from {{ 
                        opacity: 0; 
                        transform: translateY(8px);
                    }}
                    to {{ 
                        opacity: 1; 
                        transform: translateY(0);
                    }}
                }}
                .message-bubble {{
                    transform-origin: {"right" if sender == "User" else "left"};
                }}
                .message-bubble:hover {{
                    transform: scale(1.02);
                    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                }}
            </style>
        '''

        content = css + html
        cursor.insertHtml(content)
        
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

class ReportsDialog(FluentDialog):
    """Dialog for accessing various loan reporting features."""
    def __init__(self, db_manager, loan_crm, loans, parent=None):
        super().__init__("Loan Reports", parent)
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        
        self.db_manager = db_manager
        self.loan_crm = loan_crm
        self.loans = loans
        self.report_generator = LoanReport(db_manager, loan_crm)
        
        # Create tab widget for different report categories
        self.tab_widget = QTabWidget()
        
        # Create tabs for different report categories
        self.create_portfolio_tab()
        self.create_client_tab()
        self.create_forecast_tab()
        self.create_export_tab()
        
        # Add tab widget to main layout
        self.main_layout.insertWidget(0, self.tab_widget)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(close_button)
        
    def create_portfolio_tab(self):
        """Create the portfolio reports tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Portfolio summary section
        group_summary = QGroupBox("Portfolio Summary")
        summary_layout = QVBoxLayout(group_summary)
        
        summary_btn = QPushButton("Generate Portfolio Summary")
        summary_btn.clicked.connect(self.generate_portfolio_summary)
        summary_layout.addWidget(summary_btn)
        
        # Comparative analysis section
        group_comparative = QGroupBox("Comparative Analysis")
        comp_layout = QVBoxLayout(group_comparative)
        
        comp_btn = QPushButton("Generate Comparative Report")
        comp_btn.clicked.connect(self.generate_comparative_report)
        comp_layout.addWidget(comp_btn)
        
        # Amortization report section
        group_amort = QGroupBox("Amortization Report")
        amort_layout = QVBoxLayout(group_amort)
        
        amort_form = QFormLayout()
        self.loan_combo = QComboBox()
        self.update_loan_combo()
        amort_form.addRow("Select Loan:", self.loan_combo)
        
        amort_btn = QPushButton("Generate Amortization Report")
        amort_btn.clicked.connect(self.generate_amortization_report)
        
        amort_layout.addLayout(amort_form)
        amort_layout.addWidget(amort_btn)
        
        # Probabilistic pricing section
        group_pricing = QGroupBox("Probabilistic Pricing")
        pricing_layout = QVBoxLayout(group_pricing)
        
        pricing_form = QFormLayout()
        self.pricing_loan_combo = QComboBox()
        self.update_loan_combo(self.pricing_loan_combo)
        pricing_form.addRow("Select Loan:", self.pricing_loan_combo)
        
        self.sim_count_spin = QSpinBox()
        self.sim_count_spin.setRange(100, 10000)
        self.sim_count_spin.setValue(1000)
        self.sim_count_spin.setSingleStep(100)
        pricing_form.addRow("Simulation Count:", self.sim_count_spin)
        
        pricing_btn = QPushButton("Generate Pricing Report")
        pricing_btn.clicked.connect(self.generate_pricing_report)
        
        pricing_layout.addLayout(pricing_form)
        pricing_layout.addWidget(pricing_btn)
        
        # Add all groups to the tab layout
        layout.addWidget(group_summary)
        layout.addWidget(group_comparative)
        layout.addWidget(group_amort)
        layout.addWidget(group_pricing)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Portfolio Reports")
        
    def create_client_tab(self):
        """Create the client reports tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Client segmentation section
        group_segmentation = QGroupBox("Client Segmentation")
        segmentation_layout = QVBoxLayout(group_segmentation)
        
        segmentation_btn = QPushButton("Generate Client Segmentation Report")
        segmentation_btn.clicked.connect(self.generate_segmentation_report)
        segmentation_layout.addWidget(segmentation_btn)
        
        # CRM Performance section
        group_crm = QGroupBox("CRM Performance")
        crm_layout = QVBoxLayout(group_crm)
        
        crm_btn = QPushButton("Generate CRM Performance Report")
        crm_btn.clicked.connect(self.generate_crm_report)
        crm_layout.addWidget(crm_btn)
        
        enhanced_crm_btn = QPushButton("Generate Enhanced CRM Report")
        enhanced_crm_btn.clicked.connect(self.generate_enhanced_crm_report)
        crm_layout.addWidget(enhanced_crm_btn)
        
        # Add all groups to the tab layout
        layout.addWidget(group_segmentation)
        layout.addWidget(group_crm)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Client Reports")
        
    def create_forecast_tab(self):
        """Create the forecasting tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Euribor forecast section
        group_forecast = QGroupBox("Euribor Rate Forecast")
        forecast_layout = QVBoxLayout(group_forecast)
        
        forecast_form = QFormLayout()
        
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["monthly", "quarterly", "semi-annual", "annual"])
        forecast_form.addRow("Frequency:", self.frequency_combo)
        
        self.start_date_edit = QLineEdit()
        self.start_date_edit.setText("2020-01-01")  # Default to last few years
        forecast_form.addRow("Start Date (YYYY-MM-DD):", self.start_date_edit)
        
        forecast_btn = QPushButton("Generate Forecast Report")
        forecast_btn.clicked.connect(self.generate_forecast_report)
        
        forecast_layout.addLayout(forecast_form)
        forecast_layout.addWidget(forecast_btn)
        
        # Add all groups to the tab layout
        layout.addWidget(group_forecast)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Forecasting")
        
    def create_export_tab(self):
        """Create the export options tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Export section
        group_export = QGroupBox("Export Options")
        export_layout = QVBoxLayout(group_export)
        
        export_form = QFormLayout()
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PDF", "CSV"])
        export_form.addRow("Export Format:", self.export_format_combo)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "portfolio", "comparative", "amortization", "probabilistic", 
            "client_segmentation", "crm_performance", "euribor_forecast"
        ])
        export_form.addRow("Report Type:", self.report_type_combo)
        
        export_btn = QPushButton("Export Last Generated Report")
        export_btn.clicked.connect(self.export_report)
        
        export_layout.addLayout(export_form)
        export_layout.addWidget(export_btn)
        
        # Add all groups to the tab layout
        layout.addWidget(group_export)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Export Options")
        
    def update_loan_combo(self, combo_box=None):
        """Update the loan combo box with available loans."""
        if combo_box is None:
            combo_box = self.loan_combo
            
        combo_box.clear()
        for loan in self.loans:
            combo_box.addItem(f"Loan {loan.loan_id} - €{loan.loan_amount:,.2f}", loan.loan_id)
            
    def generate_portfolio_summary(self):
        """Generate and display portfolio summary report."""
        try:
            summary = self.report_generator.generate_portfolio_summary()
            
            # Create a formatted display of the summary
            text = "Portfolio Summary Report\n"
            text += "=" * 50 + "\n\n"
            
            for key, value in summary.items():
                if isinstance(value, float):
                    if "Rate" in key or "TAEG" in key:
                        formatted_value = f"{value * 100:.2f}%" if key != "Average Initial Rate" else f"{value:.2f}%"
                    else:
                        formatted_value = f"€{value:,.2f}"
                else:
                    formatted_value = str(value)
                text += f"{key}: {formatted_value}\n"
                
            self.show_report_result(text, "Portfolio Summary")
            self.last_report_data = summary
            self.last_report_type = "portfolio"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate portfolio summary: {str(e)}")
            
    def generate_comparative_report(self):
        """Generate and display comparative report."""
        if len(self.loans) < 2:
            QMessageBox.warning(self, "Warning", "You need at least two loans to generate a comparative report.")
            return
            
        try:
            report = self.report_generator.generate_comparative_report(self.loans)
            
            self.show_report_result(report, "Comparative Analysis")
            self.last_report_data = report
            self.last_report_type = "comparative"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate comparative report: {str(e)}")
            
    def generate_amortization_report(self):
        """Generate and display amortization report."""
        if self.loan_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warning", "Please select a loan.")
            return
            
        loan_id = self.loan_combo.currentData()
        
        try:
            amort_table = self.report_generator.generate_amortization_report(loan_id)
            
            # Create a dialog to display the amortization table
            dialog = AmortizationDialog(amort_table, self)
            dialog.exec_()
            
            self.last_report_data = amort_table
            self.last_report_type = "amortization"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate amortization report: {str(e)}")
            
    def generate_pricing_report(self):
        """Generate and display probabilistic pricing report."""
        if self.pricing_loan_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Warning", "Please select a loan.")
            return
            
        loan_id = self.pricing_loan_combo.currentData()
        simulations = self.sim_count_spin.value()
        
        try:
            report = self.report_generator.generate_probabilistic_pricing_report(
                loan_id, 
                simulations=simulations
            )
            
            # Create a formatted display of the results
            text = "Probabilistic Pricing Analysis\n"
            text += "=" * 50 + "\n\n"
            text += f"Based on {simulations} simulations\n\n"
            
            if isinstance(report, pd.DataFrame):
                stats = {
                    "Mean": report.mean().mean(),
                    "Median": report.median().mean(),
                    "Min": report.min().min(),
                    "Max": report.max().max(),
                    "Std Dev": report.std().mean()
                }
                
                for key, value in stats.items():
                    text += f"{key}: {value:.2f}\n"
                
                text += "\nNote: Full results available in exported PDF report"
            else:
                text += str(report)
                
            self.show_report_result(text, "Probabilistic Pricing")
            self.last_report_data = report
            self.last_report_type = "probabilistic"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate pricing report: {str(e)}")
            
    def generate_segmentation_report(self):
        """Generate and display client segmentation report."""
        if not self.loan_crm:
            QMessageBox.warning(self, "Warning", "CRM module not available.")
            return
            
        try:
            report = self.report_generator.generate_client_segmentation_report()
            
            if "error" in report:
                QMessageBox.warning(self, "Warning", f"Segmentation report issue: {report['error']}")
                return
                
            # Create a formatted display of the results
            text = "Client Segmentation Report\n"
            text += "=" * 50 + "\n\n"
            
            # Income segments
            if "income_segments" in report:
                text += "Income Segments:\n"
                for segment, count in report["income_segments"].items():
                    text += f"  {segment}: {count} clients\n"
                text += "\n"
                
            # Credit score segments
            if "credit_score_segments" in report:
                text += "Credit Score Segments:\n"
                for segment, count in report["credit_score_segments"].items():
                    text += f"  {segment}: {count} clients\n"
                text += "\n"
                
            # Cluster profiles
            if "cluster_profiles" in report and "error" not in report["cluster_profiles"]:
                text += "Cluster Profiles:\n"
                for cluster, profile in report["cluster_profiles"].items():
                    text += f"  {cluster}: {profile['count']} clients\n"
                    
                    if "avg_income" in profile and profile["avg_income"] != "N/A":
                        text += f"    Avg Income: €{profile['avg_income']:,.2f}\n"
                        
                    if "avg_credit_score" in profile and profile["avg_credit_score"] != "N/A":
                        text += f"    Avg Credit Score: {profile['avg_credit_score']:.1f}\n"
                text += "\n"
                
            self.show_report_result(text, "Client Segmentation")
            self.last_report_data = report
            self.last_report_type = "client_segmentation"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate segmentation report: {str(e)}")
            
    def generate_crm_report(self):
        """Generate and display CRM performance report."""
        if not self.loan_crm:
            QMessageBox.warning(self, "Warning", "CRM module not available.")
            return
            
        try:
            report = self.report_generator.generate_crm_performance_report()
            
            # Create a formatted display of the results
            text = "CRM Performance Report\n"
            text += "=" * 50 + "\n\n"
            
            for key, value in report.items():
                formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                text += f"{key}: {formatted_value}\n"
                
            self.show_report_result(text, "CRM Performance")
            self.last_report_data = report
            self.last_report_type = "crm_performance"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate CRM report: {str(e)}")
            
    def generate_enhanced_crm_report(self):
        """Generate and display enhanced CRM report."""
        if not self.loan_crm:
            QMessageBox.warning(self, "Warning", "CRM module not available.")
            return
            
        try:
            report = self.report_generator.generate_enhanced_crm_report()
            
            if "error" in report:
                QMessageBox.warning(self, "Warning", f"Enhanced CRM report issue: {report['error']}")
                return
                
            # Create a formatted display of the results
            text = "Enhanced CRM Report\n"
            text += "=" * 50 + "\n\n"
            
            # Performance metrics
            if "performance_metrics" in report:
                text += "Performance Metrics:\n"
                for key, value in report["performance_metrics"].items():
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    text += f"  {key}: {formatted_value}\n"
                text += "\n"
                
            # Client segmentation summary
            if "client_segmentation" in report:
                segmentation = report["client_segmentation"]
                
                if "income_segments" in segmentation:
                    total = sum(segmentation["income_segments"].values())
                    text += "Income Distribution:\n"
                    for segment, count in segmentation["income_segments"].items():
                        percentage = (count / total * 100) if total > 0 else 0
                        text += f"  {segment}: {count} clients ({percentage:.1f}%)\n"
                    text += "\n"
                
                if "credit_score_segments" in segmentation:
                    total = sum(segmentation["credit_score_segments"].values())
                    text += "Credit Score Distribution:\n"
                    for segment, count in segmentation["credit_score_segments"].items():
                        percentage = (count / total * 100) if total > 0 else 0
                        text += f"  {segment}: {count} clients ({percentage:.1f}%)\n"
                    text += "\n"
                    
            self.show_report_result(text, "Enhanced CRM Report")
            self.last_report_data = report
            self.last_report_type = "enhanced_crm"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate enhanced CRM report: {str(e)}")
            
    def generate_forecast_report(self):
        """Generate and display Euribor forecast report."""
        frequency = self.frequency_combo.currentText()
        start_date = self.start_date_edit.text().strip()
        
        if not start_date or not self.is_valid_date(start_date):
            QMessageBox.warning(self, "Warning", "Please enter a valid start date in YYYY-MM-DD format.")
            return
            
        try:
            report = self.report_generator.generate_forecasting_report(
                frequency=frequency,
                start=start_date
            )
            
            if report.empty:
                QMessageBox.warning(self, "Warning", "No data available for the selected period.")
                return
                
            # Create a formatted display of the results
            text = "Euribor Forecast Report\n"
            text += "=" * 50 + "\n\n"
            text += f"Frequency: {frequency}\n"
            text += f"Period: {report['TIME_PERIOD'].min()} to {report['TIME_PERIOD'].max()}\n\n"
            
            # Recent values
            text += "Recent Values:\n"
            recent = report.sort_values("TIME_PERIOD").tail(5)
            for _, row in recent.iterrows():
                period = row["TIME_PERIOD"]
                value = row["OBS_VALUE"]
                trend = "↑" if value > recent["OBS_VALUE"].iloc[0] else "↓" if value < recent["OBS_VALUE"].iloc[0] else "→"
                text += f"  {period}: {value:.3f}% {trend}\n"
            text += "\n"
            
            # Statistics
            text += "Statistics:\n"
            text += f"  Latest: {report['OBS_VALUE'].iloc[-1]:.3f}%\n"
            text += f"  Average: {report['OBS_VALUE'].mean():.3f}%\n"
            text += f"  Min: {report['OBS_VALUE'].min():.3f}%\n"
            text += f"  Max: {report['OBS_VALUE'].max():.3f}%\n"
            
            self.show_report_result(text, "Euribor Forecast")
            self.last_report_data = report
            self.last_report_type = "euribor_forecast"
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate forecast report: {str(e)}")
            
    def export_report(self):
        """Export the last generated report."""
        if not hasattr(self, "last_report_data") or not hasattr(self, "last_report_type"):
            QMessageBox.warning(self, "Warning", "No report has been generated yet.")
            return
            
        export_format = self.export_format_combo.currentText()
        report_type = self.report_type_combo.currentText()
        
        file_filter = "PDF Files (*.pdf)" if export_format == "PDF" else "CSV Files (*.csv)"
        default_ext = ".pdf" if export_format == "PDF" else ".csv"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Report", 
            f"{report_type}_report{default_ext}",
            file_filter
        )
        
        if not filepath:
            return  # User cancelled
            
        try:
            if export_format == "PDF":
                filepath = self.report_generator.export_to_pdf(
                    self.last_report_data,
                    report_type,
                    filepath
                )
                QMessageBox.information(self, "Success", f"Report exported to PDF at: {filepath}")
                
            else:  # CSV
                # For DataFrame-based reports
                if isinstance(self.last_report_data, pd.DataFrame):
                    filepath = self.report_generator.export_report_to_csv(
                        self.last_report_data,
                        filepath
                    )
                    QMessageBox.information(self, "Success", f"Report exported to CSV at: {filepath}")
                else:
                    QMessageBox.warning(
                        self, 
                        "Warning", 
                        "This report type cannot be exported to CSV format. Please choose PDF instead."
                    )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
            
    def show_report_result(self, text, title):
        """Display the report result in a text viewer dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Text display
        text_display = QTextEdit()
        text_display.setReadOnly(True)
        text_display.setText(text)
        layout.addWidget(text_display)
        
        # Buttons
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        
        export_button = QPushButton("Export to PDF")
        export_button.clicked.connect(lambda: self.quick_export_pdf(title))
        
        button_layout.addWidget(export_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec_()
        
    def quick_export_pdf(self, title):
        """Quick export of the current report to PDF."""
        if not hasattr(self, "last_report_data") or not hasattr(self, "last_report_type"):
            QMessageBox.warning(self, "Warning", "No report data available for export.")
            return
            
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save PDF Report", 
            f"{title.lower().replace(' ', '_')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not filepath:
            return  # User cancelled
            
        try:
            filepath = self.report_generator.export_to_pdf(
                self.last_report_data,
                self.last_report_type,
                filepath
            )
            QMessageBox.information(self, "Success", f"Report exported to: {filepath}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export report: {str(e)}")
            
    def is_valid_date(self, date_string):
        """Check if a string is a valid date in YYYY-MM-DD format."""
        import re
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            return False
            
        try:
            import datetime
            year, month, day = map(int, date_string.split('-'))
            datetime.date(year, month, day)
            return True
        except ValueError:
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Carica i font
    font_files = [
        os.path.join(os.path.dirname(__file__), 'fonts', 'SourceSansPro-Regular.ttf'),
        os.path.join(os.path.dirname(__file__), 'fonts', 'SourceSansPro-Bold.ttf'),
        os.path.join(os.path.dirname(__file__), 'fonts', 'SourceSansPro-Italic.ttf'),
    ]

    # Carica i font e imposta il font di default
    loaded_font_family = None
    for font_file in font_files:
        if os.path.exists(font_file):
            font_id = QFontDatabase.addApplicationFont(font_file)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    loaded_font_family = font_families[0]
                    print(f"Font caricato con successo: {loaded_font_family}")
                    break

    # Imposta il font di default per tutta l'applicazione
    if loaded_font_family:
        default_font = QFont(loaded_font_family, 10)  # Puoi modificare la dimensione (10) come preferisci
        app.setFont(default_font)
        print(f"Font predefinito impostato: {loaded_font_family}")
    else:
        print("Usando font di sistema come fallback")

        
    # Mostra la finestra di login
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        # Se il login ha successo, procedi con la visualizzazione dello splash screen e dell'applicazione principale
        
        # Recupera i parametri del database dal dialogo di login
        db_params = login_dialog.get_db_params()
        
        # Crea un'istanza di DbManager con i parametri del database
        db_manager = DbManager(**db_params)
        
        # Crea le tabelle necessarie nel database
        db_manager.create_db()

        # Nel main()
        try:
            # Percorso assoluto per debug
            splash_path = os.path.join(os.path.dirname(__file__), 'assets', 'loan_splashscreen.png')
            splash_pix = QPixmap(splash_path)
            if splash_pix.isNull():
                print(f"Errore: Impossibile caricare lo splash screen da {splash_path}")
            else:
                splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
                splash.setMask(splash_pix.mask())
                splash.show()
        except Exception as e:
            print(f"Errore nel caricamento dello splash screen: {e}")

        # Simulate some loading time
        time.sleep(6)
        
        # Create and show main window
        main_window = LoanApp(db_manager)
        main_window.show()
        # Ensure light theme is set
        theme_manager = ThemeManager()
        theme_manager.current_theme = "light"
        main_window.setStyleSheet(theme_manager.get_stylesheet())
        splash.finish(main_window)
        
        # Start event loop
        try:
            sys.exit(app.exec_())
        except SystemExit:
            pass
    else:
        # Se il login fallisce, esci dall'applicazione
        sys.exit()
