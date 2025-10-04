#backend\tareas.py

import uuid
from .celery_configuracion import celery_app
from .agentes.orquestador_del_grafo import grafo_compilado
from .base_de_datos import obtener_sesion
from .api.modelos_compartidos import Evidencia
from sqlmodel import Session

@celery_app.task(name="procesar_evidencia_principal")
def procesar_evidencia_tarea(id_evidencia_str: str):
    print(f"INFO: [CELERY-WORKER] Iniciando procesamiento con RAG para evidencia: {id_evidencia_str}")
    
    db_session_gen = obtener_sesion()
    sesion: Session = next(db_session_gen)
    id_evidencia = uuid.UUID(id_evidencia_str)
    evidencia_db = None

    try:
        evidencia_db = sesion.get(Evidencia, id_evidencia)
        if not evidencia_db: return
            
        evidencia_db.estado_procesamiento = "procesando"
        sesion.add(evidencia_db)
        sesion.commit()
        
        historial_simulado = (
            f"El usuario ha iniciado un caso sobre '{evidencia_db.caso.titulo}' y ha subido el archivo "
            f"'{evidencia_db.nombre_archivo}'. El resumen es: '{evidencia_db.caso.resumen}'."
        )
        pregunta_juridica_simulada = (
            "¿Cuáles son los elementos esenciales de un contrato de arrendamiento "
            "según el código civil colombiano?"
        )

        estado_inicial = {
            "historial_conversacion": historial_simulado,
            "rutas_archivos_evidencia": [evidencia_db.ruta_archivo],
            "consulta_juridica_actual": pregunta_juridica_simulada,
        }
        
        print(f"INFO: [CELERY-WORKER] Invocando grafo con consulta RAG: '{pregunta_juridica_simulada}'")
        estado_final = grafo_compilado.invoke(estado_inicial)
        print(f"INFO: [CELERY-WORKER] El grafo de agentes con RAG ha finalizado.")

        es_admisible = estado_final.get("es_admisible")
        justificacion = estado_final.get("justificacion_triaje", "N/A")
        area_competencia = estado_final.get("area_competencia", "N/A")
        id_estudiante = estado_final.get("id_estudiante_asignado", "N/A")
        id_asesor = estado_final.get("id_asesor_asignado", "N/A")
        respuesta_juridica = estado_final.get("respuesta_juridica", "El Agente Jurídico no generó respuesta.")

        # --- CAMBIO CLAVE: AJUSTAMOS EL FORMATO DEL REPORTE ---
        # Ahora las etiquetas coinciden exactamente con las que busca el componente ReporteAdmision.jsx
        reporte_final = (
            f"--- REPORTE DE ADMISIÓN AUTOMÁTICA ---\n\n"
            f"VEREDICTO DEL TRIAJE: { 'ADMISIBLE' if es_admisible else 'NO ADMISIBLE' }\n"
            f"Justificación: {justificacion}\n\n"
            f"--- CLASIFICACIÓN Y ASIGNACIÓN ---\n"
            f"Área de Competencia Determinada: {area_competencia}\n"
            f"Equipo Asignado (Simulado):\n"
            f"  - ID Estudiante: {id_estudiante}\n"
            f"  - ID Asesor: {id_asesor}\n\n"
            f"--- CONSULTA JURÍDICA (RAG) ---\n"
            f"Pregunta: {pregunta_juridica_simulada}\n"
            f"Respuesta del Agente Jurídico:\n{respuesta_juridica}"
        )
        
        evidencia_db.texto_extraido = reporte_final
        evidencia_db.estado_procesamiento = "completado" if es_admisible else "error_de_procesamiento"

        sesion.add(evidencia_db)
        sesion.commit()

    except Exception as e:
        print(f"ERROR-CRITICO: [CELERY-WORKER] Ocurrió una excepción en la tarea: {e}")
            
    finally:
        sesion.close()
        print(f"INFO: [CELERY-WORKER] Tarea finalizada para: {id_evidencia_str}")