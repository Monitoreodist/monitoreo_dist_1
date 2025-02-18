import requests
from bs4 import BeautifulSoup
import smtplib
import os

# Lista de URLs a monitorear
URLS = {
    "E-Distribución": "https://www.edistribucion.com/es/red-electrica/Nodos_capacidad_acceso.html",
    "I-DE Iberdrola": "https://www.i-de.es/conexion-red-electrica/produccion-energia/mapa-capacidad-acceso",
    "UFD Unión Fenosa": "https://www.ufd.es/capacidad-de-acceso-de-generacion/",
    "Viesgo Distribución": "https://www.viesgodistribucion.com/soy-cliente/mapa-interactivo-de-la-red",
    "E-Redes Distribución": "https://www.eredesdistribucion.es/soy-cliente/mapa-interactivo-de-la-red"
}

# Credenciales para el envío de correos (se configuran en GitHub)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# Función para obtener el contenido HTML de una web
def obtener_html(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    return response.text if response.status_code == 200 else None

# Función para enviar correos
def enviar_email(mensaje):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, f"Subject: 🔔 Cambio detectado en una web\n\n{mensaje}")

# Revisar cambios en las webs
def revisar_cambios():
    cambios = []
    
    for nombre, url in URLS.items():
        nuevo_html = obtener_html(url)
        if not nuevo_html:
            print(f"⚠️ No se pudo acceder a {nombre}")
            continue

        filename = f"/tmp/{nombre.replace(' ', '_')}.txt"
        
        try:
            with open(filename, "r") as f:
                viejo_html = f.read()
        except FileNotFoundError:
            viejo_html = ""

        # Si el contenido ha cambiado, se notifica
        if nuevo_html != viejo_html:
            print(f"🔔 ¡Cambio detectado en {nombre}!")
            cambios.append(f"- {nombre}: {url}")
            with open(filename, "w") as f:
                f.write(nuevo_html)

    # Si hubo cambios, enviamos el correo
    if cambios:
        mensaje = "Se han detectado cambios en las siguientes páginas:\n\n" + "\n".join(cambios)
        enviar_email(mensaje)
    else:
        print("✅ No hay cambios en las páginas.")

# Ejecutar la revisión
if __name__ == "__main__":
    revisar_cambios()
