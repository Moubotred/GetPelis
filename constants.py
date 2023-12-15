
class WEBSITE:
	# SITIOS WEB DE SCRAPING
	
	# pelisplushd.to
	PELISPLUSHD_TO = 'https://www16.pelisplushd.to/'
	# cuevana3.ch
	CUEVANA3_CH = 'https://www12.cuevana3.ch/'
    # cuevana3.nu
	CUEVANA_NU = 'https://cuevana3.nu/'
	# pelispop.lat
	PELISPOP_LAT = 'https://pelispop.lat/'
	pass

class SERVIDORES:
	 # LISTA DE SERVIDORES
	      
     PELISPLUSHD_TO_SERVIDORES = ['SBFast','VIP','Upfast','DoodStream','Mobile','PLUSTO VIP','Uqload','filemoon','voesx','streamwish','doodstream','streamtape','netu','filelions']
     SERVIDORES_TO_XPATH = "//ul[@class='TbVideoNv nav nav-tabs']/li/a[text()='Uqload']"
		
     CUEVANA3_CH_SERVIDORES = ['1 - Latino - HD','2 - Latino - Filelions','3 - Latino - Streamwish','4 - Latino - Doodstream']

     
     CUEVANA3_NU_SERVIDORES = ['1 - gdplayer','2 - gdplayer','3 - gdplayer','4 - fembed','5 - fembed','6 - gdplayer','7 - gdplayer']
     PELISPOP_LAT_SERVIDORES = ['PLUSVIP','filemoon','streamwish','dood','waaw','Stream HD','uptobox','1fichier']
     pass
	 
class BARRA_DE_BUSQUEDA:
	# BARRA DE BUSQUEDA EN DIFERENTES WEBS
    def __init__(self):	#servidor
        # pelisplushd.to
        #self.servidor = None
        self.PELISPLUSHD_TO_BARRA = '//a[@class="search-toggle"]'
        self.PELISPLUSHD_TO_TEXTO = "//li[contains(@class, 'search-input') and contains(@class, 'active')]//input[contains(@class, 'form-control')]"
        self.PELISPLUSHD_TO_Lista = '//a[@class="Posters-link"]/@href'
        #self.PELISPLUSHD_TO_BUSQUEDA_SERVIDORES = f"//ul[@class='TbVideoNv nav nav-tabs']/li/a[text()='{self.servidor}']"
    
        #time.sleep(5)
        #root = html.fromstring(search.page_source)
        #img = root.xpath('//a[@class="Posters-link"]/@href')	
        #name = root.xpath('//a/div[@class="listing-content"]/p/text()')
	
	    # cuevana3.ch
        self.CUEVANA3_CH_BARRA = '//div[@class="ep-autosuggest-container"]'#By.XPATH
        self.CUEVANA3_CH_TEXTO = 'keysss'#By.ID
        #time.sleep(5)
        #root = html.fromstring(search.page_source)
        #img = root.xpath('//li[@class="xxx TPostMv"]/div/a/@href')
        #name = root.xpath('//h2[@class="Title"]/text()')

        # cuevana3.nu
        self.CUEVANA_NU_BARRA = '//form[@id="searchform"]'
        self.CUEVANA_NU_TEXTO = 'keysss'#By.ID
        #time.sleep(5)
        #root = html.fromstring(search.page_source)
        #nombre_de_serie = root.xpath('//div[@class="TPost C post-7544 post type-post status-publish format-standard has-post-thumbnail hentry"]/a/@href')
        #total_de_enlaces = len(nombre_de_serie)-1
        #for x in range(total_de_enlaces):
        #    iteracion = nombre_de_serie[x].split('/')
        #    print(WEBSITE.CUEVANA3_CH+iteracion[1]+'/'+iteracion[2])
		
	    # pelispop.lat
        self.PELISPOP_LAT_BARRA = '//form[@id="searchform"]'
        self.PELISPOP_LAT_TEXTO = 's'#By.ID
        #root = html.fromstring(search.page_source)
        #name = root.xpath('//div[@class="result-item"]/article/div[@class="details"]/div/a/@href')
        pass

class SERIES:#,SERIE,TEMP,EPI
    def __init__(self,SERIE,TEMP,EPI):
        self.SERIE = SERIE
        self.TEMP = TEMP
        self.EPI = EPI
        
        #<---------------------------------------------------------------------------------------->
        self.PELISPLUSHD_TO_SERIE = f'serie/{self.SERIE}/temporada/{self.TEMP}/capitulo/{self.EPI}'
        self.CUEVANA3_CH_TO_SERIE = f'episodio/{self.SERIE}-{self.TEMP}x{self.EPI}' 
        self.CUEVANA_NU_TO_SERIE = f'ver-el-episodio/episodio-{self.EPI}-de-{self.SERIE}-temporada-{self.TEMP}/'
        self.PELISPOP_LAT_TO_SERIE = f'episodios/{self.SERIE}-{self.TEMP}x{self.EPI}/'
        #<---------------------------------------------------------------------------------------->
        #print(self.PELISPLUSHD_TO_SERIE)
    
class PELICULAS:
    def __init__(self):#,SERIE,TEMP,EPI):
        self.PELICULA = None#PELICULA
        #<---------------------------------------------------------------------------------------->
        self.PELISPLUSHD_TO_SERIE = f'pelicula/{self.PELICULA}'
        #<---------------------------------------------------------------------------------------->
        pass




#root = html.fromstring(search.page_source)
#iframe = root.xpath('//iframe/@src')[0]
#print(iframe)

#search.get(iframe)
#element = search.find_element(By.XPATH,"//li[contains(., 'streamwish')]")
#element.click()

#element.click()

#'//div[@class="play isnd"]'
#'//div[@class="pframe"]/iframe'
#'//iframe/@src'

#https://stackoverflow.com/questions/23426350/how-to-click-onclick-javascript-form-using-selenium

#root = html.fromstring(search.page_source)
#iframe = root.xpath('//div[@id="link_url"]/span/@url')
#print(iframe)

# lista de servidores
# --- pelisplushd.to ----
# https://www16.pelisplushd.to/serie/loki/temporada/1/capitulo/1
# "//div[@class='video']/div/iframe/@src" 
# se uso xpath de lxml

# lista de servidores
# -----cuevana3.ch--------
# https://www12.cuevana3.ch/episodio/the-flash-1x1
# "//ul/li[@class='open_submenu latino-select ']/div[2]/ul/li/@data-video"
# se uso xpath de lxml 

# lista de servidores
# -----cuevana3.nu--------
# https://cuevana3.nu/ver-el-episodio/episodio-6-de-loki-temporada-1/
#
# con interfaz:
# 				'//ul[@class="sub-tab-lang _3eEG3_0 optm3 latinox"]/li/@data-server'
# sin interfaz:
# 				'//div[@id="link_url"]/span/@url'
# se uso xpath de lxml 


# lista de servidores
# -----PELISPOP.LAT--------
#
# recolecta el iframe con lxml con xpath
# recive el papametro de iframe y recarga la pagina
# con otro sub menu de opciones de li luego aplica
# By.ID y hace click para ver una de las opciones
# de los servidores 

#root = html.fromstring(search.page_source)
#iframe = root.xpath('//iframe/@src')[0]
#print(iframe)

#search.get(iframe)
#element = search.find_element(By.XPATH,"//li[contains(., 'streamwish')]")
#element.click()

# todos los video se transmiten m3u8
# si se quiere ver mas rapido crear una funcion que permita buscar el m3u8
# https://chat.openai.com/c/27aa8d11-bcd1-46d7-9179-5c0bf65dd4cc

#options = Options()
#options.add_argument('--headless')
#options.add_argument("--profile")
#options.add_argument(r'/home/user/.mozilla/firefox/2sqo50t4.Default User')
#search = webdriver.Firefox(options=options)
#search.get('https://pelispop.lat/')
#time.sleep(7)

#Busqueda = search.find_element(By.XPATH,'//form[@id="searchform"]')
#Busqueda.click()
#time.sleep(3)

#iniciar = search.find_element(By.ID,'s')
#iniciar.send_keys('the flash')
#iniciar.send_keys(Keys.RETURN)

#time.sleep(3)
#root = html.fromstring(search.page_source)
#name = root.xpath('//div[@class="result-item"]/article/div[@class="details"]/div/a/@href')[1]

#nombre_de_la_serie = name.split('/')[4]
#x = SERIES(nombre_de_la_serie,'1','5')

#search.get(WEBSITE.PELISPOP_LAT+x.PELISPOP_LAT_TO_SERIE)


