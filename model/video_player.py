from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget
import sys
import os

# Detecta si estás usando PyInstaller (modo ejecutable)
def is_frozen():
    return getattr(sys, 'frozen', False)

# Ruta base para VLC portable
def get_vlc_base_path():
    if is_frozen():
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "third_party", "vlc"))

# Establece las rutas necesarias para VLC
def setup_vlc_environment():
    vlc_base = get_vlc_base_path()
    plugins_path = os.path.join(vlc_base, "plugins")
    
    os.environ["VLC_PLUGIN_PATH"] = plugins_path

    # if sys.platform == "win32":
    #     os.add_dll_directory(vlc_base)  # Python 3.8+
    # return True

try:
    setup_vlc_environment()
    import vlc
except Exception as e:
    print(f"[!] Error cargando VLC: {e}")


class VLCPlayer(QWidget):
    # Señal que se emite cuando el widget se destruye correctamente
    destroyed_signal = pyqtSignal()

    def __init__(self, url):
        """
        Inicializa el reproductor VLC embebido dentro de un QWidget.
        :param url: Ruta o URL del archivo de video a reproducir.
        """
        super().__init__()
        self.setWindowTitle("VLC Player")
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.resize(800, 600)

        # Instancia VLC
        self.instance = vlc.Instance(['--video-on-top', '--no-plugins-cache', '--quiet'])
        self.player = self.instance.media_player_new()

        media = self.instance.media_new(url)
        self.player.set_media(media)

        # Asignar canvas de video según sistema
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(self.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(self.winId())
        elif sys.platform == "darwin":
            self.player.set_nsobject(int(self.winId()))

        print("🎥 Reproducción iniciada.")
        self.player.play()

    def keyPressEvent(self, event):
        """
        Controla volumen y seek con flechas del teclado:
          - Up: subir volumen +10
          - Down: bajar volumen -10
          - Right: adelantar 10 s
          - Left: retroceder 10 s
        """
        key = event.key()
        # Volumen actual y posición actual
        current_vol = self.player.audio_get_volume()
        current_time = self.player.get_time()

        if key == Qt.Key_Up:
            new_vol = min(current_vol + 10, 100)
            self.player.audio_set_volume(new_vol)
            print(f"🔊 Volumen: {new_vol}%")
        elif key == Qt.Key_Down:
            new_vol = max(current_vol - 10, 0)
            self.player.audio_set_volume(new_vol)
            print(f"🔉 Volumen: {new_vol}%")
        elif key == Qt.Key_Right:
            # get_time devuelve ms; sumamos 10000 ms => 10 s
            new_time = current_time + 10_000
            self.player.set_time(new_time)
            print(f"⏩ Adelantado a {new_time//1000}s")
        elif key == Qt.Key_Left:
            new_time = max(current_time - 10_000, 0)
            self.player.set_time(new_time)
            print(f"⏪ Retrocedido a {new_time//1000}s")
        else:
            # Para cualquier otra tecla, comportarse como QWidget normal
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """
        Al cerrar, detenemos y liberamos recursos de VLC, emitimos señal.
        """
        print("🛑 Cerrando VLCPlayer...")
        try:
            self.player.stop()
            self.player.release()
            self.instance.release()
        except Exception as e:
            print(f"[!] Error al liberar VLC: {e}")

        self.destroyed_signal.emit()
        event.accept()
