# backend/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import base_de_datos
from .api.enrutador_autenticacion import router_auth

# ==============================================================================
# INICIO DE LA CORRECCION: Eliminamos la importación duplicada
# ==============================================================================
# Mantenemos únicamente la línea que importa TODOS los routers necesarios.
from .api.enrutador_principal import router_casos, router_chat, router_evidencias, router_expedientes
# La línea duplicada ha sido eliminada.
# ==============================================================================
# FIN DE LA CORRECCION
# ==============================================================================

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

aplicacion.mount("/archivos_subidos", StaticFiles(directory="backend/archivos_subidos"), name="archivos")

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
aplicacion.include_router(router_expedientes)
print("-> Enrutadores registrados exitosamente.")

@aplicacion.get("/", tags=["Root"])
def leer_raiz():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}