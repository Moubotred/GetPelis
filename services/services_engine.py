import httpx
from bs4 import BeautifulSoup
from lxml import etree
import re
from base64 import b64decode
from Crypto.Cipher import AES
import json
from colorama import init, Fore

from utils_Qt.log import logger

import logging
logger = logging.getLogger(__name__)


# Inicializar colorama
init(autoreset=True)

def success(message: str):
    print(Fore.GREEN + '[+] ' + message)

def warning(message: str):
    print(Fore.YELLOW + '\n[!] ' + message)

def error(message: str):
    print(Fore.RED + '[-] ' + message)

def decryption_engine(url: str) -> dict:
    """
    Parsea la página de entrada y devuelve un diccionario de servidores disponibles.
    :param url: URL de la página a procesar
    :return: dict con forma {{ 'Servidor 1': url1, 'Servidor 2': url2, ... }}
    """
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        root = etree.HTML(response.content)

        # Buscar bloques onclick de jugadores
        players = root.xpath('.//div[@class="OptionsLangDisp"]//li[@onclick]')
        servers = {}

        if players:
            for idx, item in enumerate(players, start=1):
                onclick = item.get('onclick', '')
                match = re.search(r"go_to_playerVast\('([^']+)'", onclick)
                if match:
                    link = match.group(1)
                    if 'https://' in link.split('=')[-1] and len(link) < 50:
                        name = f"Servidor {idx}"
                        servers[name] = link
                        logger.info("[+] recopilando servidor :{} -> {}".format(idx,link))
                        # success(f"{name}: {link}")
        else:
            # Si no hay <li> con onclick, intentar decifrar con fuzzing
            logger.info('[-] No se encontraron servidores en OptionsLangDisp, intentando fuzzing...')
            servers = fuzzing(response.text)

        return servers

    except Exception as e:
        error(f"Error en engine: {e}")
        return {}

def fuzzing(html_content: str) -> dict:
    """
    Decifra enlaces encriptados de video y devuelve un dict de servidores.
    """
    servers = {}
    key_match = re.search(r"decryptLink\([^,]+,\s*['\"]([^'\"]+)", html_content)
    data_match = re.search(r"(?:const|let|var)\s+dataLink\s*=\s*(\[.*?\]);", html_content, re.DOTALL)

    if not key_match or not data_match:
        error("No se encontró la clave o los datos encriptados")
        return servers

    key = key_match.group(1)
    data_json = data_match.group(1).replace('\\/', '/')

    try:
        embeds = json.loads(data_json)[0].get('sortedEmbeds', [])
    except json.JSONDecodeError as e:
        error(f"Error al parsear JSON: {e}")
        return servers

    for idx, entry in enumerate(embeds, start=1):
        encrypted = entry.get('link')
        decrypted_url = decrypt_link(encrypted, key)
        if decrypted_url:
            name = f"Servidor {idx}"
            servers[name] = decrypted_url
            logger.info("[+] recopilando servidor incriptado :{} -> {}".format(idx,decrypted_url))
            # success(f"{name}: {decrypted_url}")

    return servers

def decrypt_link(encrypted: str, key: str) -> str:
    """
    Desencripta un enlace con AES-CBC.
    """
    try:
        raw = b64decode(encrypted)
        iv = raw[:16]
        ciphertext = raw[16:]
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        pad_len = decrypted[-1]
        return decrypted[:-pad_len].decode('utf-8')
    except Exception as e:
        error(f"Error al desencriptar: {e}")
        return ""

def check_site_status(url: str) -> str:
    """
    Verifica el estado del sitio y detecta errores comunes.
    """
    try:
        from requests import get
        resp = get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Detectar errores 404 o títulos "Not Found"
        if soup.find('title', string=re.compile('Not Found', re.IGNORECASE)):
            return "Error detectado en el contenido HTML"
        return "El sitio funciona correctamente"
    
    except Exception as e:
        return f"Error de conexión: {e}"
