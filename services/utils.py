
import httpx
from lxml import etree
from typing import Dict, Optional
from colorama import Fore
from urllib.parse import urlencode, urlparse, urlunparse, ParseResult
# from utils_Qt.log import logger


import logging
logger = logging.getLogger(__name__)


XUPA_ERR = "Esta fuente de video o enlace tiene un error y no esta disponible"
EMBED_ERR = "No folders found"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/91.0.4472.124 Safari/537.36"


# --------------------SECCION PARA VER LOS RESULTADOS DE LOS SERVICIOS DE STREAM -------------------------->

def build_urls(imdb_id: str, season: Optional[int] = None, episode: Optional[int] = None) -> Dict[str, str]:
    logger.info(f"[+] Construyendo URLs para imdb_id='{imdb_id}', season='{season}', episode='{episode}'")
    if season is not None and episode is not None:
        eps = f'x{episode}' if episode >= 10 else f'x0{episode}'
        suffix = f"{imdb_id}-{season}{eps}"
        urls = {
            'xupalace': f"https://xupalace.org/video/{suffix}/",
            'embed': f"https://embed69.org/f/{suffix}"
        }
        logger.info(f"[+] URLs generadas para episodio: {urls}")
        return urls
    

    urls = {
        'xupalace': f"https://xupalace.org/video/{imdb_id}",
        'embed': f"https://embed69.org/f/{imdb_id}"
            }
    logger.info(f"[+] URLs generadas para película: {urls}")
    return urls

async def validate_xupalace(url: str) -> bool:
    # logger.info(f"[+] Validando URL de Xupalace: {url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            is_valid = XUPA_ERR not in resp.text
            # logger.info(f"[+] Validación de Xupalace: {'OK' if is_valid else 'FALLA'} - {url}")
            return is_valid
    except Exception as e:
        logger.exception(f"Error validando Xupalace: {e}")
        return False

async def validate_embed(url: str) -> bool:
    logger.info(f"[+] Validando URL de Embed: {url}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            is_valid = EMBED_ERR not in resp.text
            logger.info(f"[-] Validación de Embed: {'OK' if is_valid else 'FALLA'} - {url}")
            return is_valid
    except Exception as e:
        logger.exception(f"Error validando Embed: {e}")
        return False

async def build_options_animetv(title:str = None):
    
    try:
        _root_tree_ = await fetch_search_results(
            query = title,
            lang  = None,
            base_url = "https://www3.animeflv.net/browse",
            q_param_name = "q"
        )

        options = build_options_dict(
            root        = _root_tree_,
            item_xpath  = './/div/main/ul/li',
            title_xpath = './/article/div/div/strong/text()',
            href_xpath  = './/a/@href',
            id_prefix   = None,   # <— desactiva el filtro de IMDb
            domain      = "https://www3.animeflv.net",
            reconfig    = True    # para ver el volcado de títulos→hrefs
        )

        return options
        
    except Exception as e:
        logger.exception(f"Error validando Embed: {e}")
        return False

SERVICE_VALIDATORS = {
    "xupalace": validate_xupalace,
    "embed":    validate_embed,
    "animetv": ''
}

# ------------------ FUNCIÓN AUXILIAR GENÉRICA ------------------

async def validate_sources(
    urls: Dict[str, str],
    *args,
    **kwargs
) -> Optional[str]:
    """
    Recorre SERVICE_VALIDATORS y llama al validador correspondiente
    para cada URL en el dict `urls`. Devuelve el nombre del primer
    servicio válido, o None si ninguno lo es.

    Args:
        urls: Dict de la forma {servicio: url}.
        *args: Parámetros posicionales para pasar a cada validador.
        **kwargs: Parámetros clave-valor (p.ej. timeout, headers).
    """
    for service_name, validate_func in SERVICE_VALIDATORS.items():
        url = urls.get(service_name)
        if not url:
            continue
        logger.info(f"[+] Probando {service_name} -> {url}")
        try:
            if await validate_func(url, *args, **kwargs):
                logger.info(f"[✓] Fuente válida: {service_name}")
                return service_name
            
        except Exception as e:
            logger.warning(f"[!] Excepción en {service_name}: {e}")
    logger.info("[-] Ninguna fuente válida encontrada.")
    
    return None


# <--------------------------------------SECCION DE BUSQUEDA DE IMDB---------------------------------------->


def _config_build_url(base_url: str, params: dict = None) -> str:
    """
    Construye una URL completa a partir de una base y un diccionario de parámetros.

    Args:
        base_url (str): URL base como 'https://example.com/path'
        params (dict): Diccionario opcional de parámetros query (?key=value)

    Returns:
        str: URL final construida con parámetros codificados
    """
    logger.info(f"[+] Construyendo URL: base='{base_url}', params={params}")
    
    if not params:
        return base_url

    url_parts = list(urlparse(base_url))
    query_string = urlencode(params)
    url_parts[4] = query_string  # index 4 = 'query' en ParseResult

    return urlunparse(ParseResult(*url_parts))


def _Build_service_url(query: str, lang: str = 'es', base_url: str = '', q_param_name: str = 'q', **extra_params) -> str:
    """
    Construye una URL para cualquier servicio usando una query principal y parámetros adicionales.

    Args:
        query (str): Término de búsqueda o ID principal.
        lang (str): Idioma opcional (default 'es').
        base_url (str): URL base del servicio.
        q_param_name (str): Nombre del parámetro de búsqueda principal (default 'q').
        **extra_params: Otros parámetros opcionales.

    Returns:
        str: URL completa lista para usarse.
    """
    logger.info(f"[+] Construyendo URL de servicio para query='{query}', lang='{lang}', extras={extra_params}")
    
    params = {q_param_name: query}
    if lang:
        params['lang'] = lang
    params.update(extra_params)

    return _config_build_url(base_url, params)


def build_options_dict(
    root: etree._Element,
    item_xpath: str = '//ul/li',
    title_xpath: str = './/a/text()',
    href_xpath: str = './/a/@href',
    id_prefix: Optional[str] = '/es/title/tt',
    domain: Optional[str] = None,
    reconfig:bool = False,
) -> Dict[int, Dict[str, str]]:
    logger.info("[+] Procesando árbol XML para construir opciones de resultados")


    items = root.xpath(item_xpath)
    options = {}
    idx = 1

    for item in items:
        title_nodes = item.xpath(title_xpath)
        href_nodes = item.xpath(href_xpath)

        """<---session de agregar xpath para testear--->"""
        type_content = list(item.xpath('.//ul/li/span/text()'))
        """<------------------------------------------->"""
        
        # Dump de debug si reconfig==True    
        if reconfig:
            count = min(len(title_nodes), len(href_nodes))
            for n in range(count):
                title = title_nodes[n].strip()
                href  = href_nodes[n].strip()
                tipo_etiqueta = 'serie' if '/anime/' in href else 'pelicula'
                options[idx] = {
                    'title': title,
                    'url':   (domain + href) if domain else href,
                    'type':  tipo_etiqueta
                }
                idx += 1

            # return options
        

        if not title_nodes or not href_nodes or not type_content:
            continue


        tipo_principal = type_content[0].strip()
        tipo_secundario = type_content[1].strip() if len(type_content) > 1 else ''

        # Clasificación de contenido
        
        # Convertimos a minúsculas para hacer comparaciones insensibles a mayúsculas/minúsculas
        tipo_secundario_lower = tipo_secundario.lower()
        

        # Evaluamos si el contenido es una serie:
        # - Contiene explícitamente "serie de tv" o "miniserie de tv"
        # - O el campo principal (tipo_principal) tiene un guion largo, indicando un rango de años (ej: "1996–2003"), típico de series
        es_serie = (
            'serie de tv' in tipo_secundario_lower 
            or 'miniserie de tv' in tipo_secundario_lower 
            or '–' in tipo_principal
        )

        # Evaluamos si el contenido es una película:
        # - tipo_principal es un número de 4 dígitos (un año)
        # - No contiene palabras que indiquen que es un tipo de contenido que NO nos interesa (ej: 'cortometraje', 'video', 'episodio', 'documental')
        # - Y además no debe haberse identificado como serie (para evitar falsos positivos)
        es_pelicula = (
            tipo_principal.isdigit() 
            and len(tipo_principal) == 4 
            and all(termino not in tipo_secundario_lower 
                    for termino in ['cortometraje', 'video', 'episodio', 'documental']) 
            and not es_serie
        )

        # Si el contenido no es ni serie ni película, lo descartamos
        if not (es_pelicula or es_serie):
            continue

        title = title_nodes[0].strip()
        href = href_nodes[0].strip()

        # Etiquetamos el tipo de contenido
        tipo_contenido = 'serie' if es_serie else 'pelicula'


        # Si id_prefix está definido, asumimos que buscamos un ID (tipo IMDb)
        if id_prefix and id_prefix in href:
            parts = href.split('/')
            imdb_id = next((p for p in parts if p.startswith("tt")), None)

            if imdb_id:
                options[idx] = {
                    'title': title,
                    'id': imdb_id,
                    'url': (domain + href) if domain else href,
                    'type':'{}'.format(tipo_contenido)
                }
                idx += 1

        # Si no hay id_prefix, simplemente agregamos el título y el href
        elif not id_prefix:
            options[idx] = {
                'title': title,
                'url': (domain + href) if domain else href
            }
            idx += 1

    logger.info(f"[+] Total de resultados válidos encontrados: {len(options)}")
    return options


async def fetch_search_results(
    query: str = None,
    lang: str = 'es',
    base_url: str = "https://www.imdb.com/es/find/",
    q_param_name: str = 'q',
    **extra_params
) -> etree._Element:
    """
    Realiza una búsqueda usando una URL base configurable.

    Args:
        query (str): Término de búsqueda.
        lang (str): Idioma opcional.
        base_url (str): URL del servicio (por defecto IMDB).
        q_param_name (str): Clave del parámetro de búsqueda (por defecto 'q').
        **extra_params: Otros parámetros extra opcionales.

    Returns:
        etree._Element: Árbol HTML de la respuesta.
    """
    url = _Build_service_url(
        query=query,
        lang=lang,
        base_url=base_url,
        q_param_name=q_param_name,
        **extra_params
    )

    headers = {'User-Agent': USER_AGENT}
    logger.info(f"[+] Realizando solicitud GET a: {url}")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, follow_redirects=True)
            resp.raise_for_status()
            parser = etree.HTMLParser()
            logger.info("[+] Respuesta recibida correctamente")

            # print(resp.content)

            return etree.fromstring(resp.content, parser)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"[✗] Error HTTP: {e}")
        raise

    except Exception as e:
        logger.exception(f"[✗] Error inesperado: {e}")
        raise
