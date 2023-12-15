import urllib3

# Deshabilitar la verificación del certificado SSL
http = urllib3.PoolManager(cert_reqs='CERT_NONE', assert_hostname=False)

# Realiza una solicitud GET a una URL
url = 'https://www.ejemplo.com'
response = http.request('GET', url)

# Obtiene el código de estado de la respuesta
status_code = response.status

# Imprime el código de estado
print(status_code)
