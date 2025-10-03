#backend\tareas.py

import uuid
from .celery_configuracion import celery_app
from .agentes.orquestador_del_grafo import grafo_compilado
from .base_de_datos import obtener_sesion
from .api.modelos_compartidos import Evidencia
from sqlmodel import Session

@celery_app.task(name="procesar_evidencia_principal")
def procesar_evidencia_tarea(id_evidencia_str: str):
    """
    Tarea de Celery que ejecuta la cadena completa de agentes (Triaje, Competencia, Reparto)
    y guarda un resumen completo de los resultados.
    """
    print(f"INFO: [CELERY-WORKER] Iniciando procesamiento con CADENA COMPLETA para evidencia: {id_evidencia_str}")
    
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
        
        historial_simulado = (
            f"El usuario ha iniciado un caso sobre '{evidencia_db.caso.titulo}' "
            f"y ha subido el archivo '{evidencia_db.nombre_archivo}'. "
            f"El resumen inicial es: '{evidencia_db.caso.resumen}'. "
            f"Por favor, iniciar el proceso de admisión."
        )
        
        estado_inicial = {
            "historial_conversacion": historial_simulado,
            "rutas_archivos_evidencia": [evidencia_db.ruta_archivo],
        }
        
        print(f"INFO: [CELERY-WORKER] Invocando el grafo de agentes completo...")
        estado_final = grafo_compilado.invoke(estado_inicial)
        print(f"INFO: [CELERY-WORKER] El grafo de agentes completo ha finalizado.")

        # --- RECOPILACIÓN Y GUARDADO DE TODOS LOS RESULTADOS ---
        es_admisible = estado_final.get("es_admisible")
        justificacion = estado_final.get("justificacion_triaje", "N/A")
        area_competencia = estado_final.get("area_competencia", "N/A")
        id_estudiante = estado_final.get("id_estudiante_asignado", "N/A")
        id_asesor = estado_final.get("id_asesor_asignado", "N/A")

        # Construimos un reporte completo para guardarlo en la base de datos.
        reporte_final = (
            f"--- REPORTE DE ADMISIÓN AUTOMÁTICA ---\n\n"
            f"VEREDICTO DEL TRIAJE: {'ADMISIBLE' if es_admisible else 'NO ADMISIBLE'}\n"
            f"Justificación: {justificacion}\n\n"
            f"--- CLASIFICACIÓN Y ASIGNACIÓN ---\n"
            f"Área de Competencia Determinada: {area_competencia}\n"
            f"Equipo Asignado (Simulado):\n"
            f"  - ID Estudiante: {id_estudiante}\n"
            f"  - ID Asesor: {id_asesor}\n"
        )
        
        evidencia_db.texto_extraido = reporte_final

        if es_admisible:
            evidencia_db.estado_procesamiento = "completado"
            print(f"INFO: [CELERY-WORKER] Caso ADMISIBLE y ASIGNADO. Reporte guardado.")
        else:
            evidencia_db.estado_procesamiento = "error_de_procesamiento"
            print(f"INFO: [CELERY-WORKER] Caso NO ADMISIBLE. Reporte guardado.")

        sesion.add(evidencia_db)
        sesion.commit()

    except Exception as e:
        print(f"ERROR-CRITICO: [CELERY-WORKER] Ocurrió una excepción en la tarea: {e}")
        if evidencia_db:
            evidencia_db.estado_procesamiento = "error_critico"
            sesion.add(evidencia_db)
            sesion.commit()
            
    finally:
        sesion.close()
        print(f"INFO: [CELERY-WORKER] Tarea finalizada para: {id_evidencia_str}")