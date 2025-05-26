# app/controller/video_controller.py

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox
from model.video_player import VLCPlayer
from model.m3u8_intercept import M3U8Worker

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)


class VideoManager(QObject):
    """
    Clase encargada de coordinar la reproducción de videos en streaming utilizando PyQt5.

    Funciona como intermediario entre la interfaz gráfica (view), el procesamiento de streams m3u8,
    y el reproductor de video basado en VLC.
    """

    # Señales para comunicar eventos:
    url_ready = pyqtSignal(str)          # Emitida cuando una URL de stream ha sido procesada y está lista.
    play_requested = pyqtSignal(str)     # Emitida cuando se solicita la reproducción de un stream.

    def __init__(self, view):
        """
        Inicializa el VideoManager.

        :param view: La vista principal (usualmente una ventana QMainWindow).
        """
        super().__init__()
        self.view = view
        self.active_player = None        # Instancia del reproductor VLC activo.
        self.m3u8_thread = None          # Hilo que ejecuta el procesamiento de streams m3u8.
        self.m3u8_processor = None       # Objeto encargado de procesar la URL m3u8.

    def _cleanup_player(self):
        """Cierra el reproductor de video si está activo."""
        logger.info('[+] _cleanup_player - cerrando jugador activo')
        if self.active_player:
            self.active_player.close()

    def _player_cleanup(self):
        """Limpia la referencia al reproductor de video activo (después de ser destruido)."""
        logger.info('[+] _player_cleanup - referencia eliminada')
        self.active_player = None

    def _cleanup_m3u8_thread(self):
        """
        Detiene y limpia el hilo y objeto de procesamiento M3U8 si existen,
        para liberar recursos.
        """
        logger.info('[+] _cleanup_m3u8_thread - limpiando recursos de m3u8')
        if self.m3u8_thread and self.m3u8_thread.isRunning():
            self.m3u8_thread.quit()
            self.m3u8_thread.wait()

        if self.m3u8_thread:
            self.m3u8_thread.deleteLater()
            self.m3u8_thread = None

        if self.m3u8_processor:
            self.m3u8_processor.deleteLater()
            self.m3u8_processor = None

    def shutdown(self):
        """
        Método llamado al cerrar la aplicación. Limpia todos los recursos activos.
        """
        logger.info('[+] shutdown - cerrando aplicación')
        self._cleanup_m3u8_thread()
        self._cleanup_player()

    @pyqtSlot(str)
    def handle_processing_error(self, error):
        """
        Slot que maneja errores ocurridos durante el procesamiento de la URL m3u8.

        :param error: Mensaje de error recibido.
        """
        logger.info('[+] handle_processing_error - ocurrió un error durante el procesamiento')
        QMessageBox.critical(self.view, "Error", f"Error M3U8: {error}")
        self.view.status_bar.setText("Error en procesamiento")

    def play_stream(self, url, connect_play_request=True):
        """
        Inicia el procesamiento de una URL de stream m3u8 en un hilo separado.

        :param url: La URL a procesar.
        :param connect_play_request: Si es True, se conecta directamente al slot de reproducción.
        """
        logger.info('[+] play_stream - preparando hilo de reproducción')
        self._cleanup_m3u8_thread()

        # Crear nuevo hilo y mover el procesador M3U8 allí
        self.m3u8_thread = QThread()
        self.m3u8_processor = M3U8Worker(url)
        self.m3u8_processor.moveToThread(self.m3u8_thread)

        # Conexiones de señales
        self.m3u8_thread.started.connect(self.m3u8_processor.process)
        self.m3u8_processor.m3u8_ready.connect(self.on_m3u8_ready)
        self.m3u8_processor.error_occurred.connect(self.handle_processing_error)
        self.m3u8_processor.finished.connect(self._cleanup_m3u8_thread)

        if connect_play_request:
            self.m3u8_processor.m3u8_ready.connect(self.play_requested)
            self.m3u8_processor.m3u8_ready.connect(self.handle_play_request)

        # Inicia el hilo

        self.m3u8_thread.start()
        self.view.status_bar.setText("Obteniendo stream...")

    @pyqtSlot(str)
    def handle_play_request(self, url):
        """
        Slot encargado de iniciar la reproducción del stream usando VLCPlayer.

        :param url: URL del stream ya procesada.
        """
        logger.info('[+] handle_play_request - intentando reproducir')
        self._cleanup_player()
        try:
            self.active_player = VLCPlayer(url)
            self.active_player.destroyed_signal.connect(self._player_cleanup)
            self.active_player.show()
        except Exception as e:
            logger.error(f'[-] Error al iniciar VLCPlayer: {e}')
            QMessageBox.critical(self.view, "Error", f"Error VLC: {str(e)}")

    @pyqtSlot(str)
    def on_m3u8_ready(self, url):
        """
        Slot que maneja cuando la URL m3u8 ha sido procesada correctamente.

        :param url: La URL del stream lista para reproducir.
        """
        logger.info(f'[+] on_m3u8_ready - URL del stream procesada: {url}')
        self.view.status_bar.setText("Stream listo")
        self.view.stream_url = url  # Almacena la URL en la vista
        self.url_ready.emit(url)    # Emite señal para notificar que la URL está lista
