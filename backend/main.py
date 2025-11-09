# C:\react\asistente_legal_multimodal\backend\main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os # Asegúrate de importar os

from . import base_de_datos

from .api.enrutador_autenticacion import router_auth
from .api.enrutador_principal import router_chat, router_evidencias
from .api.enrutador_agentes import router_agentes
from .api.enrutador_asesor import router_asesor
from .api.enrutador_administrador import router as router_administrador
from .api.enrutador_usuario import router as router_usuario
from .api.enrutador_estudiante import router as router_estudiante

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Iniciando la aplicación (dentro del lifespan)...")
    base_de_datos.inicializar_base_de_datos()
    yield
    print("INFO:     Apagando la aplicación...")

aplicacion = FastAPI(
    title="API del Asistente Legal Multimodal",
    description="Proyecto de grado para gestionar y analizar evidencia legal con agentes de IA.",
    version="1.0.0",
    lifespan=lifespan
)

# =====================================================================
#  Creamos el directorio ANTES de intentar montarlo.
# Esta es la lógica correcta porque este código se ejecuta al leer el archivo.
# =====================================================================
print("SETUP-FILES: Verificando y creando el directorio para archivos subidos...")
os.makedirs("backend/archivos_subidos", exist_ok=True)
print("SETUP-FILES: Directorio 'backend/archivos_subidos' listo.")

aplicacion.mount("/archivos_subidos", StaticFiles(directory="backend/archivos_subidos"), name="archivos")

# --- Configuración de CORS ---
# Lee la variable de entorno CORS_ORIGINS
origenes_cors_raw = os.getenv("CORS_ORIGINS", "")
# Divídela por comas si está definida
if origenes_cors_raw:
    # Elimina espacios en blanco alrededor de cada origen
    origenes_permitidos = [orig.strip() for orig in origenes_cors_raw.split(",")]
else:
    # Fallback por si la variable no está definida (solo desarrollo local)
    origenes_permitidos = ["http://localhost:5173", "http://127.0.0.1:5173"]

print(f"DEBUG: Orígenes CORS configurados: {origenes_permitidos}") # Línea de debug opcional, puedes quitarla luego

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos, # Usamos la lista de orígenes leída
    allow_credentials=True,
    allow_methods=["*"], # O restringe a ["GET", "POST", "PUT", "DELETE"] si lo prefieres
    allow_headers=["*"], # O restringe si lo prefieres
)

print("INFO: Registrando enrutadores de la API...")
aplicacion.include_router(router_auth)
aplicacion.include_router(router_chat)
aplicacion.include_router(router_evidencias)
aplicacion.include_router(router_agentes)
aplicacion.include_router(router_asesor)
aplicacion.include_router(router_administrador)
aplicacion.include_router(router_usuario)
aplicacion.include_router(router_estudiante)
print("-> Enrutadores registrados exitosamente.")

@aplicacion.get("/", tags=["Root"])
def leer_raiz():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}
