# app/utils_Qt/http_server.py

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import subprocess
import threading
from .streaming import build_ffmpeg_command

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/live.mp4":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.end_headers()

        ffmpeg_cmd = build_ffmpeg_command(self.server.m3u8_url)

        try:
            with subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:

                def log_errors():
                    for err in proc.stderr:
                        logger.error("FFmpeg: %s", err.decode().strip())

                threading.Thread(target=log_errors, daemon=True).start()

                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError):
                        proc.kill()
                        break
                    
        except Exception as e:
            logger.error("Error crítico en la transmisión: %s", e)
            self.send_error(500)

    def do_HEAD(self):
        if self.path == '/live.mp4':
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.end_headers()
        else:
            self.send_error(404)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    def __init__(self, server_address, handler_class, m3u8_url):
        super().__init__(server_address, handler_class)
        self.m3u8_url = m3u8_url

