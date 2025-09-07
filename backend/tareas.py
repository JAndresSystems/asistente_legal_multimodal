# backend/tareas.py

import uuid
from .celery_configuracion import celery_app
from .agentes.orquestador_del_grafo import grafo_compilado
from .base_de_datos import obtener_sesion
from .api.modelos_compartidos import Evidencia
from sqlmodel import Session

@celery_app.task(name="procesar_evidencia_principal")
def procesar_evidencia_tarea(id_evidencia_str: str):
    """
    Tarea de Celery que se ejecuta en segundo plano para procesar un archivo de evidencia.
    VERSIÓN CORREGIDA Y ROBUSTA FINAL.
    """
    print(f"INFO: [CELERY-WORKER] Iniciando procesamiento para la evidencia: {id_evidencia_str}")
    
    db_session_gen = obtener_sesion()
    sesion: Session = next(db_session_gen)
    id_evidencia = uuid.UUID(id_evidencia_str)
    evidencia_db = None

    try:
        evidencia_db = sesion.get(Evidencia, id_evidencia)
        if not evidencia_db:
            print(f"ERROR: [CELERY-WORKER] No se encontró la evidencia con ID: {id_evidencia_str}")
            return
            
        evidencia_db.estado_procesamiento = "procesando"
        sesion.add(evidencia_db)
        sesion.commit()
        
        estado_inicial = {
            "id_caso": str(evidencia_db.id_caso),
            "ruta_archivo": evidencia_db.ruta_archivo,
            "tipo_contenido": evidencia_db.tipo_contenido,
            "intentos_correccion": 0
        }
        
        print(f"INFO: [CELERY-WORKER] Invocando el grafo de agentes para: {evidencia_db.nombre_archivo}")
        estado_final = grafo_compilado.invoke(estado_inicial)
        print(f"INFO: [CELERY-WORKER] El grafo de agentes ha completado el análisis.")

        # --- LÓGICA DE ACTUALIZACIÓN FINAL Y SEGURA ---
        # La única fuente de verdad es el contenido de 'texto_extraido'.

        texto_resultado = estado_final.get("texto_extraido")

        if texto_resultado and texto_resultado.startswith("Error"):
            # CASO 1: EL PROCESAMIENTO INICIAL FALLÓ
            print(f"ERROR: [CELERY-WORKER] El procesamiento falló. Guardando estado de error.")
            evidencia_db.texto_extraido = texto_resultado
            evidencia_db.estado_procesamiento = "error_de_procesamiento"
            # Nos aseguramos de que los otros campos estén vacíos para no guardar basura
            evidencia_db.entidades_extraidas = []
            evidencia_db.informacion_recuperada = []
            evidencia_db.borrador_estrategia = None
            evidencia_db.verificacion_calidad = None
        
        elif texto_resultado:
            # CASO 2: EL PROCESAMIENTO FUE EXITOSO
            print(f"INFO: [CELERY-WORKER] Procesamiento exitoso. Guardando todos los resultados.")
            evidencia_db.texto_extraido = texto_resultado
            evidencia_db.entidades_extraidas = estado_final.get("entidades_extraidas")
            evidencia_db.informacion_recuperada = estado_final.get("informacion_recuperada")
            evidencia_db.borrador_estrategia = estado_final.get("borrador_estrategia")
            evidencia_db.verificacion_calidad = estado_final.get("verificacion_calidad")
            evidencia_db.estado_procesamiento = "completado"

        else:
            # CASO 3: UN ERROR INESPERADO DONDE NO HAY TEXTO
            print(f"ERROR: [CELERY-WORKER] Error inesperado, no se produjo texto. Marcando como error.")
            evidencia_db.estado_procesamiento = "error_inesperado"

        sesion.add(evidencia_db)
        sesion.commit()

    except Exception as e:
        print(f"ERROR-CRITICO: [CELERY-WORKER] Ocurrió una excepción procesando {id_evidencia_str}: {e}")
        if evidencia_db:
            evidencia_db.estado_procesamiento = "error_critico"
            sesion.add(evidencia_db)
            sesion.commit()
            
    finally:
        sesion.close()
        print(f"INFO: [CELERY-WORKER] Tarea finalizada y sesión de BD cerrada para: {id_evidencia_str}")