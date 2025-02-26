import requests
from bs4 import BeautifulSoup
import smtplib
import os
import time
import difflib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


# Lista de URLs a monitorear
URLS = {
    "E-Distribución": "https://www.edistribucion.com/es/red-electrica/Nodos_capacidad_acceso.html",
    "I-DE Iberdrola": "https://www.i-de.es/conexion-red-electrica/produccion-energia/mapa-capacidad-acceso",
    "UFD Unión Fenosa": "https://www.ufd.es/capacidad-de-acceso-de-generacion/",
    "Viesgo Distribución": "https://www.viesgodistribucion.com/soy-cliente/mapa-interactivo-de-la-red",
    "E-Redes Distribución": "https://areaprivada.eredesdistribucion.es/blank/interactive-map"
}


def obtener_html(url, intentos=3, espera=5):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
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

def obtener_links_importantes(url, nombre):
    if nombre == "Viesgo Distribución":
        return obtener_archivos_viesgo()
    
    html = obtener_html(url)
    if not html:
        print(f"⚠️ No se pudo obtener HTML de {url}")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 🔍 Obtener todos los enlaces de la página
    todos_los_links = [a['href'] for a in soup.find_all('a', href=True)]
    print(f"\n🔍 Enlaces encontrados en {url} ({len(todos_los_links)} en total):")
    
    for enlace in todos_los_links:
        print(f"🔗 {enlace}")  # 👀 Ver todos los enlaces encontrados

    # Expresión regular para archivos PDF, XLS y XLSX
    patron = re.compile(r'([^\/]+\.pdf(?:\?.*|\/.*)?|[^\/]+\.xls(?:\?.*|\/.*)?|[^\/]+\.xlsx(?:\?.*|\/.*)?)$', re.IGNORECASE)

    # Filtrar solo los enlaces con archivos
    archivos = [link for link in todos_los_links if patron.search(link)]

    if archivos:
        print(f"📂 Archivos detectados en {nombre}:")
        for archivo in archivos:
            print(f"🔗 {archivo}")
        return "\n".join(sorted(set(archivos)))

    print(f"⚠️ No se encontraron archivos .pdf, .xls o .xlsx en {url}.")
    return None

def obtener_archivos_viesgo():
    api_url = "https://content-storage.googleapis.com/download/storage/v1/b/apdes-static-resources/o/network-capacity-map%2Fviesgo%2F"
    try:
        response = requests.get(api_url)
        data = response.json()
        archivos = [item["mediaLink"] for item in data.get("data", {}).get("items", [])]
        if archivos:
            print(f"📂 Archivos detectados en Viesgo:")
            for archivo in archivos:
                print(f"🔗 {archivo}")
            return "\n".join(archivos)
    except Exception as e:
        print(f"❌ Error obteniendo archivos de Viesgo: {e}")
    return None

def guardar_estado(nombre, contenido):
    filename = f"{nombre.replace(' ', '_')}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contenido)
    except Exception as e:
        print(f"❌ Error al guardar el estado de {nombre}: {e}")

def cargar_estado(nombre):
    filename = f"{nombre.replace(' ', '_')}.txt"
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"❌ Error al leer {filename}: {e}")
    return ""

def revisar_cambios():
    cambios = []
    detalles_cambios = []
    for nombre, url in URLS.items():
        nuevo_contenido = obtener_links_importantes(url, nombre)
        if not nuevo_contenido:
            continue
        viejo_contenido = cargar_estado(nombre)
        diferencias = list(difflib.unified_diff(
            viejo_contenido.split("\n") if viejo_contenido else [],
            nuevo_contenido.split("\n") if nuevo_contenido else [],
            lineterm=""
        ))
        if diferencias:
            cambios.append(f"- {nombre}: {url}")
            detalles_cambios.append(f"🔹 **{nombre}**:\n{diferencias}\n")
            guardar_estado(nombre, nuevo_contenido)
    if cambios:
        mensaje = "🔔 **Se han detectado cambios:**\n\n" + "\n".join(cambios) + "\n\n" + "\n".join(detalles_cambios)
        print(mensaje)
    else:
        print("✅ No hay cambios en las páginas.")

if __name__ == "__main__":
    revisar_cambios()
