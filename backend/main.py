# Ubicación: backend/main.py

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import base_de_datos

# Importamos los routers desde sus módulos
from .api.enrutador_autenticacion import router_auth
from .api.enrutador_principal import router_chat, router_evidencias
from .api.enrutador_agentes import router_agentes
from .api.enrutador_asesor import router_asesor
from .api.enrutador_administrador import router as router_administrador
from .api.enrutador_usuario import router as router_usuario
from .api.enrutador_estudiante import router as router_estudiante

# --- INICIO DE LA CORRECCIÓN ROBUSTA DE RUTAS ---
# 1. Obtenemos la ruta absoluta de la carpeta donde está ESTE archivo (main.py)
# Esto garantiza que funcione igual en Windows, Linux y Render.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Definimos la carpeta de subidas relativa a este archivo.
# Resultado esperado: .../backend/archivos_subidos
DIRECTORIO_SUBIDAS = os.path.join(BASE_DIR, "archivos_subidos")

# 3. Creamos la carpeta si no existe para evitar errores de arranque
os.makedirs(DIRECTORIO_SUBIDAS, exist_ok=True)
print(f"INFO: Carpeta de archivos configurada en: {DIRECTORIO_SUBIDAS}")
# --- FIN DE LA CORRECCIÓN ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Iniciando la aplicación...")
    base_de_datos.inicializar_base_de_datos()
    yield
    print("INFO:     Apagando la aplicación...")

aplicacion = FastAPI(
    title="API del Asistente Legal Multimodal",
    description="Proyecto de grado para gestionar y analizar evidencia legal con agentes de IA.",
    version="1.0.0",
    lifespan=lifespan
)

# Montamos la carpeta estática usando la ruta absoluta calculada.
# Esto permite acceder a http://localhost:8000/archivos_subidos/foto.png
aplicacion.mount("/archivos_subidos", StaticFiles(directory=DIRECTORIO_SUBIDAS), name="archivos")

# --- CONFIGURACIÓN DE CORS (Conexión Frontend-Backend) ---
# Leemos los orígenes permitidos desde la variable de entorno o usamos localhost por defecto.
origenes_permitidos = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
print(f"INFO: Orígenes CORS permitidos: {origenes_permitidos}")

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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