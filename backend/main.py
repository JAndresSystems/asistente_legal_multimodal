# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# --- Cambios para la Base de Datos ---
# 1. Importamos la función que crea las tablas.
from . import base_de_datos
# 2. Renombramos el import del enrutador para que coincida con el nuevo nombre de archivo de los modelos.
from .api import enrutador_principal
# ------------------------------------

# Creamos un "evento" que se ejecuta al iniciar la aplicación.
# Esto asegura que las tablas de la base de datos se creen (si no existen)
# justo cuando el servidor arranca.
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Iniciando la aplicación...")
    base_de_datos.inicializar_base_de_datos()
    yield
    print("INFO:     Apagando la aplicación...")

aplicacion = FastAPI(
    title="API del Asistente Legal Multimodal",
    description="Proyecto de grado para gestionar y analizar evidencia legal con agentes de IA.",
    version="0.1.0",
    lifespan=lifespan # FastAPI usa  evento de inicio.
)

origenes_permitidos = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

aplicacion.include_router(enrutador_principal.router)