from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from constants import WEBSITE,BARRA_DE_BUSQUEDA,SERIES,SERVIDORES,PELICULAS
from lxml import html
import threading
import time

class Hilos_De_Busqueda:
	def __init__(self):
		self.driver = None
		self.Peticion = 'the flash'
		self.codigo_fuente = None
		
	def CUEVANA3_CH(self):
		time.sleep(4)
		Variables = BARRA_DE_BUSQUEDA()
		BB = Variables.CUEVANA3_CH_BARRA
		TB = Variables.CUEVANA3_CH_TEXTO
		# ----->* Iniciar Barra De Busqueda 
		Busqueda_To = self.driver.find_element(By.XPATH,'//div[@class="ep-autosuggest-container"]')
		Busqueda_To.click()
		time.sleep(4)
		# ----->* Enviar La Búsqueda 
		Iniciar_To = self.driver.find_element(By.ID,'keysss')
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
		self.driver.get(WEBSITE.CUEVANA3_CH)
		self.Peticion = 'silicon'
		self.CUEVANA3_CH()
		pass
		 
if __name__=='__main__':
	App = Hilos_De_Busqueda()
	App.main()
	
	

		 
