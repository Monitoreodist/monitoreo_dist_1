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

# Función para guardar el estado en un archivo TXT y subirlo a GitHub
def guardar_estado_viesgo(nombre, contenido):
    filename = f"{nombre.replace(' ', '_')}.txt"

    # 🔹 Convertir la lista en una cadena separada por saltos de línea
    contenido_str = "\n".join(contenido) if isinstance(contenido, list) else contenido

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contenido)
        
        print(f"✅ Estado guardado correctamente en {filename}")

        # 📂 Verificar que el archivo existe antes de hacer commit
        if os.path.exists(filename):
            print(f"📂 Archivo {filename} creado correctamente, procediendo con git commit y push.")
        else:
            print(f"❌ ERROR: {filename} no encontrado después de crearlo.")

        # 🟢 Hacer commit y push de los cambios en GitHub Actions
        os.system("git config --global user.email 'github-actions@github.com'")
        os.system("git config --global user.name 'GitHub Actions'")
        os.system(f"git add {filename}")
        os.system(f'git commit -m "Actualización de {nombre}" || echo "⚠️ No hay cambios para commitear."')
        os.system("git push || echo '⚠️ No se pudo hacer push a GitHub'")

    except Exception as e:
        print(f"❌ Error al guardar el estado de {nombre}: {e}")



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
        guardar_estado_viesgo("Viesgo Distribución", nuevos_enlaces)
    else:
        print("✅ No hay cambios en los archivos de Viesgo.")

if __name__ == "__main__":
    detectar_cambios_viesgo()

