# app/controller/main_controller.py

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QListWidget, QPushButton
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, Qt
from qasync import asyncSlot
import asyncio

from controller.video_controller import VideoManager
from view.dlnastream import DlnaStreamDialog
from view.urlselection import UrlSelectionDialog

from services.utils import fetch_search_results, build_options_dict, build_urls, validate_xupalace, validate_sources, build_options_animetv
from services.services_engine import decryption_engine
from utils_Qt.log import logger

import logging
logger = logging.getLogger(__name__)


class MainController(QObject):
    playRequested = pyqtSignal(str)  # Señal para solicitar reproducción

    def __init__(self, view):
        super().__init__()
        self.view = view

        # Estado actual
        self.title_in_another_service = None
        self.video_manager = VideoManager(self.view)
        self.current_selection = None
        self.smart_tv_or_devices = None
        self.current_stream_url = None
        self.dlna_dialog = None

        # Conectar señales de la UI con métodos del controlador
        self.view.search_btn.clicked.connect(self.on_search_clicked)
        self.view.results_list.itemClicked.connect(self.on_result_selected)
        self.view.series_check.stateChanged.connect(self.toggle_series_options)
        self.view.validate_btn.clicked.connect(self.on_validate_clicked)
        self.view.play_btn.clicked.connect(self.initiate_stream_playback)        
        self.view.transmit_btn.clicked.connect(self.on_transmit_search)


    def toggle_eval_automatic_or_externas(self):
        """(No implementada) Cambiar entre validación automática o manual."""
        self.view.external_services.setChecked(True)
        self.view.auto_services.setChecked(False)

    def toggle_series_options(self, state):
        """Muestra u oculta las opciones si se trata de una serie."""
        logger.info('[+] toggle_series_options - alternando opciones de series')
        self.view.show_series_options(state == Qt.Checked)

    def on_result_selected(self, item):
        """Acciones al seleccionar un resultado de búsqueda."""
        logger.info('[+] on_result_selected - seleccionando resultado de búsqueda')
        text = item.text()
        idx = int(text.split(".")[0])
        self.current_selection = self.view.title_results[idx]
        info = self.view.title_results.get(idx)

        if not info:
            return

        # Detectar si es una serie y activar opciones correspondientes
        if info.get('type') == 'serie':
            self.view.series_check.setChecked(True)
            self.toggle_series_options(Qt.Checked)
        else:
            self.view.series_check.setChecked(False)
            self.toggle_series_options(Qt.Unchecked)
            self.view.series_group.setVisible(False)

        self.view.play_btn.setEnabled(True)
        self.view.clear_servers()
        self.view.validate_btn.setEnabled(True)

    def on_transmit_search(self, url=None):
        """Transmite el video seleccionado usando DLNA."""
        logger.info('[+] Iniciando transmisión DLNA')
        selected = self.view.servers_list.currentItem()
        if not selected:
            QMessageBox.warning(self.view, "Error", "Selecciona un servidor")
            return

        server_name = selected.text().split(":")[0]
        server_url = self.view.servers.get(server_name)

        if not server_url:
            return

        # Reutilizar la instancia
        if self.dlna_dialog is None:
            self.dlna_dialog = DlnaStreamDialog(url_server=server_url, parent=self.view)
        else:
            # actualizar sólo la URL base si cambió
            self.dlna_dialog.url_plantilla = server_url

        # Mostrar el diálogo (no destruirlo al cerrar)
        self.dlna_dialog.show()
        self.dlna_dialog.raise_()
        self.dlna_dialog.activateWindow()

        # dlna = DlnaStreamDialog(url_server=server_url,parent=self.view)
        # dlna.exec_()

    def initiate_stream_playback(self):
        """Inicia la reproducción del video en VLC."""
        logger.info('[+] initiate_stream_playback - iniciando reproducción de stream via VLC')
        selected = self.view.servers_list.currentItem()
        if not selected:
            QMessageBox.warning(self.view, "Error", "Selecciona un servidor")
            return

        server_name = selected.text().split(":")[0]
        server_url = self.view.servers.get(server_name)

        if not server_url:
            QMessageBox.critical(self.view, "Error", "URL inválida")
            return

        self.video_manager.play_stream(server_url, connect_play_request=True)
        self.view.status_bar.setText("Obteniendo Stream")

    @asyncSlot()
    async def on_search_clicked(self):
        """Realiza la búsqueda de títulos a partir del texto ingresado por el usuario."""
        logger.info('[+] on_search_clicked - ejecutando búsqueda')
        self.view.transmit_btn.setEnabled(False)

        query = self.view.get_search_text().strip()

        if not query:
            QMessageBox.warning(self.view, "Error", "¡La consulta de búsqueda no puede estar vacía!")
            return

        self.view.status_bar.setText("Búsqueda...")
        self.view.results_list.clear()

        try:
            root = await fetch_search_results(query)
            options = build_options_dict(root)
            self.view.title_results = options

            if not options:
                QMessageBox.information(self.view, "No Resultados", "No se encontraron resultados.")
                return

            self.view.clear_results()
            for idx, info in options.items():
                self.view.add_search_result(f"{idx}. {info['title']}")
            self.view.status_bar.setText("Búsqueda completada")

        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Búsqueda fallida: {str(e)}")
            self.view.status_bar.setText("Búsqueda fallida")

    @asyncSlot()
    async def on_validate_clicked(self):
        """Valida los servidores para el título seleccionado."""
        logger.info('[+] on_validate_clicked - clic en validar')
        if self.current_selection is None:
            QMessageBox.warning(self.view, "Error", "Por favor selecciona un título primero.")
            return

        self.view.transmit_btn.setEnabled(True)
        await self.validate_servers()

    @asyncSlot()
    async def validate_servers(self):
        """Valida los servidores para streaming según el título seleccionado."""
        logger.info('[+] validate_servers - validando servidores')
        is_series = self.view.series_check.isChecked()

        # Obtiene la temporada y episodio si es una serie
        season = self.view.season_spin.value() if is_series else None
        episode = self.view.episode_spin.value() if is_series else None

        urls = build_urls(self.current_selection['id'], season, episode)
        logger.info(f"[+] URLs generadas: {urls}")

        try:
            # Validación automática de servicios si está seleccionado
            if self.view.auto_services.isChecked():
                valid_service = await validate_sources(urls)
                if not valid_service:
                    QMessageBox.warning(self.view, "Sin fuentes", "No se encontró ninguna fuente válida.")
                    return
                parsed_servers = decryption_engine(urls[valid_service])
            else:
                # Validación manual mediante diálogo
                dialog = UrlSelectionDialog(urls=urls.keys(), parent=self.view)
                if dialog.exec_() != QDialog.Accepted or not dialog.selected_url:
                    QMessageBox.warning(self.view, "Advertencia", "¡Debes seleccionar un servicio!")
                    return
                parsed_servers = decryption_engine(urls[dialog.selected_url])

        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"Engine failed: {str(e)}")
            return

        # Limpia lista y prepara para nuevos servidores
        self.view.servers.clear()
        self.view.servers_list.clear()
        self.view.status_bar.setText("Validando servidores...")

        validation_tasks = []
        name_url_pairs = []

        try:
            for name, url in parsed_servers.items():
                validation_tasks.append(validate_xupalace(url))
                name_url_pairs.append((name, url))

            results = await asyncio.gather(*validation_tasks)

            available_servers = []
            for (name, url), is_valid in zip(name_url_pairs, results):
                if is_valid:
                    display_text = f"{name}: {url}"
                    available_servers.append(display_text)
                    self.view.servers[name] = url

            if available_servers:
                self.view.servers_list.addItems(available_servers)
                self.view.play_btn.setEnabled(True)
                self.view.status_bar.setText(f"Se encontraron {len(available_servers)} servidores disponibles")
            else:
                QMessageBox.warning(self.view, "Servidores", "¡No hay servidores disponibles!")
                self.view.status_bar.setText("Sin servidores disponibles")

        except Exception as e:
            QMessageBox.warning(self.view, "Advertencia", "¡Debes seleccionar un servicio!")
