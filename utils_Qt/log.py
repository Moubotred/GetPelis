import logging
    
logger = logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(name)s - %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S',
    # handlers=[
        # logging.RotatingFileHandler('app.log', maxBytes=5*1024*1024, backupCount=3),  # 5MB por archivo, 3 archivos de backup
    #     logging.StreamHandler()
    # ]
)

# logging.getLogger("httpx").setLevel(logging.INFO)  # Reduce el nivel de logging de httpx

logging.getLogger("httpx").disabled = True
logging.getLogger("seleniumwire.handler").disabled = True
logging.getLogger("seleniumwire.server").disabled = True
logging.getLogger("seleniumwire.storage").disabled = True
logging.getLogger("seleniumwire.backend").disabled = True


logger = logging.getLogger(__name__)



# # Configurar niveles específicos para librerías externas
# logging.getLogger("httpx").setLevel(logging.INFO)  # Reduce el nivel de logging de httpx
# # logging.getLogger("httpcore").setLevel(logging.WARNING)  # httpx depende de httpcore

# # Opcional: Configurar otras librerías que puedan ser ruidosas
# logging.getLogger("urllib3").setLevel(logging.WARNING)
# logging.getLogger("asyncio").setLevel(logging.WARNING)

# # Nivel más detallado para tu aplicación
# logging.getLogger("seleniumwire.handler").setLevel(logging.INFO)
# # logging.getLogger("services").setLevel(logging.INFO)

# logger = logging.getLogger(__name__)
# logger.info("Configuración de logging completada")