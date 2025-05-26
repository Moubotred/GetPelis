# app/utils_Qt/upnp.py

import time
import logging
import socket
import struct
import requests
import xml.etree.ElementTree as ET
from .soap_utils import send_soap, build_stop, build_pause, build_play, build_set_uri
import threading

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)


SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
ST = 'urn:schemas-upnp-org:service:AVTransport:1'

# --- Dispositivos ---
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
                if line.lower().startswith('location:'):
                    locations.add(line.split(':', 1)[1].strip())
    except socket.timeout:
        pass

    devices = []
    for url in locations:
        try:
            resp = requests.get(url, timeout=10)
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
        logger.warning("[-] No se encontraron dispositivos compatibles.")
        
    return devices

# --- Control básico wrappers ---
def send_media(control_url, uri, stop_after=0):

    logger.info("Enviando medio a %s: %s", control_url, uri)

    # conversion de dato stop_after a dato float ya que lo 
    # entrega como una cadena str y lanza un false ya que 
    # no valida el tipo de dato correcto
    
    stop_after = float(stop_after)

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
        time.sleep(4)

        # 3) Iniciar reproducción
        send_soap(control_url, 'Play', build_play())
        logger.info("Comando Play enviado.")

        # logger.info("====> Tiempo: {}".format(stop_after))
        # logger.info("====> Tipo de dato: {}".format(type(stop_after)))
        
        # 4) (Opcional) Programar un Stop tras stop_after segundo
        if stop_after.is_integer():
        #if stop_after > 0:
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
        logger.error("Error al enviar medio: {}".format(e))
        return False

# --- Opcion de STOP ---
def stop_media(control_url):
    return send_soap(control_url, 'Stop', build_stop())

# --- Opcion de PAUSA ---
def pause_media(control_url):
    return send_soap(control_url, 'Pause', build_pause())
