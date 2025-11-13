# backend/celery_configuracion.py

from celery import Celery

"""
Este archivo centraliza la configuración de la instancia de Celery para nuestra aplicación.
"""

# --- Dirección del Broker (Redis) ---
# Esta es la "dirección" donde nuestro broker Redis está escuchando.
# Celery se conectará aquí para enviar y recibir mensajes de tareas.
# El '/0' al final se refiere a la base de datos número 0 dentro de Redis, que es la predeterminada.
URL_BROKER_REDIS = "redis://localhost:6379/0"

# --- Dirección del Backend de Resultados (Redis) ---
# Aquí es donde Celery almacenará los resultados de las tareas que se han ejecutado.
# Usamos la base de datos número 1 ('/1') para mantener los resultados separados de la cola de tareas.
URL_RESULTADO_REDIS = "redis://localhost:6379/1"


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