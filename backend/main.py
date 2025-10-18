# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from . import base_de_datos
# Importamos los routers de casos y chat
from .api.enrutador_principal import router_casos, router_chat


from .api.enrutador_autenticacion import router_auth


from .herramientas import herramienta_rag, herramienta_multimodal_gemini

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona los eventos de inicio y apagado de la aplicacion.
    """
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
print("-> Enrutadores de Autenticacion, Casos y Chat registrados exitosamente.")

@aplicacion.get("/", tags=["Root"])
def leer_raiz():
    """
    Endpoint principal de bienvenida para verificar que la API esta en linea.
    """
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}