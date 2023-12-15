from constants import SERVIDORES
import time



PELISPLUSHD_TO_SERVIDORES = ['SBFast','Mobile','VIP','Upfast','DoodStream','PLUSTO VIP','Uqload','filemoon','voesx','streamwish','doodstream','streamtape','netu','filelions']

for servidor in PELISPLUSHD_TO_SERVIDORES:
	try:
		time.sleep(3)
		print(f'Scrapeo Exitoso Url De Video {servidor}')
			
	except KeyboardInterrupt:
		print('interrupcion de teclado')
		break
        
        
