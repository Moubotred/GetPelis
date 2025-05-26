from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import re

from utils_Qt.log import logger
import os
import sys
import time
# import logging

# logger = logging.getLogger(__name__)

import logging
logger = logging.getLogger(__name__)


class M3U8Worker(QObject):

    # m3u8_procesar = pyqtSignal(str)

    m3u8_ready = pyqtSignal(str)

    error_occurred = pyqtSignal(str)

    finished = pyqtSignal()

    def __init__(self, target_url):
        logger.info('[+] M3U8Worker::__init__ - Inicializando worker con URL objetivo')
        super().__init__()
        self.target_url = target_url

    def get_geckodriver_path(self):
        # Si estoy dentro de un EXE de PyInstaller
        if getattr(sys, "_MEIPASS", False):
            return os.path.join(sys._MEIPASS, "geckodriver.exe")
        # Si estoy en desarrollo, la copia está en third_party/
        return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            os.pardir,
                                            "third_party",
                                            "geckodriver.exe"))
    def get_firefox_portable(self):
        if getattr(sys, "_MEIPASS", False):
            return os.path.join(sys._MEIPASS, "FirefoxPortable", "App","Firefox64","firefox.exe")
        return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            os.pardir,
                                            "third_party",
                                            "FirefoxPortable",
                                            "App",
                                            "Firefox64",
                                            "firefox.exe",
                                            ))

    @pyqtSlot()
    def process(self):

        # 2) Configuro las opciones de Firefox:
        from selenium.webdriver.firefox.options import Options
        # firefox_options = Options()
        # firefox_options.binary_location = self.get_firefox_portable()
        # firefox_options.add_argument("--headless")

        # 3) Configuro el Service para usar mi geckodriver
        from selenium.webdriver.firefox.service import Service
        # service = Service(executable_path=self.get_geckodriver_path())

        # 4) Arranco el navegador PASÁNDOLE service **y** options
        from seleniumwire import webdriver
        # driver = webdriver.Firefox(service=service, options=firefox_options)
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.wait import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException

        # firefox_options = Options()
        
        # # Aceptar certificados inseguros
        # firefox_options.set_capability("acceptInsecureCerts", True)

        # firefox_options.set_preference("security.tls.version.min", 3)  # 3=TLS 1.2
        # firefox_options.set_preference("security.tls.version.max", 4)  # 4=TLS 1.3
        # firefox_options.set_preference("security.enterprise_roots.enabled", True)

        # firefox_options.add_argument("--headless")

        options = Options()
        options.add_argument("--headless")
        options.set_capability("acceptInsecureCerts", True)

        # logger.info('[+] M3U8Worker::process - Lanzando Firefox en modo headless')
        logger.info('[+] M3U8Worker::process - Iniciando procesamiento para buscar M3U8')

        driver = webdriver.Firefox(options=options)

        logger.info('[+] Lanzando Firefox Portable headless')

        wait = WebDriverWait(driver,20)

        m3u8_url = None

        try:
            logger.info(f'[+] M3U8Worker::process - Accediendo a la URL: {self.target_url}')
            
            driver.get(self.target_url)

            # > condicion para evalur servidores que no cargan el m3u8 antes de tiempo 
            # > y realizar el click esperar un tiempo hasta que carge el m3u8 y poder 
            # > intercetar ese trafico

            # <========================================================================================>
            try:
                server_redirect_voe = bool(re.findall(r'\bv\w+',self.target_url,re.IGNORECASE))
                if server_redirect_voe:
                    logger.info('[+] detectadondo servidor Voe')
                    wait.until(EC.presence_of_element_located((By.XPATH,'.//div[@class="spin"]'))).click()
                    logger.info('[+] deteccion de M3U8 exitosa')
                    time.sleep(4)

            except (Exception,TimeoutException) as e:
                logger.error('[-] No se encontro elemento o servidor caido redirigido : {}'.format(driver.current_url))
            # <========================================================================================>
                
                
            m3u8_pattern = re.compile(r'.*index.*\.m3u8')
            for request in driver.requests:
                if request.response and 'Content-Type' in request.response.headers:
                    content_type = request.response.headers['Content-Type']
                    if 'application/vnd.apple.mpegurl' in content_type or 'application/x-mpegURL' in content_type:
                        if re.match(m3u8_pattern, request.url):
                            m3u8_url = request.url
                            logger.info(f'[+] M3U8Worker::process - URL M3U8 encontrada: {m3u8_url}')
                            break

        except Exception as e:
            logger.error(f'[!] M3U8Worker::process - Error durante la navegación: {e}')
            self.error_occurred.emit(str(e))
            self.finished.emit()
            return

        finally:
            driver.quit()
            logger.info('[+] M3U8Worker::process - Navegador cerrado')
            logger.info('[+] M3U8Worker::process - Emisión de señal m3u8_ready')
            # self.m3u8_procesar.emit(m3u8_url if m3u8_url else "")
            self.m3u8_ready.emit(m3u8_url if m3u8_url else "")
            logger.info('[+] M3U8Worker::process - Emisión de señal finished')
            self.finished.emit()

    def _fetch_m3u8(self):
        logger.info('[+] M3U8Worker::_fetch_m3u8 - Retornando URL m3u8 (dummy)')
        return self.target_url  # Esto es solo un ejemplo o placeholder