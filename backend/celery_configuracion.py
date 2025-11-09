# backend/celery_configuracion.py

from celery import Celery
import os

"""
Este archivo centraliza la configuración de la instancia de Celery para nuestra aplicación.
Ahora lee la URL de Redis desde la variable de entorno REDIS_URL.
"""

# --- Dirección del Broker y Backend (Redis) ---
# Lee la URL de Redis desde la variable de entorno
# Render proporciona esta variable con la URL completa del servicio Redis.
# El fallback 'redis://localhost:6379/0' es útil para desarrollo local si no se define la variable.
URL_BROKER_REDIS = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Para el backend, puedes usar la misma URL o una base de datos diferente si lo prefieres.
# Asegúrate de que la URL apunte a la base de datos correcta (ej., /1 en lugar de /0).
# Para simplicidad y coherencia, usaremos la misma URL base y dejaremos que Celery maneje la base de datos si es necesario,
# o puedes especificarla explícitamente como 'redis://...:6379/1' si es el caso.
URL_RESULTADO_REDIS = os.getenv("REDIS_URL", "redis://localhost:6379/0") # O '/1' si usas una base distinta para resultados

# --- Creación de la Instancia de la Aplicación Celery ---
celery_app = Celery(
    # El primer argumento es el nombre del "módulo" principal donde se definirán las tareas.
    # Le daremos este nombre por convención, lo crearemos más adelante.
    "tareas",
    
    # Le decimos a Celery dónde está nuestro broker.
    broker=URL_BROKER_REDIS,
    
    # Le decimos a Celery dónde guardar los resultados.
    backend=URL_RESULTADO_REDIS
)

# --- Configuración Adicional de Celery ---
# Estas son configuraciones opcionales pero muy recomendadas para un mejor seguimiento.
celery_app.conf.update(
    # Le dice a Celery que reporte el estado 'STARTED' cuando un worker empieza una tarea.
    # Es muy útil para saber que una tarea no solo está en cola, sino que ya se está procesando.
    task_track_started=True,
    
    # Guarda metadatos adicionales sobre el resultado de la tarea (como el worker que la ejecutó).
    result_extended=True,
)

# Opcional: Configuración adicional común
celery_app.conf.update(
    # Asegúrate de que los resultados se serialicen como JSON
    result_serializer='json',
    # Acepta contenido JSON
    accept_content=['json'],
    # Serializa también las tareas como JSON
    task_serializer='json',
    # Zona horaria
    timezone='UTC',
    # Habilitar UTC
    enable_utc=True,
)