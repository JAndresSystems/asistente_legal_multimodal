# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importamos la función de inicialización de la base de datos
from . import base_de_datos
# --- CAMBIO CLAVE ---
# Ya no importamos 'enrutador_principal' completo.
# En su lugar, importamos especificamente los DOS routers que creamos dentro de ese archivo.
from .api.enrutador_principal import router_casos, router_chat
# Importamos las herramientas para forzar su inicializacion al arranque.
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
    version="1.0.0", # Actualizamos la version para reflejar nuestros cambios
    lifespan=lifespan
)

# Se mantiene la misma configuracion de CORS que ya tenias.
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

# --- CAMBIO CLAVE ---
# En lugar de incluir un solo router, ahora incluimos los dos que hemos definido.
# FastAPI gestionara los prefijos (/casos y /chat) que definimos en cada uno.
print("INFO: Registrando enrutadores de la API...")
aplicacion.include_router(router_casos)
aplicacion.include_router(router_chat)
print("-> Enrutadores de Casos y Chat registrados exitosamente.")

@aplicacion.get("/", tags=["Root"])
def leer_raiz():
    """
    Endpoint principal de bienvenida para verificar que la API esta en linea.
    """
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}