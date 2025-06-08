# app/utis/soap_utils.py

import logging
import requests
import os

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)


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

MEDIA_MAP = {
    'mp4': ('video/mp4', 'object.item.videoItem'),
    'm3u8': ('application/x-mpegURL', 'object.item.videoItem'),
    'ts': ('video/mp2t', 'object.item.videoItem'),
    'jpg': ('image/jpeg', 'object.item.imageItem'),
    'jpeg': ('image/jpeg', 'object.item.imageItem'),
    'png': ('image/png', 'object.item.imageItem'),
    'gif': ('image/gif', 'object.item.imageItem'),
}

# --- SOAP ---
def send_soap(control_url, action, body):
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': f'"{ACTIONS[action]}"'
    }
    xml = SOAP_ENVELOPE.format(body=body)
    try:

        resp = requests.post(control_url, data=xml, headers=headers, timeout=50)
        resp.raise_for_status()
        return resp.text
    
    except requests.HTTPError as e:

        logger.error("[SOAP ERROR] %s - %s", e.response.status_code, e.response.text)
        raise

    except requests.RequestException as e:
        logger.error("Error en la solicitud SOAP: %s", e)
        raise


def build_stop():
    return '<u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Stop>'


def build_pause():
    return '<u:Pause xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Pause>'


def build_play():
    return '<u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Play>'


def build_set_uri(uri):
    ext = uri.split('.')[-1].lower().split('&')[0]
    if ext not in MEDIA_MAP:
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
