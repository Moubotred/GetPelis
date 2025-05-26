# app/view/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QGroupBox,
    QCheckBox, QSpinBox, QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt


class MainWindow(QMainWindow):
    # Señal personalizada para emitir una solicitud de reproducción
    playRequested = pyqtSignal(str, name="playRequested")

    def __init__(self):
        super().__init__()

        self.title_results = {}
        self.current_imdb_id = ""
        self.servers = {}

        self.theme_switch = QCheckBox("🌙 Modo Oscuro")  # Estilo switch simple
        self.theme_switch.setChecked(True)
        self.toggle_theme(Qt.Checked)
        self.theme_switch.stateChanged.connect(self.toggle_theme)
        
        self.auto_services = QCheckBox("automaticos")  # Estilo switch simple
        self.auto_services.setChecked(True)

        # funciona aun no implementada
        # self.external_services = QCheckBox("externos") 
        # self.external_services.setChecked(False)
        

        self.setWindowTitle("UI_Tokio_X")
        self.setGeometry(100, 100, 300, 500)

        # --- Contenedor principal ---
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # === 🔍 SECCIÓN DE BÚSQUEDA ===
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar películas o programas de TV...")
        self.search_btn = QPushButton("Buscar")
        # self.search_btn.clicked.connect(self.on_search_clicked)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # === 📃 RESULTADOS DE BÚSQUEDA ===
        self.results_list = QListWidget()
        # self.results_list.itemClicked.connect(self.on_result_selected)
        layout.addWidget(self.results_list)
        layout.addWidget(self.theme_switch)
        layout.addWidget(self.auto_services)
        # layout.addWidget(self.external_services)

        # === 🌗 SWITCHES: Tema y Auto-Services ===
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(self.theme_switch)
        switch_layout.addWidget(self.auto_services)
        # switch_layout.addWidget(self.external_services)
        layout.addLayout(switch_layout)


        # === 📺 CONTROLES DE SERIE TV ===
        self.series_group = QGroupBox("TV Series Opciones")
        self.series_group.setVisible(False)
        series_layout = QVBoxLayout()

        # === [*] ESPECIFICAR EL CHECK DE SERIE  
        self.series_check = QCheckBox("¿Es una serie de televisión?")
        # self.series_check.stateChanged.connect(self.toggle_series_options)
        series_layout.addWidget(self.series_check)


        # Temporada
        season_layout = QVBoxLayout()
        self.season_spin = QSpinBox()
        self.season_spin.setMinimum(1)
        season_layout.addWidget(QLabel("Temporada:"))
        season_layout.addWidget(self.season_spin)

        # Episodio
        episode_layout = QVBoxLayout()
        self.episode_spin = QSpinBox()
        self.episode_spin.setMinimum(1)
        episode_layout.addWidget(QLabel("Episodio:"))
        episode_layout.addWidget(self.episode_spin)

        series_layout.addLayout(season_layout)
        series_layout.addLayout(episode_layout)
        self.series_group.setLayout(series_layout)
        layout.addWidget(self.series_group)


        # === 🌐 SELECCIÓN DE SERVIDORES ===
        layout.addWidget(QLabel("Servidores disponibles:"))
        self.servers_list = QListWidget()
        layout.addWidget(self.servers_list)

        barra = QHBoxLayout()

        self.play_btn = QPushButton("reproducir")
        # self.play_btn.clicked.connect(self.on_play_clicked)
        self.play_btn.setEnabled(False)
        barra.addWidget(self.play_btn)

        self.validate_btn = QPushButton("servidores")
        # self.validate_btn.clicked.connect(self.on_validate_clicked)
        barra.addWidget(self.validate_btn)

        self.transmit_btn = QPushButton("trasmitir Tv")
        # self.transmit_btn.setVisible(False)
        # self.transmit_btn.setEnabled(False)
        # self.validate_btn.clicked.connect(self.on_validate_clicked)
        barra.addWidget(self.transmit_btn)

        layout.addLayout(barra)

        # === ℹ️ ESTADO ===
        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_bar)

    # Puedes definir funciones como estas para usar desde el controlador si prefieres
    def get_search_text(self):
        return self.search_input.text()

    def show_series_options(self, show: bool):
        self.series_group.setVisible(show)

    def add_search_result(self, title: str):
        self.results_list.addItem(title)

    def clear_results(self):
        self.results_list.clear()

    def add_server(self, name: str):
        self.servers_list.addItem(name)

    def clear_servers(self):
        self.servers_list.clear()

    def set_status(self, message: str):
        self.status_bar.setText(message)

    def toggle_theme(self, state):
        if state == Qt.Checked:
            # Tema oscuro
            self.setStyleSheet("""
                QWidget {
                    background-color: #2E2E2E;
                    color: white;
                }
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: 1px solid #666;
                    padding: 5px;
                }
                QLineEdit, QListWidget, QSpinBox {
                    background-color: #333;
                    color: white;
                    border: 1px solid #666;
                }
            """)
            self.theme_switch.setText("🌞 Modo Claro")
        else:
            # Tema claro
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    color: black;
                }
                QPushButton {
                    background-color: #eee;
                    color: black;
                    border: 1px solid #ccc;
                    padding: 5px;
                }
                QLineEdit, QListWidget, QSpinBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
            """)
            self.theme_switch.setText("🌙 Modo Oscuro")

