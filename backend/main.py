# backend/main.py

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# --- FUNCION LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("INFO: Iniciando la aplicación (dentro del lifespan)...")
    # Asumiendo que tienes este archivo para inicializar la base de datos
    from . import base_de_datos
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
    # Importar enrutadores específicos de roles
    from .api.enrutador_usuario import router as router_usuario
    from .api.enrutador_estudiante import router as router_estudiante
    # CORRECCIÓN AQUÍ: Importamos 'router_asesor' desde enrutador_asesor, no 'router'
    from .api.enrutador_asesor import router_asesor as router_asesor
    from .api.enrutador_administrador import router as router_administrador

    # Importar enrutadores generales
    from .api.enrutador_principal import router_chat, router_evidencias
    from .api.enrutador_autenticacion import router_auth
    # Opcional: Si enrutador_agentes tiene endpoints generales
    # from .api.enrutador_agentes import router as router_agentes

    # Registrar enrutadores generales
    aplicacion.include_router(router_auth, prefix="/api/auth", tags=["Autenticación"])
    aplicacion.include_router(router_chat, prefix="/api/chat", tags=["Chat"])
    # Cuidado con este prefijo si router_evidencias no debería estar bajo /api/casos
    # Si router_evidencias solo maneja operaciones CRUD de evidencia específica (como /{id}/estado),
    # quizás su prefijo debería ser "/api/evidencias". Asumiendo que es correcto según tu arquitectura.
    aplicacion.include_router(router_evidencias, prefix="/api/evidencias", tags=["Gestión de Evidencias"])
    # Si enrutador_agentes tiene endpoints generales, descomenta la siguiente línea.
    # aplicacion.include_router(router_agentes, prefix="/api/agentes", tags=["Agentes"])

    # Registrar enrutadores específicos de roles
    # El prefijo (e.g., /api/casos, /api/expedientes, /api/asesor, /api/administrador)
    # está definido DENTRO de cada archivo de enrutador correspondiente.
    aplicacion.include_router(router_usuario)      # -> Monta sus rutas bajo /api/casos
    aplicacion.include_router(router_estudiante)   # -> Monta sus rutas bajo /api/expedientes
    aplicacion.include_router(router_asesor)       # -> Monta sus rutas bajo /api/asesor
    aplicacion.include_router(router_administrador) # -> Monta sus rutas bajo /api/administrador

    print("-> Enrutadores registrados exitosamente.")

except ImportError as e:
    print(f"ERROR de importación al registrar routers: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"ERROR general al registrar routers: {e}")
    import traceback
    traceback.print_exc()

# --- HEALTH CHECK (Asumiendo que está en router_chat o es general) ---
# Ya está definido en enrutador_principal.py bajo /api/chat/healthcheck
# No es necesario duplicarlo aquí a menos que quieras un healthcheck en la raíz
# @aplicacion.get("/health", status_code=status.HTTP_200_OK)
# def health_check():
#     return {"status": "ok"}

# --- RUTA RAIZ (opcional) ---
@aplicacion.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la API del Asistente Legal Multimodal."}
