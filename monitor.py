import requests
from bs4 import BeautifulSoup
import smtplib
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lista de URLs a monitorear
URLS = {
    "E-Distribución": "https://www.edistribucion.com/es/red-electrica/Nodos_capacidad_acceso.html",
    "I-DE Iberdrola": "https://www.i-de.es/conexion-red-electrica/produccion-energia/mapa-capacidad-acceso",
    "UFD Unión Fenosa": "https://www.ufd.es/capacidad-de-acceso-de-generacion/",
    "Viesgo Distribución": "https://www.viesgodistribucion.com/soy-cliente/mapa-interactivo-de-la-red",
    "E-Redes Distribución": "https://areaprivada.eredesdistribucion.es/blank/interactive-map"  # NUEVA URL
}


# Credenciales para el envío de correos (se configuran en GitHub)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

# Función para obtener el contenido HTML de una web
def obtener_html(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    return response.text if response.status_code == 200 else None



def enviar_email(mensaje):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "🔔 Cambio detectado en una web"

    # Convertimos el mensaje a UTF-8
    msg.attach(MIMEText(mensaje, "plain", "utf-8"))

    # Enviar el correo
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())



def obtener_links_importantes(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Error {response.status_code} al acceder a {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.pdf', '.xls', '.xlsx'))]

        return "\n".join(sorted(links))  # Convertimos la lista a un string ordenado para comparar
    except requests.exceptions.RequestException as e:
        print(f"⚠️ No se pudo acceder a {url}: {e}")
        return None



# Revisar cambios en las webs
def revisar_cambios():
    cambios = []
    
    for nombre, url in URLS.items():
        nuevo_contenido = obtener_links_importantes(url)
        if not nuevo_contenido:
            print(f"⚠️ No se pudo acceder a {nombre}")
            continue

        filename = f"{nombre.replace(' ', '_')}.txt"
        
        try:
            with open(filename, "r") as f:
                viejo_contenido = f.read()
        except FileNotFoundError:
            viejo_contenido = ""

        if nuevo_contenido != viejo_contenido:
            print(f"🔔 ¡Cambio detectado en {nombre}!")
            cambios.append(f"- {nombre}: {url}")
            with open(filename, "w") as f:
                f.write(nuevo_contenido)

    if cambios:
        mensaje = "Se han detectado cambios en las siguientes páginas:\n\n" + "\n".join(cambios)
        enviar_email(mensaje)
    else:
        print("✅ No hay cambios en las páginas.")



# Ejecutar la revisión
if __name__ == "__main__":
    revisar_cambios()
