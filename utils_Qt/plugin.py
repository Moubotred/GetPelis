import socket
from .upnp import discover_devices

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)



def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No importa si esta IP no es accesible
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

        # return '192.168.1.109'
    
    finally:
        s.close()



def get_dlna_devices():
    data = {}
    for d in discover_devices():
        # Suponiendo que d es una tupla como ('llave', valor)
        data[d[0]] = d[1]
    return data


# ips =  get_dlna_devices()
# print(ips)