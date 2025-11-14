# Ubicación: backend/main.py

import os # Importamos el módulo 'os'
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

# --- INICIO DE LA CORRECCIÓN #1 (ERROR DE ARRANQUE) ---
# Nos aseguramos de que el directorio para archivos subidos exista ANTES de que FastAPI intente montarlo.
# Esto soluciona el 'RuntimeError: Directory ... does not exist' durante el arranque en Render.
DIRECTORIO_SUBIDAS = "backend/archivos_subidos"
os.makedirs(DIRECTORIO_SUBIDAS, exist_ok=True)
# --- FIN DE LA CORRECCIÓN #1 ---


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

# Ahora estamos 100% seguros de que el directorio existe antes de esta línea.
aplicacion.mount("/archivos_subidos", StaticFiles(directory=DIRECTORIO_SUBIDAS), name="archivos")

# --- INICIO DE LA CORRECCIÓN #2 (ERROR DE CORS EN PRODUCCIÓN) ---
# Leemos los orígenes permitidos desde la variable de entorno definida en render.yaml.
# Esto permite que tanto el localhost (desarrollo) como el frontend de Render (producción) se conecten.
origenes_permitidos = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
print(f"INFO: Orígenes CORS permitidos: {origenes_permitidos}")

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- FIN DE LA CORRECCIÓN #2 ---

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