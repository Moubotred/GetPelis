#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
from urllib.parse import urlparse
import re
import os
import time
import socket
import struct
import xml.etree.ElementTree as ET
import requests
import threading
import subprocess
import tempfile

# from .utils_Qt.log import logger
# logger.getLogger(__name__)

# Configuración básica de logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

PORT = 9000
M3U8_URL = "https://2goita23a7njj.premilkyway.com/hls2/01/03795/phblack9pqu6_,n,h,.urlset/index-f1-v1-a1.m3u8?t=k_KZs60WemvehWhiFQVw88bOozgESjURdT9v9cXlxn8&s=1747108034&e=129600&f=18977802&srv=vpusxz6e9t3q&i=0.4&sp=500&p1=vpusxz6e9t3q&p2=vpusxz6e9t3q&asn=269826"
SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
ST = 'urn:schemas-upnp-org:service:AVTransport:1'

MEDIA_MAP = {
    'mp4': ('video/mp4', 'object.item.videoItem'),
    'm3u8': ('application/x-mpegURL', 'object.item.videoItem'),
    'ts': ('video/mp2t', 'object.item.videoItem'),
    'jpg': ('image/jpeg', 'object.item.imageItem'),
    'jpeg': ('image/jpeg', 'object.item.imageItem'),
    'png': ('image/png', 'object.item.imageItem'),
    'gif': ('image/gif', 'object.item.imageItem'),
}

SOAP_ENVELOPE = '''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    {body}
  </s:Body>
</s:Envelope>'''

ACTIONS = {
    'Stop': 'urn:schemas-upnp-org:service:AVTransport:1#Stop',
    'Pause': 'urn:schemas-upnp-org:service:AVTransport:1#Pause',
    'SetAVTransportURI': 'urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI',
    'Play': 'urn:schemas-upnp-org:service:AVTransport:1#Play',
}


class StreamHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/live.mp4":
            self.send_response(404)
            self.end_headers()
            logger.warning("Ruta no encontrada: %s", self.path)
            return

        logger.info("Cliente conectado: %s", self.client_address)
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.end_headers()

        ffmpeg_cmd = [
            "ffmpeg",
            "-i", M3U8_URL,
            "-c:v", "libx264",  # Usando un códec más común, como x264
            "-c:a", "aac",
            "-bsf:a", "aac_adtstoasc",
            "-movflags", "frag_keyframe+empty_moov",
            "-f", "mp4",
            "-loglevel", "error",  # Reduce el nivel de logs
            "-"
        ]

        logger.debug("Comando FFmpeg: %s", " ".join(ffmpeg_cmd))

        proc = None
        try:
            with subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capturamos stderr
                bufsize=4096
            ) as proc:
                
                # Hilo para leer errores y evitar bloqueos
                def log_errors():
                    while True:
                        err = proc.stderr.readline()
                        if not err:
                            break
                        logger.error("FFmpeg: %s", err.decode().strip())
                
                import threading
                error_logger = threading.Thread(target=log_errors, daemon=True)
                error_logger.start()

                logger.debug("Esperando paquetes de FFmpeg...")
                # Stream de datos
                while True:
                    chunk = proc.stdout.read(4096)
                    if not chunk:
                        logger.debug("Finalizado el flujo de datos desde FFmpeg.")
                        break

                    try:
                        self.wfile.write(chunk)
                        
                        # logger.debug(f"Enviado un bloque de {len(chunk)} bytes")
                
                    except (ConnectionResetError, BrokenPipeError):
                        logger.warning("Cliente desconectado durante la transmisión")
                        proc.kill()
                        break

        except BrokenPipeError:
            logger.warning("Cliente desconectado antes de iniciar la transmisión")
            if proc:
                proc.kill()

        except Exception as e:
            logger.error("Error crítico en la transmisión: %s", str(e))
            if proc:
                proc.kill()
            self.send_error(500)

    def do_HEAD(self):
        if self.path == '/live.mp4':
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.end_headers()
        else:
            self.send_error(404)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    pass

# --- Discovery ---
def discover_devices(timeout=2):
    logger.info("Iniciando búsqueda de dispositivos UPnP...")
    msg = '\r\n'.join([
        'M-SEARCH * HTTP/1.1',
        f'HOST: {SSDP_ADDR}:{SSDP_PORT}',
        'MAN: "ssdp:discover"',
        f'ST: {ST}',
        'MX: 1', '', ''
    ]).encode('utf-8')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
    sock.settimeout(timeout)
    sock.sendto(msg, (SSDP_ADDR, SSDP_PORT))
    locations = set()
    try:
        while True:
            data, _ = sock.recvfrom(1024)
            for line in data.decode().split('\r\n'):
                # logger.info('[*] data line: {}'.format(line))
                if line.lower().startswith('location:'):
                    locations.add(line.split(':', 1)[1].strip())
    except socket.timeout:
        pass
    devices = []
    for url in locations:
        try:
            resp = requests.get(url, timeout=3)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            ns = {'d': 'urn:schemas-upnp-org:device-1-0'}
            d = root.find('d:device', ns)
            name = d.find('d:friendlyName', ns).text
            logger.debug("Dispositivo encontrado: %s", name)
            for srv in d.find('d:serviceList', ns).findall('d:service', ns):
                if 'AVTransport' in srv.find('d:serviceType', ns).text:
                    ctrl = srv.find('d:controlURL', ns).text
                    base = url[:url.find('/', url.find('//')+2)]
                    devices.append((name, base + ctrl))
                    logger.debug("Control URL: %s", base + ctrl)
        except Exception as e:
            logger.error("Error al descubrir dispositivo: %s", e)
            continue
    if not devices:
        logger.warning("No se encontraron dispositivos compatibles.")
    return devices

# --- SOAP ---
def send_soap(control_url, action, body):
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': f'"{ACTIONS[action]}"'
    }
    xml = SOAP_ENVELOPE.format(body=body)
    try:

        resp = requests.post(control_url, data=xml, headers=headers, timeout=10)
        resp.raise_for_status()

        return resp.text
    except requests.HTTPError as e:

        logger.error("[SOAP ERROR] %s - %s", e.response.status_code, e.response.text)
        raise

    except requests.RequestException as e:
        logger.error("Error en la solicitud SOAP: %s", e)
        raise

# --- Builders ---
def build_stop(): 
    return '<u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Stop>'

def build_pause(): 
    return '<u:Pause xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Pause>'

def build_set_uri(uri):
    # parsed = urlparse(uri)
    # path = parsed.path
    # ext = os.path.splitext(path)[1][1:].lower()

    ext = uri.split('.')[-1].lower()  # ❌ Esto da: '4&sp=500...'

    # print(ext)

    if ext not in MEDIA_MAP:
        logger.error("Formato no soportado: .%s", ext)
        raise ValueError(f"Formato no soportado: .{ext}")
    
    mime, upnp_class = MEDIA_MAP[ext]
    didl = (
        f'<DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" '
        f'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" '
        f'xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/">'
        f'<item id="0" parentID="0" restricted="1">'
        f'<dc:title>{os.path.basename(uri)}</dc:title>'
        f'<upnp:class>{upnp_class}</upnp:class>'
        f'<res protocolInfo="http-get:*:{mime}:*">{uri}</res>'
        f'</item></DIDL-Lite>'
    )
    esc = didl.replace('<','&lt;').replace('>','&gt;')
    return (
        f'<u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">'
        f'<InstanceID>0</InstanceID>'
        f'<CurrentURI>{uri}</CurrentURI>'
        f'<CurrentURIMetaData>{esc}</CurrentURIMetaData>'
        f'</u:SetAVTransportURI>'
    )

def build_play():
    return '<u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Play>'

# --- Conversion m3u8 -> mp4 ---
def convert_m3u8_to_mp4(m3u8_url, output_path=None):
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix='.mp4')
        os.close(fd)
    cmd = ['ffmpeg', '-y', '-i', m3u8_url, '-c', 'copy', output_path]
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info("Archivo MP4 generado en %s", output_path)
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else "Error desconocido"
        logger.error("Error al convertir m3u8 a MP4: %s", error_message)
        raise
    return output_path  # Retorno corregido

# --- Control básico wrappers ---
def send_media(control_url, uri, stop_after=0):

    logger.info("Enviando medio a %s: %s", control_url, uri)

    try:
        # 1) Detener cualquier reproducción previa
        try:
            send_soap(control_url, 'Stop', build_stop())
            logger.info("Comando Stop enviado.")

        except Exception:
            logger.debug("Ignorando error en Stop inicial (puede que no hubiera nada que detener).")

        # Pequeña pausa para asegurarnos de que el estado cambie a STOPPED
        time.sleep(1)

        # 2) Configurar la nueva URI
        send_soap(control_url, 'SetAVTransportURI', build_set_uri(uri))
        logger.info("Comando SetAVTransportURI enviado.")

        # Dar un momento al dispositivo para procesar el nuevo URI
        time.sleep(1)

        # 3) Iniciar reproducción
        send_soap(control_url, 'Play', build_play())
        logger.info("Comando Play enviado.")

        # 4) (Opcional) Programar un Stop tras stop_after segundos
        if stop_after > 0:
            def _delayed_stop():
                try:
                    send_soap(control_url, 'Stop', build_stop())
                    logger.info("Comando Stop programado enviado.")
                except Exception as e:
                    logger.error("Error al enviar Stop programado: %s", e)

            timer = threading.Timer(stop_after, _delayed_stop)
            timer.daemon = True
            timer.start()
            logger.info("Stop programado en %d segundos.", stop_after)

        return True

    except Exception as e:
        logger.error("Error al enviar medio: %s", e)
        return False

def pause_media(control_url): 
    return send_soap(control_url, 'Pause', build_pause())

def stop_media(control_url): 
    return send_soap(control_url, 'Stop', build_stop())

def obtener_duracion_total(url_m3u8):
    # Descarga el archivo M3U8
    response = requests.get(url_m3u8)
    if response.status_code != 200:
        print("Error al descargar el archivo .m3u8")
        return None
    
    # Contenido del archivo M3U8
    m3u8_content = response.text

    # Buscar todas las duraciones de los segmentos (valores de EXTINF)
    duraciones = re.findall(r'#EXTINF:(\d+\.\d+),', m3u8_content)

    # Convertir las duraciones de los segmentos a float
    duraciones = [float(d) for d in duraciones]

    # Calcular la duración total sumando todas las duraciones
    duracion_total = sum(duraciones)

    bach = f'{duracion_total:.2f}'

    # Retornar la duración total
    return bach

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No importa si esta IP no es accesible
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


# if __name__ == "__main__":
    # logger.info(f"Sirviendo http://0.0.0.0:{PORT}/live.mp4 desde {M3U8_URL}")
    
    # server = ThreadedHTTPServer(("", PORT), StreamHandler)
    # server_thread = threading.Thread(target=server.serve_forever)
    # server_thread.daemon = True
    # server_thread.start()

    # Descubrir el dispositivo y enviar video
    # iot = discover_devices()

    # print(iot)
    
    # if iot:

    #     LOCAL_IP = get_local_ip()

    #     server_dlna = iot[0][1]

    #     time_duraction = obtener_duracion_total(M3U8_URL)

    #     send_media(server_dlna, 'http://{}:{}/live.mp4'.format(LOCAL_IP,PORT), stop_after=time_duraction)
        
    #     uri = iot[0][1]
        # send_media(disp,'http://192.168.1.109:7000/ror.mp4',stop_after=30)

    # else:
    #     logger.warning("No se encontraron dispositivos.")
    
    # try:
    #     server_thread.join()

    # except KeyboardInterrupt:
    #     logger.info("\nServidor detenido.")

