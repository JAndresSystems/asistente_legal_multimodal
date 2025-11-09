# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os # Asegúrate de importar os
# ... (otros imports) ...

# --- FUNCION LIFESPAN (si la tienes) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO:     Iniciando la aplicación (dentro del lifespan)...")
    # Aquí puedes poner tu lógica de inicialización (BD, modelos, etc.)
    from . import base_de_datos # Asumiendo que tienes este archivo
    base_de_datos.inicializar_base_de_datos()
    yield
    print("INFO:     Apagando la aplicación...")

# --- CREACION DE LA APLICACION FASTAPI ---
aplicacion = FastAPI(
    title="API del Asistente Legal Multimodal",
    description="Proyecto de grado para gestionar y analizar evidencia legal con agentes de IA.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CONFIGURACION DE CORS ---
# Lee la variable de entorno CORS_ORIGINS
origenes_cors_raw = os.getenv("CORS_ORIGINS", "")
# Divídela por comas si está definida
if origenes_cors_raw:
    # Elimina espacios en blanco alrededor de cada origen
    origenes_permitidos = [orig.strip() for orig in origenes_cors_raw.split(",")]
else:
    # Fallback por si la variable no está definida (solo desarrollo local)
    origenes_permitidos = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

print(f"DEBUG: Orígenes CORS configurados: {origenes_permitidos}") # Línea de debug opcional, puedes quitarla luego

aplicacion.add_middleware(
    CORSMiddleware,
    # USAMOS la lista de orígenes leída desde la variable de entorno
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"], # O restringe a ["GET", "POST", "PUT", "DELETE"] si lo prefieres
    allow_headers=["*"], # O restringe si lo prefieres
)

# --- REGISTRO DE ENRUTADORES ---
print("INFO: Registrando enrutadores de la API...")
from .api.enrutador_principal import router_chat, router_evidencias
from .api.enrutador_autenticacion import router_auth
# ... importa otros enrutadores ...
# Asumiendo prefijos
aplicacion.include_router(router_auth, prefix="/api/auth", tags=["Autenticación"])
aplicacion.include_router(router_chat, prefix="/api/chat", tags=["Chat"])
aplicacion.include_router(router_evidencias, prefix="/api/casos", tags=["Casos"])
# ... otros include_router ...

print("-> Enrutadores registrados exitosamente.")

# --- RUTA RAIZ (opcional) ---
@aplicacion.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}