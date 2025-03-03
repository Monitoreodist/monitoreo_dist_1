import requests
from bs4 import BeautifulSoup
import smtplib
import os
import time
import difflib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import viesgo_scraper

# Lista de URLs a monitorear
URLS = {
    "E-Distribución": "https://www.edistribucion.com/es/red-electrica/Nodos_capacidad_acceso.html",
    "I-DE Iberdrola": "https://www.i-de.es/conexion-red-electrica/produccion-energia/mapa-capacidad-acceso",
    "UFD Unión Fenosa": "https://www.ufd.es/capacidad-de-acceso-de-generacion/",
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


import re

import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def obtener_links_importantes(url, nombre):
    """Obtiene los enlaces de archivos PDF, XLS y XLSX de una página web, excepto Viesgo."""
    if nombre == "Viesgo Distribución":
        return None  # Se manejará por la API
        
    html = obtener_html(url)
    if not html:
        print(f"⚠️ No se pudo obtener HTML de {url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 🔍 Obtener todos los enlaces de la página
    todos_los_links = [a['href'] for a in soup.find_all('a', href=True)]
    print(f"\n🔍 Enlaces encontrados en {url} ({len(todos_los_links)} en total):")
    
    # Expresión regular para capturar archivos .pdf, .xls, .xlsx sin importar los parámetros después
    patron = re.compile(r'([^\/]+\.pdf(?:\?.*|\/.*)?|[^\/]+\.xls(?:\?.*|\/.*)?|[^\/]+\.xlsx(?:\?.*|\/.*)?)$', re.IGNORECASE)

    # Filtrar solo los enlaces que contienen archivos PDF, XLS o XLSX
    archivos = [link for link in todos_los_links if patron.search(link)]

    # 🟢 Si NO encontramos PDFs en la página normal y es Viesgo, usamos Selenium
    if not archivos and nombre == "Viesgo Distribución":
        print("⚠️ No se encontró PDF en HTML, intentando con Selenium...")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Modo sin interfaz gráfica
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Cargar la página de Viesgo
        driver.get(url)
        time.sleep(5)  # Esperar a que cargue la web

        # Obtener todos los enlaces de la web renderizada
        selenium_links = [a.get_attribute("href") for a in driver.find_elements(By.TAG_NAME, "a")]

        # Filtrar PDFs con Selenium
        archivos = [link for link in selenium_links if link and "pdf" in link.lower()]

        driver.quit()

    # Mostrar los archivos detectados
    if archivos:
        print(f"📂 Archivos detectados en {nombre}:")
        for archivo in archivos:
            print(f"🔗 {archivo}")
        return "\n".join(sorted(set(archivos)))  # Devolver los enlaces únicos en formato string

    print(f"⚠️ No se encontraron archivos .pdf, .xls o .xlsx en {url}.")
    return None





# Función para guardar el estado en un archivo TXT
def guardar_estado(nombre, contenido):
    filename = f"{nombre.replace(' ', '_')}.txt"
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contenido)
        
        print(f"✅ Estado guardado correctamente en {filename}")

        # 📂 Verificar que el archivo existe después de guardarlo
        if os.path.exists(filename):
            print(f"📂 Archivo {filename} existe después de guardarlo.")
        else:
            print(f"❌ Archivo {filename} NO se encuentra después de guardarlo.")

        # 🟢 Hacer commit y push de los cambios en GitHub Actions
        os.system("git config --global user.email 'github-actions@github.com'")
        os.system("git config --global user.name 'GitHub Actions'")
        os.system(f"git add {filename}")
        os.system(f'git commit -m "Actualización de {nombre}" || echo "⚠️ No hay cambios para commitear."')
        os.system("git push || echo '⚠️ No se pudo hacer push a GitHub'")




    except Exception as e:
        print(f"❌ Error al guardar el estado de {nombre}: {e}")





# Función para cargar el estado previo desde un archivo TXT
def cargar_estado(nombre):
    filename = f"{nombre.replace(' ', '_')}.txt"
    
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                contenido = f.read().strip()  # Eliminamos espacios vacíos extra
                print(f"📄 Archivo {filename} leído correctamente. Contenido anterior:")
                print(contenido if contenido else "⚠️ El archivo estaba vacío.")
                return contenido
        except Exception as e:
            print(f"❌ Error al leer {filename}: {e}")
            return ""
    else:
        print(f"⚠️ El archivo {filename} no existe aún. (Primera ejecución esperada)")
    
    return ""



# Función para detectar diferencias entre el contenido anterior y el nuevo
def obtener_diferencias(viejo_contenido, nuevo_contenido):
    viejo_lineas = viejo_contenido.split("\n")
    nuevo_lineas = nuevo_contenido.split("\n")

    diff = list(difflib.unified_diff(viejo_lineas, nuevo_lineas, lineterm=""))
    return "\n".join(diff) if diff else "No hay cambios detectados."








def enviar_email(detalles_cambios):
    """ Envía un correo con los cambios detectados, mostrando solo los enlaces añadidos correctamente. """
    if not detalles_cambios or not isinstance(detalles_cambios, list):
        print("✅ No hay cambios detectados o formato incorrecto. No se enviará correo.")
        return

    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "🔔 Cambios detectados en las webs monitoreadas"

    # Mensaje en texto plano
    mensaje_texto = "🔔 **Se han detectado cambios en las siguientes páginas:**\n"
    
    # Mensaje en formato HTML
    mensaje_html = "<html><body><h2>🔔 Se han detectado cambios en las siguientes páginas:</h2><ul>"

    print("\n🔍 DEPURACIÓN: Detalles de cambios recibidos:")
    for cambio in detalles_cambios:
        print(cambio)  # 🚀 Ver qué datos se están procesando

        # Verificar si el cambio está en el formato correcto
        if not isinstance(cambio, str) or ":\n" not in cambio:
            continue  # Ignorar entradas no válidas

        plataforma, diffs = cambio.split(":\n", 1)
        lineas = diffs.strip("[]").replace("'", "").split(", ")

        # Extraer SOLO los enlaces nuevos añadidos (+)
        nuevos = [line[1:].strip() for line in lineas if line.startswith("+") and "http" in line]

        if nuevos:
            print(f"✅ {plataforma} - Enlace añadido: {nuevos}")  # 🔍 Verificar qué enlaces aparecen

            mensaje_texto += f"\n📂 **{plataforma}**\n"
            mensaje_html += f"<li><b>{plataforma}</b><ul>"

            for enlace in nuevos:
                mensaje_texto += f"  ➕ {enlace}\n"
                mensaje_html += f"<li><a href='{enlace}'>{enlace}</a></li>"

            mensaje_html += "</ul></li>"

    mensaje_html += "</ul></body></html>"

    # Si no hay enlaces nuevos, no enviamos nada
    if "📂" not in mensaje_texto:
        print("⚠️ No se encontraron enlaces añadidos. No se enviará correo.")
        return

    # Adjuntar versiones en texto y HTML
    msg.attach(MIMEText(mensaje_texto.strip(), "plain", "utf-8"))
    msg.attach(MIMEText(mensaje_html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("📧 Correo enviado correctamente.")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")


import difflib

def revisar_cambios():
    cambios = []
    detalles_cambios = []

    # Primero, revisar Viesgo usando su API
    print("\n🔍 **Revisando Viesgo Distribución...**")
    cambios_viesgo, detalles_viesgo = viesgo_scraper.detectar_cambios_viesgo()

    if cambios_viesgo:
        cambios.extend(cambios_viesgo)  # 🔹 Agregar cambios de Viesgo a la lista general
    if detalles_viesgo:
        detalles_cambios.extend(detalles_viesgo)

    
    for nombre, url in URLS.items():
        
        if nombre == "Viesgo Distribución":  # 🔹 Saltar Viesgo, ya se procesó antes
            continue

        nuevo_contenido = obtener_links_importantes(url, nombre)
        if not nuevo_contenido:
            print(f"⚠️ No se pudo acceder a {nombre}")
            continue

        viejo_contenido = cargar_estado(nombre)

        # 🔍 Imprimir contenido anterior solo una vez
        print(f"\n📂 **{nombre}** - Comparación de estado")
        print("=" * 40)

        if viejo_contenido:
            print("📜 **Contenido anterior:**")
            lineas_viejas = viejo_contenido.split("\n")
            print(f"🔹 {len(lineas_viejas)} enlaces guardados anteriormente.")
        else:
            print("📜 **Contenido anterior:** ❌ No había archivo previo o estaba vacío.")

        if nuevo_contenido:
            lineas_nuevas = nuevo_contenido.split("\n")
            print(f"🆕 **Nuevo contenido:** 🔹 {len(lineas_nuevas)} enlaces encontrados en la web.")
        else:
            print("🆕 **Nuevo contenido:** ❌ No se encontró contenido nuevo.")

        # Comparar y mostrar solo las novedades
        diferencias = list(difflib.unified_diff(
            viejo_contenido.split("\n") if viejo_contenido else [],
            nuevo_contenido.split("\n") if nuevo_contenido else [],
            lineterm=""
        ))

        if diferencias:
            print("\n🔍 **Diferencias detectadas:**")
            novedades = [line[1:] for line in diferencias if line.startswith("+")]
            eliminados = [line[1:] for line in diferencias if line.startswith("-")]

            if novedades:
                print(f"✅ **Nuevos enlaces encontrados ({len(novedades)}):**")
                for enlace in novedades:
                    print(f"➕ {enlace}")

            if eliminados:
                print(f"❌ **Enlaces eliminados ({len(eliminados)}):**")
                for enlace in eliminados:
                    print(f"➖ {enlace}")

            cambios.append(f"- {nombre}: {url}")
            detalles_cambios.append(f"🔹 **{nombre}**:\n{diferencias}\n")

            # Guardar la nueva lista de archivos detectados
            guardar_estado(nombre, nuevo_contenido)

        else:
            print("✅ No hay cambios detectados.")

        print("=" * 40)  # Separador para mayor claridad

    if cambios:
        mensaje = "🔔 **Se han detectado cambios en las siguientes páginas:**\n\n" + "\n".join(cambios) + "\n\n" + "\n".join(detalles_cambios)
        enviar_email(mensaje)
    else:
        print("✅ No hay cambios en las páginas.")




# Ejecutar la revisión cuando se corre el script
if __name__ == "__main__":
    revisar_cambios()
