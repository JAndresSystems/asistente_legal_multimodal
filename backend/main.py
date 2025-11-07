# backend/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import base_de_datos

# --- INICIO DE LA MODIFICACIÓN ---
# Importamos los routers desde sus nuevos módulos
from .api.enrutador_autenticacion import router_auth
from .api.enrutador_principal import router_chat, router_evidencias
from .api.enrutador_agentes import router_agentes
from .api.enrutador_asesor import router_asesor
from .api.enrutador_administrador import router as router_administrador
from .api.enrutador_usuario import router as router_usuario
from .api.enrutador_estudiante import router as router_estudiante

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