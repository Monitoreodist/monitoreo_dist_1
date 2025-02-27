import requests
import os
import difflib

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

    # 🔹 Asegurar que contenido es una cadena de texto, si es lista, la convertimos
    if isinstance(contenido, list):
        contenido = "\n".join(contenido)  # Convierte lista en string con saltos de línea

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
    """Compara el estado actual con el anterior y detecta novedades en Viesgo."""
    nuevos_enlaces = obtener_pdfs_viesgo()
    enlaces_anteriores = cargar_estado_viesgo()

    print("\n📂 **Viesgo Distribución** - Comparación de estado")
    print("=" * 40)

    if enlaces_anteriores:
        print("📜 **Contenido anterior:**")
        lineas_viejas = enlaces_anteriores.split("\n")
        print(f"🔹 {len(lineas_viejas)} enlaces guardados anteriormente.")
    else:
        print("📜 **Contenido anterior:** ❌ No había archivo previo o estaba vacío.")

    if nuevos_enlaces:
        lineas_nuevas = nuevos_enlaces
        print(f"🆕 **Nuevo contenido:** 🔹 {len(lineas_nuevas)} enlaces encontrados en la web.")
    else:
        print("🆕 **Nuevo contenido:** ❌ No se encontró contenido nuevo.")

    # Comparar las diferencias
    diferencias = list(difflib.unified_diff(
        enlaces_anteriores.split("\n") if enlaces_anteriores else [],
        nuevos_enlaces.split("\n") if nuevos_enlaces else [],
        lineterm=""
    ))

    cambios = []
    detalles_cambios = []

    if diferencias:
        print("\n🔍 **Diferencias detectadas:**")
        nuevos = [line[1:] for line in diferencias if line.startswith("+")]
        eliminados = [line[1:] for line in diferencias if line.startswith("-")]

        if nuevos:
            print(f"✅ **Nuevos enlaces encontrados ({len(nuevos)}):**")
            for enlace in nuevos:
                print(f"➕ {enlace}")

        if eliminados:
            print(f"❌ **Enlaces eliminados ({len(eliminados)}):**")
            for enlace in eliminados:
                print(f"➖ {enlace}")

        cambios.append("- Viesgo Distribución")
        detalles_cambios.append(f"🔹 **Viesgo Distribución**:\n{diferencias}\n")

        # Guardar la nueva lista de archivos detectados
        guardar_estado_viesgo("\n".join(nuevos_enlaces))

    else:
        print("✅ No hay cambios detectados.")

    print("=" * 40)  # Separador para mayor claridad

    return cambios, detalles_cambios  # 🔹 Ahora devuelve los cambios detectados

    

if __name__ == "__main__":
    detectar_cambios_viesgo()

