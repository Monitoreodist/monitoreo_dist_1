import requests
import os
import difflib
from monitor import obtener_links_importantes, cargar_estado



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



import difflib
import os

def detectar_cambios_viesgo():
    nombre = "Viesgo Distribución"
    
    # Cargar estado anterior
    viejo_contenido = cargar_estado(nombre)

    # Obtener nuevos enlaces de Viesgo
    nuevo_contenido = obtener_pdfs_viesgo()
    nuevo_contenido = "\n".join(obtener_pdfs_viesgo())
    if not nuevo_contenido:
        print(f"⚠️ No se pudo acceder a {nombre}")
        return [], []

    # 🔍 Imprimir contenido anterior
    print(f"\n📂 **{nombre}** - Comparación de estado")
    print("=" * 40)

    if viejo_contenido:
        lineas_viejas = viejo_contenido.split("\n")
        print(f"📜 **Contenido anterior:** 🔹 {len(lineas_viejas)} enlaces guardados anteriormente.")
    else:
        print("📜 **Contenido anterior:** ❌ No había archivo previo o estaba vacío.")

    if nuevo_contenido:
        lineas_nuevas = nuevo_contenido.split("\n")
        print(f"🆕 **Nuevo contenido:** 🔹 {len(lineas_nuevas)} enlaces encontrados en la web.")
    else:
        print("🆕 **Nuevo contenido:** ❌ No se encontró contenido nuevo.")

    # Comparar diferencias
    diferencias = list(difflib.unified_diff(
        viejo_contenido.split("\n") if viejo_contenido else [],
        nuevo_contenido.split("\n") if nuevo_contenido else [],
        lineterm=""
    ))

    cambios = []
    detalles_cambios = []

    if diferencias:
        print("\n🔍 **Diferencias detectadas:**")
        novedades = [line[1:] for line in diferencias if line.startswith("+")]
        novedades = [enlace for enlace in novedades if enlace.startswith("http") or enlace.startswith("\\")]
        #eliminados = [line[1:] for line in diferencias if line.startswith("-")]

        if novedades:
            print(f"✅ **Nuevos enlaces encontrados ({len(novedades)}):**")
            for enlace in novedades:
                print(f"➕ {enlace}")

        #if eliminados:
        #    print(f"❌ **Enlaces eliminados ({len(eliminados)}):**")
        #    for enlace in eliminados:
        #        print(f"➖ {enlace}")

        cambios.append(f"- {nombre}: https://www.viesgodistribucion.com")
        detalles_cambios.append(f"🔹 **{nombre}**:\n" + "\n".join(novedades) + "\n")
        print(cambios)
        print(detalles_cambios)

        # Guardar nuevo estado
        guardar_estado_viesgo(nombre, nuevo_contenido)

    else:
        print("✅ No hay cambios detectados.")

    print("=" * 40)

    return cambios, detalles_cambios

    

if __name__ == "__main__":
    detectar_cambios_viesgo()

