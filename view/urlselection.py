# app/view/urlselection.py

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton
from controller.video_controller import VideoManager

import logging
logger = logging.getLogger(__name__)


class UrlSelectionDialog(QDialog):
    def __init__(self, view = None, urls = None, parent=None):
        super().__init__()

        self.setWindowTitle("Servicio Stream")
        self.resize(250, 100)

        if not urls:
            return

        self.urls = list(urls)

        # Layout del diálogo
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Selecciona Un Servicio de Stream"))

        # Lista de URLs disponibles
        self.list_widget = QListWidget()
        self.list_widget.addItems(urls)
        layout.addWidget(self.list_widget)

        # Botón para confirmar selección
        select_button = QPushButton("Seleccionar")
        select_button.clicked.connect(self.select_url)
        layout.addWidget(select_button)

        self.setLayout(layout)
        self.selected_url = None

        # self.video_manager.play_requested.connect(self.video_manager.handle_play_request)

        if parent:
            self.move(parent.frameGeometry().center() - self.rect().center())

    def select_url(self):
        """Obtiene la URL seleccionada del diálogo."""
        logger.info('[+] Entrando en select_url')
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.selected_url = selected_items[0].text()
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, selecciona una URL.")

