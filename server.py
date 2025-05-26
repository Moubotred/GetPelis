#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import threading
import logging
import socket
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

PORT = 18000

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
)
logger = logging.getLogger("proxy_stream")

# Estado global protegido por un lock
CURRENT_M3U8_URL = None
CURRENT_M3U8_LOCK = threading.Lock()


def get_local_ip():
    """Devuelve la IP local usada para salir a Internet."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Server multihilo."""
    daemon_threads = True


class StreamHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path != "/set_url":
            return self.send_error(404, "Ruta no válida")

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        m = re.search(r"(https?://[^\s]+)", body)

        logger.info('[+] datos: {}'.format(body))

        if not m:
            return self.send_error(400, "URL no válida en el cuerpo")

        url = m.group(1)
        with CURRENT_M3U8_LOCK:
            global CURRENT_M3U8_URL
            CURRENT_M3U8_URL = url

        logger.info("URL establecida: %s", url)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(
            f"http://{get_local_ip()}:{PORT}/live.mp4\n".encode()
        )

    def do_GET(self):
        if self.path != "/live.mp4":
            return self.send_error(404, "Ruta no encontrada")

        with CURRENT_M3U8_LOCK:
            m3u8 = CURRENT_M3U8_URL

        if not m3u8:
            self.send_response(503)
            self.end_headers()
            return self.wfile.write(b"No hay una fuente activa.\n")

        logger.info("Cliente %s solicitando /live.mp4", self.client_address)
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.end_headers()

        cmd = [
            "ffmpeg",
            "-threads", "1",  # Limita uso de CPU
            "-i", m3u8,
            "-c:v", "libx264",  # Requiere recodificación (más CPU)
            "-preset", "ultrafast",  # Reduce carga de CPU
            "-c:a", "aac",
            "-b:a", "128k",
            "-bsf:a", "aac_adtstoasc",
            "-movflags", "+frag_keyframe+empty_moov",
            "-f", "mp4",
            "-loglevel", "error",
            "-"
        ]
        
        logger.debug("Ejecutando: %s", " ".join(cmd))

        try:
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                # hilo para leer stderr y evitar bloqueos
                def drain_err():
                    for line in proc.stderr:
                        logger.error("ffmpeg: %s", line.decode().strip())
                threading.Thread(target=drain_err, daemon=True).start()

                # enviar chunks al cliente
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        logger.warning("Cliente desconectado, matando ffmpeg")
                        proc.kill()
                        break
        except Exception as e:
            logger.error("Error en transmisión: %s", e)
            return self.send_error(500, "Error interno")

    def do_HEAD(self):
        if self.path == '/live.mp4':
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.end_headers()
        else:
            self.send_error(404)


if __name__ == "__main__":
    logger.info("Iniciando proxy en puerto %d", PORT)
    server = ThreadedHTTPServer(("", PORT), StreamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor")
        server.shutdown()
        server.server_close()
