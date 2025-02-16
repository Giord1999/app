#Imports for the GUI
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QListWidget, QMessageBox, 
                             QTableWidget, QTableWidgetItem, QSplashScreen, QDialog, QPushButton, 
                             QDoubleSpinBox, QSpinBox, QScrollArea, QFormLayout, 
                             QTextEdit, QHBoxLayout, QToolButton, QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QToolButton, QSizePolicy, QScrollArea, QAction, QTabWidget, QFrame, QInputDialog)


from PyQt5.QtGui import QIcon, QPixmap, QFontDatabase, QFont, QFont
from PyQt5.QtCore import Qt, QSize, QTimer


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


#TODO: implementare i tassi variabili


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
                font-size: 12pt;
            }
            
            QMainWindow {
                background-color: #ffffff;
            }
            
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12pt;
                min-width: 80px;
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
            
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #d1d1d1;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                min-height: 25px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #0078d4;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(assets/dropdown_arrow.png);
                width: 12px;
                height: 12px;
            }
            
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
            }
            
            QListWidget::item {
                height: 28px;
                padding: 4px;
                border-radius: 4px;
            }
            
            QListWidget::item:selected {
                background-color: #e5f3ff;
                color: black;
            }
            
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                gridline-color: #f0f0f0;
            }
            
            QTableWidget::item {
                padding: 4px;
            }
            
            QTableWidget::item:selected {
                background-color: #e5f3ff;
                color: black;
            }
            
            QHeaderView::section {
                background-color: #f8f8f8;
                padding: 4px;
                border: none;
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }
            
            QScrollBar:vertical {
                border: none;
                background-color: #f8f8f8;
                width: 14px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                min-height: 30px;
                border-radius: 7px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
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

    def open_additional_costs_dialog(self):
        dialog = AdditionalCostsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.additional_costs = dialog.get_costs()

    def get_loan_data(self):
        return {
            "rate": self.rate_entry.value(),
            "term": self.term_entry.value(),
            "loan_amount": self.pv_entry.value(),
            "downpayment_percent": self.downpayment_entry.value(),
            "amortization_type": self.amortization_combobox.currentText(),
            "frequency": self.frequency_combobox.currentText(),
            "additional_costs": self.additional_costs
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
        costs = {}
        for name_entry, value_entry in self.cost_entries:
            name = name_entry.text().strip()
            value = value_entry.value()
            if name and value > 0:
                costs[name] = value
        
        periodic_cost = self.periodic_cost_entry.value()
        if periodic_cost > 0:
            costs['Periodic Costs'] = periodic_cost
        return costs


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
        
        # Rate input
        self.rate_entry = QDoubleSpinBox()
        self.rate_entry.setRange(0, 100)
        self.rate_entry.setDecimals(4)
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
    
        self.main_layout.addWidget(main_container)


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
            # Creazione dell'oggetto Loan dai dati del database
            loan_id, rate, term, amount, amort_type, frequency, rate_type, use_euribor, update_freq, downpayment, start_date, active = loan_data
            
            loan = Loan(
                db_manager=self.db_manager,
                rate=float(rate),
                term=int(term),
                loan_amount=float(amount),
                amortization_type=amort_type,
                frequency=frequency,
                rate_type=rate_type,
                use_euribor=use_euribor,
                update_frequency=update_freq,
                downpayment_percent=float(downpayment),
                start=start_date.isoformat(),
                loan_id=str(loan_id),
                should_save=False  # Evitiamo di salvarlo di nuovo nel DB
            )
            
            self.loans.append(loan)  # Aggiungiamo l'oggetto Loan alla lista

            # Mostra il prestito nella UI
            loan_text = f"Loan {loan_id} - €{amount:,.2f} ({amort_type})"
            self.loan_listbox.addItem(loan_text)

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


class ChatAssistantDialog(QDialog):

    def __init__(self, loan_app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LoanManager AI Assistant")
        self.loan_app = loan_app
        # Aggiungi l'icona della finestra
        self.setWindowIcon(QIcon(resource_path('loan_icon.ico')))
        # Costruiamo il percorso assoluto al file degli intent
        intents_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'intents.json')
        self.chatbot = Chatbot(intents_file)
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
                return

            # Altrimenti procediamo con il normale flusso di intent
            intent = self.chatbot.get_intent(user_message)
            
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
        intent_actions = {
            "greeting": lambda: self.append_message("Assistant", 
                                    np.random.choice([
                                        "Hi! How can I help you with your loans?",
                                        "Hello! I'm here to help you manage your loans.",
                                        "Good day! What can I do for you today?"
                                    ])),
            "amortization_schedule": lambda: self._handle_amortization(),
            "calculate_taeg": lambda: self._handle_taeg(),
            "compare_loans": lambda: self._handle_compare_loans(),
            "plot_graph": lambda: self._handle_plot()
            
        }

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

    class GuiInputManager:
        """
        Context manager per intercettare le chiamate a input() e sostituirle
        con QInputDialog.getText().
        """
        def __init__(self, parent):
            self.parent = parent
            self.original_input = __builtins__.input
        def __enter__(self):
            __builtins__.input = self.gui_input
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            __builtins__.input = self.original_input
        def gui_input(self, prompt):
            text, ok = QInputDialog.getText(self.parent, "Input", prompt)
            if ok:
                return text
            else:
                raise Exception("Input cancelled by user")
    
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
