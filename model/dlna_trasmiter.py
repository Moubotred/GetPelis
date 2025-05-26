# app/model/dlba_trasnmiter.py

import logging
import threading
from PyQt5.QtCore import QObject, pyqtSignal

from utils_Qt.http_server import ThreadedHTTPServer, StreamHandler
from utils_Qt.upnp import discover_devices, send_media
from utils_Qt.streaming import get_total_duration
from utils_Qt.plugin import get_local_ip
from utils_Qt.log import logger

import requests

class DlnaWorker(QObject):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, manager_config: dict = None):
        super().__init__()
        cfg = manager_config or {}
        self.control_url = cfg.get("device", "")
        self.stream_url = cfg.get("url", "")
        self.vol = cfg.get("vol", 10)
        self.position = cfg.get("position", "00:00:00")
        self.timeout = cfg.get("timeout", 1)
        self.action = cfg.get("action", "play")
        self.log_level = cfg.get("logLevel", logging.INFO)
        self.proxy_enabled = cfg.get("proxy", False)
        self.proxy_port = cfg.get("proxy_port", 9000)

        logging.basicConfig(level=self.log_level)
        self.http_server = None
        self.http_thread = None

    def run(self):
        """
        Busca dispositivos DLNA y emite un diccionario nombre->control_url.
        """
        try:
            devices = {name: url for name, url in discover_devices(timeout=self.timeout)}
            self.finished.emit(devices)
        except Exception as e:
            logger.error("Error buscando dispositivos DLNA", exc_info=e)
            self.error.emit(str(e))

    def start_streaming(self):
        """
        Inicia el servidor HTTP (proxy) si corresponde y envía media al dispositivo.
        """
        try:
            target_url = self._prepare_media_url()
            # iniciar proxy si es necesario
            if self.proxy_enabled:
                self._send_stream_to_proxy_server()
            # duración del stream original
            duration = get_total_duration(self.stream_url)
            
            # logger.info(f"Duración total: {duration}")

            logger.info(f"Control: {self.control_url}")
            logger.info(f"uri: {target_url}")
            logger.info(f"Duración total: {duration}")


            # enviar media via DLNA
            success = send_media(
                control_url=self.control_url,
                uri=target_url,
                stop_after=duration
            )

            logger.info('DATA INSPECT: {}'.format(success))

            # if not success:
            #     raise RuntimeError("Fallo al enviar media DLNA")
            
            logger.info("Transmisión iniciada correctamente")
        except Exception as e:
            logger.error("Error en start_streaming", exc_info=e)
            self.error.emit(str(e))

    def _prepare_media_url(self) -> str:
        """
        Devuelve URL a usar: proxy HTTP o directo.
        """
        if self.proxy_enabled:
            ip = get_local_ip()
            return f"http://{ip}:{self.proxy_port}/live.mp4"
        return self.stream_url

    # def _start_http_server(self):
    #     """
    #     Inicia servidor HTTP para servir el stream (hls->mp4).
    #     """
    #     if not self.stream_url:
    #         raise ValueError("No hay URL para proxy HTTP.")
    #     # ajustar M3U8 en el handler

    #     StreamHandler.M3U8_URL = self.stream_url
    #     self.http_server = ThreadedHTTPServer(("", self.proxy_port), StreamHandler,m3u8_url=self.stream_url)
    #     self.http_thread = threading.Thread(
    #         target=self.http_server.serve_forever,
    #         daemon=True
    #     )
    #     self.http_thread.start()
    #     logger.info(f"HTTP proxy iniciado en puerto {self.proxy_port}")

    # def stop(self):
    #     """
    #     Detiene el servidor HTTP si está activo.
    #     """
    #     if self.http_server:
    #         self.http_server.shutdown()
    #         self.http_server.server_close()
    #         self.http_server = None
    #         logger.info("HTTP proxy detenido")
    #     if self.http_thread and self.http_thread.is_alive():
    #         self.http_thread.join()
    #         self.http_thread = None

    def _send_stream_to_proxy_server(self):
        """
        Envía la URL al servidor remoto para que la sirva como /live.mp4.
        """
        if not self.stream_url:
            raise ValueError("No hay URL para enviar al servidor proxy remoto.")

        proxy_base_url = f"http://{get_local_ip()}:{self.proxy_port}"  # o usa directamente '192.168.1.109'
        endpoint = f"{proxy_base_url}/set_url"
        try:
            response = requests.post(endpoint, data=self.stream_url, timeout=3)
            response.raise_for_status()
            logger.info(f"URL enviada correctamente al servidor remoto: {self.stream_url}")
        except requests.RequestException as e:
            logger.error("Error al enviar la URL al servidor proxy remoto", exc_info=e)
            raise