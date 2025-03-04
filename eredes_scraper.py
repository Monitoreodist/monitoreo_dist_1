import requests
import os
import difflib


# URL de la API de EREDES (ajusta si es diferente)
EREDES_API_URL = "https://srv.areaprivada.eredesdistribucion.es/private/interactivemap/getNetHistory"

# Archivo donde se guardará el estado anterior
EREDES_ESTADO_FILE = "E-Redes.txt"

def obtener_pdfs_eredes():
    from monitor import obtener_html 
    """Obtiene la lista de PDFs desde la API de E-Redes Distribución."""
    try:
        response = requests.get(EREDES_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "items" in data["data"]:
                return [item["mediaLink"] for item in data["data"]["items"]]
            else:
                print("⚠️ La estructura del JSON de E-Redes no es la esperada.")
        else:
            print(f"⚠️ Error al obtener datos de E-Redes. Código {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error de conexión con la API de E-Redes: {e}")
    return []

def guardar_estado_eredes(nombre, contenido):
    filename = f"{nombre.replace(' ', '_')}.txt"
    
    if isinstance(contenido, list):
        contenido = "\n".join(contenido)  
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(contenido)
        
        print(f"✅ Estado guardado correctamente en {filename}")
        
        if os.path.exists(filename):
            print(f"📂 Archivo {filename} creado correctamente, procediendo con git commit y push.")
        else:
            print(f"❌ ERROR: {filename} no encontrado después de crearlo.")

        os.system("git config --global user.email 'github-actions@github.com'")
        os.system("git config --global user.name 'GitHub Actions'")
        os.system(f"git add {filename}")
        os.system(f'git commit -m "Actualización de {nombre}" || echo "⚠️ No hay cambios para commitear."')
        os.system("git push || echo '⚠️ No se pudo hacer push a GitHub'")
    except Exception as e:
        print(f"❌ Error al guardar el estado de {nombre}: {e}")

def detectar_cambios_eredes():
    from monitor import cargar_estado
    nombre = "E-Redes Distribución"
    
    viejo_contenido = cargar_estado(nombre)
    nuevo_contenido = obtener_pdfs_eredes()
    nuevo_contenido = "\n".join(obtener_pdfs_eredes())
    
    if not nuevo_contenido:
        print(f"⚠️ No se pudo acceder a {nombre}")
        return [], []

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

        if novedades:
            print(f"✅ **Nuevos enlaces encontrados ({len(novedades)}):**")
            for enlace in novedades:
                print(f"➕ {enlace}")

        cambios.append(f"- {nombre}: https://areaprivada.eredesdistribucion.es")
        detalles_cambios.append("\n".join(novedades) + "\n")
    
        guardar_estado_eredes(nombre, nuevo_contenido)
    else:
        print("✅ No hay cambios detectados.")
    
    print("=" * 40)
    return detalles_cambios, cambios
    
if __name__ == "__main__":
    detectar_cambios_eredes()
