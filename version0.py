from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from constants import WEBSITE, BARRA_DE_BUSQUEDA, SERIES,SERVIDORES
from lxml import html
import time


class Hilos_De_Busqueda:
	def __init__(self):
		self.driver = None
		self.Peticion = None
		self.codigo_fuente = None
		pass
        
	def PELISPLUSHD_TO(self):
		Variables = BARRA_DE_BUSQUEDA()
		BB = Variables.PELISPLUSHD_TO_BARRA
		TB = Variables.PELISPLUSHD_TO_TEXTO
		LT = Variables.PELISPLUSHD_TO_Lista
		# ----->* Iniciar Barra De Busqueda 
		Busqueda_To = self.driver.find_element(By.XPATH,BB)
		Busqueda_To.click()
		time.sleep(4)
		# ----->* Enviar La Búsqueda 
		Iniciar_To = self.driver.find_element(By.XPATH,TB)
		Iniciar_To.send_keys(self.Peticion)
		Iniciar_To.send_keys(Keys.RETURN)
		time.sleep(4)        
		# ----->* Lista De Búsqueda
		self.codigo_fuente = self.driver.page_source
		Lista_Busqueda = html.fromstring(self.codigo_fuente)
		Enlace = Lista_Busqueda.xpath(LT)
		Longitud_De_Enlace = len(Enlace)        
		Construccion_Enlace = [WEBSITE.PELISPLUSHD_TO+Enlace[n] for n in range(Longitud_De_Enlace)]
		# ----->* Separacion De Enlaces Para Buscar El Nombre De La Serie
		Nombre_Serie = [Construccion_Enlace[n].split('/')[5]for n in range(Longitud_De_Enlace)]
		Temporada_Episodio = SERIES(Nombre_Serie[0],'1','5	')
		self.driver.get(WEBSITE.PELISPLUSHD_TO+Temporada_Episodio.PELISPLUSHD_TO_SERIE)
		#Servidor = SERVIDORES('SBFast')
		#print(Servidor.PELISPLUSHD_TO_BUSQUEDA_SERVIDORES)        
		# -----> Buscar La URL original Del Video En Los Servidores
		for servidor in SERVIDORES.PELISPLUSHD_TO_SERVIDORES:
			try:
				time.sleep(4)
				Servidores = self.driver.find_element(By.XPATH, f"//ul[@class='TbVideoNv nav nav-tabs']/li/a[text()='{servidor}']")
				Servidores.click()    
				time.sleep(4)
				Buscando_Url = html.fromstring(self.driver.page_source)
				Url_Original = Buscando_Url.xpath("//div[@class='video']/div/iframe/@src")[0]
				print('Scrapeo Exitoso Url De Video:',Url_Original )
			except NoSuchElementException:
				print(f"SERVIDOR NO ECONTRADO EN EL SITIO | EL SERVIOR QU  {servidor}")
				break                
			except KeyboardInterrupt:
				print('Interrupcion de teclado')
				break
         # la hacer la peticion web y dar play me da un
         # error y el m3u8 da error de status pero si vuelo
         # a recraga con F5 me carga
         # los enlaces de m3u8
        
	def CUEVANA3_CH(self):
        time.sleep(4)
        Variables = BARRA_DE_BUSQUEDA()
        BB = Variables.CUEVANA_NU_BARRA
        TB = Variables.CUEVANA_NU_TEXTO
        # ----->* Iniciar Barra De Busqueda 
        Busqueda_To = self.driver.find_element(By.XPATH,BB)
        Busqueda_To.click()
        time.sleep(4)
		# ----->* Enviar La Búsqueda 
        Iniciar_To = self.driver.find_element(By.ID,TB)
        Iniciar_To.send_keys(self.Peticion)
        Iniciar_To.send_keys(Keys.RETURN)
        time.sleep(4)
        
    def CUEVANA_NU(self):
		time.sleep(4)
		Variables = BARRA_DE_BUSQUEDA()
		BB = Variables.CUEVANA_NU_BARRA
		TB = Variables.CUEVANA_NU_TEXTO
		# ----->* Iniciar Barra De Busqueda 
		Busqueda_To = self.driver.find_element(By.XPATH,BB)
		Busqueda_To.click()
		time.sleep(4)
		# ----->* Enviar La Búsqueda 
		Iniciar_To = self.driver.find_element(By.ID,TB)
		Iniciar_To.send_keys(self.Peticion)
		Iniciar_To.send_keys(Keys.RETURN)
		time.sleep(4)
		pass
	
    def PELISPOP_LAT(self):
		time.sleep(4)
		Variables = BARRA_DE_BUSQUEDA()
		BB = Variables.PELISPOP_LAT_BARRA
		TB = Variables.PELISPOP_LAT_TEXTO
		# ----->* Iniciar Barra De Busqueda 
		Busqueda_To = self.driver.find_element(By.XPATH,'//div[@class="ep-autosuggest-container"]')
		Busqueda_To.click()
		time.sleep(4)
		# ----->* Enviar La Búsqueda 
		Iniciar_To = self.driver.find_element(By.ID,'s')
		Iniciar_To.send_keys(self.Peticion)
		Iniciar_To.send_keys(Keys.RETURN)
		time.sleep(4)
		pass
        
	def main(self):
        options = Options()
        # options.add_argument('--headless')
        options.add_argument("--profile")
        options.add_argument(r'/home/user/.mozilla/firefox/2sqo50t4.Default User')
        self.driver = webdriver.Firefox(options=options)
        self.Peticion = 'silicon'
        websites = [PELISPLUSHD_TO,CUEVANA3_CH,CUEVANA_NU,PELISPOP_LAT]
        for web in websites:
            self.driver.get(WEBSITE.web+self.peticion)# modificar CUEVANA3_CH por el sitio web
            hilo1 = threading.Thread(target=CUEVANA3_CH)
            hilo2 = threading.Thread(target=CUEVANA_NU)
            hilo1.start()
            hilo2.start()
		    pass
	
run = Hilos_De_Busqueda()
run.main()






