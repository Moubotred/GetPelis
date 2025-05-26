# streaming.py

import subprocess
import requests
import tempfile
import logging
import os
import re

from utils_Qt.log import logger
import logging
logger = logging.getLogger(__name__)

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

# --- Parsear el m3u8 y obteber duracion ---
def get_total_duration(url_m3u8):
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

def build_ffmpeg_command(m3u8_url):
    return [
        "ffmpeg",
        "-threads", "1",  # Limita uso de CPU
        "-i", m3u8_url,
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

# # --- Configuracion ffmpeg para conversion
# def build_ffmpeg_command(m3u8_url):
#     return [
#         "ffmpeg",
#         "-i", m3u8_url,
#         "-c:v", "libx264",
#         "-c:a", "aac",
#         "-bsf:a", "aac_adtstoasc",
#         "-movflags", "frag_keyframe+empty_moov",
#         "-f", "mp4",
#         "-loglevel", "error",
#         "-"
#     ]

