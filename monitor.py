import requests
from bs4 import BeautifulSoup
import smtplib
import os
import time
import difflib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lista de URLs a monitorear
URLS = {
    "E-Distribución": "https://www.edistribucion.com/es/red-electrica/Nodos_capacidad_acceso.html",
    "I-DE Iberdrola": "https://www.i-de.es/conexion-red-electrica/produccion-energia/mapa-capacidad-acceso",
    "UFD Unión Fenosa": "https://www.ufd.es/capacidad-de-acceso-de-generacion/",
    "Viesgo Distribución": "https://www.viesgodistribucion.com/soy-cliente/mapa-interactivo-de-la-red",
    "E-Redes Distribución": "https://areaprivada.eredesdistribucion.es/blank/interactive-map"  # Nueva URL
}

# Credenciales para el envío de correos (se configuran en GitHub)
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")


# Función para obtener el contenido HTML de una web con reintentos
def obtener_html(url, intentos=3, espera=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    session = requests.Session()
    session.headers.update(headers)

    for intento in range(intentos):
        try:
            response = session.get(url, timeout=15)
            if response.status_code == 200:
                return response.text
            print(f"⚠️ Intento {intento + 1} fallido para {url} (Código {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error en {url}: {e}")
        time.sleep(espera)
    return None


# Función para extraer los enlaces a archivos importantes (.pdf, .xls, .xlsx)
def obtener_links_importantes(url):
    html = obtener_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith(('.pdf', '.xls', '.xlsx'))]

    return "\n".join(sorted(links))  # Convertimos la lista a un string ordenado para comparar


# Función para guardar el estado en un archivo TXT
def guardar_estado(nombre, contenido):
    filename = f"{nombre.replace(' ', '_')}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"✅ Estado guardado correctamente en {filename}")
        print(f"📄 Contenido guardado en {filename}:\n{contenido}")  # 🔍 Verificar contenido

        # 🔄 Agregar y subir cambios a GitHub
        os.system(f"git add {filename}")
        os.system(f'git commit -m "Actualización de {nombre}"')
        os.system("git push")

    except Exception as e:
        print(f"❌ Error al guardar el estado de {nombre}: {e}")



# Función para cargar el estado previo desde un archivo TXT
def cargar_estado(nombre):
    filename = f"{nombre.replace(' ', '_')}.txt"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error al leer {filename}: {e}")
            return ""
    return ""


# Función para detectar diferencias entre el contenido anterior y el nuevo
def obtener_diferencias(viejo_contenido, nuevo_contenido):
    viejo_lineas = viejo_contenido.split("\n")
    nuevo_lineas = nuevo_contenido.split("\n")

    diff = list(difflib.unified_diff(viejo_lineas, nuevo_lineas, lineterm=""))
    return "\n".join(diff) if diff else "No hay cambios detectados."


# Función para enviar email con notificación de cambios
def enviar_email(mensaje):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "🔔 Cambios detectados en las webs monitoreadas"

    msg.attach(MIMEText(mensaje, "plain", "utf-8"))
    msg.attach(MIMEText(f"<html><body><pre>{mensaje}</pre></body></html>", "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("📧 Correo enviado correctamente.")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")


def revisar_cambios():
    cambios = []
    detalles_cambios = []

    for nombre, url in URLS.items():
        nuevo_contenido = obtener_links_importantes(url)
        if not nuevo_contenido:
            print(f"⚠️ No se pudo acceder a {nombre}")
            continue

        viejo_contenido = cargar_estado(nombre)

        # 🔍 Imprimir contenido anterior y nuevo para depuración
        print(f"\n📂 **{nombre}** - Comparación de estado")
        print("=" * 40)
        print(f"📜 **Contenido anterior en {nombre}.txt:**")
        print(viejo_contenido if viejo_contenido else "❌ No había archivo previo o estaba vacío.")
        print("\n🆕 **Nuevo contenido extraído de la web:**")
        print(nuevo_contenido if nuevo_contenido else "❌ No se encontró contenido nuevo.")
        print("=" * 40)

        if nuevo_contenido != viejo_contenido:
            print(f"🔔 ¡Cambio detectado en {nombre}!")
            cambios.append(f"- {nombre}: {url}")

            # Obtener diferencias exactas
            diferencias = obtener_diferencias(viejo_contenido, nuevo_contenido)
            print("\n🔍 **Diferencias detectadas:**")
            print(diferencias if diferencias else "No hay diferencias significativas.")
            detalles_cambios.append(f"🔹 **{nombre}**:\n{diferencias}\n")

            # Guardar la nueva lista de archivos detectados
            guardar_estado(nombre, nuevo_contenido)

    if cambios:
        mensaje = "🔔 **Se han detectado cambios en las siguientes páginas:**\n\n" + "\n".join(cambios) + "\n\n" + "\n".join(detalles_cambios)
        enviar_email(mensaje)
    else:
        print("✅ No hay cambios en las páginas.")



# Ejecutar la revisión cuando se corre el script
if __name__ == "__main__":
    revisar_cambios()
