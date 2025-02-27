import requests
import os

# URL de la API de Viesgo (ajusta si es diferente)
VIESGO_API_URL = "https://srv.areaprivada.viesgodistribucion.com/private/interactivemap/getNetHistory"

# Archivo donde se guardará el estado anterior
VIESGO_ESTADO_FILE = "Viesgo.txt"

def obtener_pdfs_viesgo():
    """Obtiene la lista de PDFs desde la API de Viesgo."""
    try:
        response = requests.get(VIESGO_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "items" in data["data"]:
                return [item["mediaLink"] for item in data["data"]["items"]]
            else:
                print("⚠️ La estructura del JSON de Viesgo no es la esperada.")
        else:
            print(f"⚠️ Error al obtener datos de Viesgo. Código {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API de Viesgo: {e}")
    return []

def cargar_estado_viesgo():
    """Carga el estado anterior desde un archivo."""
    if os.path.exists(VIESGO_ESTADO_FILE):
        with open(VIESGO_ESTADO_FILE, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    return []

def guardar_estado_viesgo(enlaces):
    """Guarda el estado actual de los enlaces en un archivo."""
    try:
        with open(VIESGO_ESTADO_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(enlaces))
        print(f"✅ Estado de Viesgo guardado correctamente en {VIESGO_ESTADO_FILE}")
    except Exception as e:
        print(f"❌ Error al guardar el estado de Viesgo: {e}")


def detectar_cambios_viesgo():
    """Compara el estado actual con el anterior y detecta novedades."""
    nuevos_enlaces = obtener_pdfs_viesgo()
    enlaces_anteriores = cargar_estado_viesgo()

    if not nuevos_enlaces:
        print("⚠️ No se encontraron PDFs nuevos en Viesgo.")
        return

    nuevos = set(nuevos_enlaces) - set(enlaces_anteriores)
    eliminados = set(enlaces_anteriores) - set(nuevos_enlaces)

    if nuevos:
        print("🆕 **Nuevos archivos en Viesgo:**")
        for enlace in nuevos:
            print(f"➕ {enlace}")

    if eliminados:
        print("❌ **Archivos eliminados en Viesgo:**")
        for enlace in eliminados:
            print(f"➖ {enlace}")

    if nuevos or eliminados:
        guardar_estado_viesgo(nuevos_enlaces)
    else:
        print("✅ No hay cambios en los archivos de Viesgo.")

if __name__ == "__main__":
    detectar_cambios_viesgo()

