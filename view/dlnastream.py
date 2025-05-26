# app/view/dlnastream.py

from PyQt5.QtWidgets import QDialog, QMessageBox,QVBoxLayout, QLabel, QListWidget, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal
from model.dlna_trasmiter import DlnaWorker
from controller.video_controller import VideoManager

import logging
logger = logging.getLogger(__name__)

class DlnaStreamDialog(QDialog):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url_server: str = None, parent=None):
        super().__init__(parent)

        logger.info("Inicializando DlnaStreamDialog")

        self.setWindowTitle("Dispositivos DLNA Disponibles")
        self.resize(300, 200)
        self.selected_device = None
        self.devices = {}
        self.url_plantilla = url_server
        self.current_stream_url = None
        self.location = None
        self.name = None

        self.is_streaming_active = False  # Bandera para controlar el estado del streaming
        self.current_stream_worker = None  # Referencia al worker actual


        self.video_manager = VideoManager(parent)

        # UI Setup
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Haz clic en 'Buscar Dispositivos'")
        self.layout.addWidget(self.label)

        self.device_list = QListWidget()
        self.layout.addWidget(self.device_list)

        # Botón: Buscar Dispositivos
        self.buscar_button = QPushButton("Buscar Dispositivos")
        self.buscar_button.clicked.connect(self.start_device_search)
        self.layout.addWidget(self.buscar_button)

        # Botón: Transmitir
        self.transmitir_button = QPushButton("Transmitir")
        self.transmitir_button.setEnabled(False)  # Solo se habilita tras la búsqueda
        self.video_manager.url_ready.connect(self.handle_stream_url)
        self.transmitir_button.clicked.connect(self.start_dlna_stream)


        self.layout.addWidget(self.transmitir_button)

        if parent:
            self.move(parent.frameGeometry().center() - self.rect().center())

    def start_device_search(self):
        logger.info("Iniciando búsqueda de dispositivos DLNA en segundo plano...")

        # if hasattr(self, 'thread') and self.thread.isRunning():
        #     QMessageBox.warning(self, "Aviso", "Ya hay una búsqueda en curso.")
        #     return

        self.thread = QThread()
        self.worker = DlnaWorker({
            'proxy_port': 9000,
            'timeout': 2,
        })

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_devices_found)
        self.worker.error.connect(self.on_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.label.setText("Buscando dispositivos...")

    def on_devices_found(self, devices: dict):
        logger.info(f"Dispositivos DLNA encontrados: {len(devices)}")

        if not devices:
            QMessageBox.information(self, "Dispositivos", "No se encontraron dispositivos disponibles.")
            self.label.setText("No se encontraron dispositivos.")
            return

        self.devices = list(devices.items())
        self.device_list.clear()

        for name, ip in self.devices:
            self.device_list.addItem(name)

        self.label.setText("Seleccione un dispositivo:")
        self.transmitir_button.setEnabled(True)

    def on_error(self, message):
        logger.error(f"Error al detectar dispositivos DLNA: {message}")
        QMessageBox.critical(self, "Error", f"No se pudo obtener dispositivos:\n{message}")
        self.close()

    def handle_stream_url(self, url):
        """Guarda la URL del stream cuando está lista."""
        self.current_stream_url = url

        if self.is_streaming_active and self.current_stream_worker:
            self.stop_current_stream()

        logger.info('[+] HANDLE STREAM: {}'.format(self.current_stream_url))

        logger.info(f"Transmitiendo a: {self.name} ({self.location})")
        logger.info('----------> device: {}'.format(self.name))
        logger.info('----------> Uri: {}'.format(self.location))
        logger.info('----------> url plantilla: {}'.format(self.url_plantilla))
        logger.info('----------> url M3U8: {}'.format(self.current_stream_url))


        logger.info(f"Transmitiendo a: {self.name} ({self.location})")

        self.stream_thread = QThread()
        self.stream_worker = DlnaWorker({
            'device': self.location,
            'url': self.current_stream_url,
            'proxy': True,
            'proxy_port': 18000,
            'action': 'play',
        })


        self.current_stream_worker = self.stream_worker  # Guardar referencia

        self.stream_worker.moveToThread(self.stream_thread)
        self.stream_thread.started.connect(self.stream_worker.start_streaming)
        self.stream_worker.error.connect(self.on_error)

        self.stream_thread.finished.connect(self.stream_worker.deleteLater)
        self.stream_worker.error.connect(self.stream_thread.quit)

        self.stream_worker.finished.connect(self.stream_thread.quit)
        self.stream_worker.finished.connect(self.stream_worker.deleteLater)
        self.stream_thread.finished.connect(self.stream_thread.deleteLater)

        self.stream_thread.start()
        self.is_streaming_active = True

        self.hide()
        # self.accept()

    def stop_current_stream(self):
        """Detiene la transmisión actual y limpia recursos"""
        if self.current_stream_worker:
            try:
                self.current_stream_worker.stop()
                self.is_streaming_active = False
                logger.info("Transmisión anterior detenida")
            except Exception as e:
                logger.error(f"Error al detener transmisión: {e}")

        if hasattr(self, 'stream_thread') and self.stream_thread.isRunning():
            logger.info("Esperando cierre de hilo de transmisión DLNA...")
            self.stream_thread.quit()
            self.stream_thread.wait()

        self.current_stream_worker = None
        self.stream_thread = None
    

    def start_dlna_stream(self):

        if not self.url_plantilla:
            QMessageBox.critical(self, "Error", "No se proporcionó URL de transmisión.")
            return

        selected_items = self.device_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecciona un dispositivo.")
            return

        index = self.device_list.row(selected_items[0])
        name, location = self.devices[index]

        self.location = location
        self.name = name

        self.video_manager.play_stream(self.url_plantilla,connect_play_request=False)
    
    def closeEvent(self, event):
        """Maneja el cierre del diálogo"""
        # No detenemos el streaming aquí, solo limpiamos los hilos de búsqueda
        thr = getattr(self, 'thread', None)
        if thr is not None:
            try:
                if thr.isRunning():
                    thr.quit()
                    thr.wait()
            except RuntimeError:
                pass
            
            finally:
                self.thread = None

        # No detenemos el stream_thread aquí para que continúe
        event.accept()
        