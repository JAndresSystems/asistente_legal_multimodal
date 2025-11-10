from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# --- FUNCION LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO: Iniciando la aplicación (dentro del lifespan)...")
    from . import base_de_datos  # Asumiendo que tienes este archivo
    base_de_datos.inicializar_base_de_datos()
    yield
    print("INFO: Apagando la aplicación...")

# --- CREACION DE LA APLICACION FASTAPI ---
aplicacion = FastAPI(
    title="API del Asistente Legal Multimodal",
    description="Proyecto de grado para gestionar y analizar evidencia legal con agentes de IA.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CONFIGURACION DE CORS ---
origenes_cors_raw = os.getenv("CORS_ORIGINS", "")
if origenes_cors_raw:
    origenes_permitidos = [orig.strip() for orig in origenes_cors_raw.split(",")]
else:
    origenes_permitidos = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
print(f"DEBUG: Orígenes CORS configurados: {origenes_permitidos}")

aplicacion.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REGISTRO DE ENRUTADORES ---
print("INFO: Registrando enrutadores de la API...")
try:
    from .api.enrutador_principal import router_chat, router_evidencias
    from .api.enrutador_autenticacion import router_auth
    # ... importa otros enrutadores ...
    aplicacion.include_router(router_auth, prefix="/api/auth", tags=["Autenticación"])
    aplicacion.include_router(router_chat, prefix="/api/chat", tags=["Chat"])
    aplicacion.include_router(router_evidencias, prefix="/api/casos", tags=["Casos"])
    # ... otros include_router ...
    print("-> Enrutadores registrados exitosamente.")
except Exception as e:
    print(f"ERROR al registrar routers: {e}")

# --- HEALTH CHECK (MOVIDO A RAÍZ PARA DEPURAR 404) ---
@aplicacion.get("/api/chat/healthcheck", status_code=status.HTTP_200_OK)
def health_check():
    print("DEBUG: Healthcheck llamado - respondiendo OK")  # Log para verificar si se ejecuta
    return {"status": "ok"}

# --- RUTA RAIZ (opcional) ---
@aplicacion.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}