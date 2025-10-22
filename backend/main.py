# backend/main.py

from fastapi import FastAPI
# ==============================================================================
# INICIO DE LA MODIFICACION: Importamos la herramienta para servir archivos
# ==============================================================================
from fastapi.staticfiles import StaticFiles
# ==============================================================================
# FIN DE LA MODIFICACION
# ==============================================================================
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import base_de_datos
from .api.enrutador_autenticacion import router_auth
from .api.enrutador_principal import router_casos, router_chat, router_evidencias

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

# ==============================================================================
# INICIO DE LA MODIFICACION: Montamos la carpeta de archivos estáticos
# ==============================================================================
# Esta linea le dice a FastAPI que cualquier peticion que empiece con '/archivos_subidos'
# debe buscar el archivo correspondiente en la carpeta 'backend/archivos_subidos' del disco.
aplicacion.mount("/archivos_subidos", StaticFiles(directory="backend/archivos_subidos"), name="archivos")
# ==============================================================================
# FIN DE LA MODIFICACION
# ==============================================================================

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("INFO: Registrando enrutadores de la API...")
aplicacion.include_router(router_auth)
aplicacion.include_router(router_casos)
aplicacion.include_router(router_chat)
aplicacion.include_router(router_evidencias)
print("-> Enrutadores registrados exitosamente.")

@aplicacion.get("/", tags=["Root"])
def leer_raiz():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}