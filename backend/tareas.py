# backend/tareas.py

from sqlmodel import Session, select
from .celery_configuracion import celery_app
from .base_de_datos import motor
from .api.modelos_compartidos import Evidencia
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo
import json # Importamos json para formatear los diccionarios

@celery_app.task
def procesar_evidencia_tarea(id_evidencia: int):
    """
    Tarea de Celery que orquesta el procesamiento de una evidencia.
    Esta version actualizada incluye los resultados del analisis multimodal
    en el reporte final.
    """
    print(f"Iniciando procesamiento para la evidencia con ID: {id_evidencia}")

    with Session(motor) as sesion:
        evidencia = sesion.get(Evidencia, id_evidencia)
        if not evidencia:
            print(f"Error critico: No se encontro la evidencia con ID {id_evidencia}")
            return

        # El estado inicial se mantiene igual, con los campos de resultados en None.
        estado_inicial: EstadoDelGrafo = {
            "id_caso": evidencia.id_caso,
            "rutas_archivos_evidencia": [evidencia.ruta_archivo],
            "resultado_triaje": None,
            "resultado_analisis_documento": None,
            "resultado_analisis_audio": None,
            "resultado_determinador_competencias": None,
            "resultado_repartidor": None,
            "solicitud_agente_juridico": "Cuales son los pasos a seguir segun el marco legal?",
            "solicitud_agente_documentos": {"tipo_documento": "derecho_de_peticion"},
            "resultado_agente_juridico": None,
            "resultado_agente_generador_documentos": None,
        }

        try:
            estado_final = grafo_compilado.invoke(estado_inicial)
            print("El grafo de LangGraph completo su ejecucion.")

            # --- ¡NUEVA LOGICA DE CONSTRUCCION DE REPORTE! ---
            
            # Extraemos los resultados de los nuevos agentes especializados.
            # Usamos .get() para no generar un error si el campo no existe.
            analisis_doc = estado_final.get('resultado_analisis_documento')
            analisis_audio = estado_final.get('resultado_analisis_audio')

            # Construimos el reporte final con etiquetas claras para el frontend.
            reporte_final = f"""
            [TRIAJE]
            {json.dumps(estado_final.get('resultado_triaje', {}), indent=2, ensure_ascii=False)}
            [/TRIAJE]

            [ANALISIS_DOCUMENTO]
            {json.dumps(analisis_doc, indent=2, ensure_ascii=False) if analisis_doc else 'No aplica'}
            [/ANALISIS_DOCUMENTO]

            [ANALISIS_AUDIO]
            {json.dumps(analisis_audio, indent=2, ensure_ascii=False) if analisis_audio else 'No aplica'}
            [/ANALISIS_AUDIO]

            [COMPETENCIA]
            {json.dumps(estado_final.get('resultado_determinador_competencias', {}), indent=2, ensure_ascii=False)}
            [/COMPETENCIA]

            [ASIGNACION]
            {json.dumps(estado_final.get('resultado_repartidor', {}), indent=2, ensure_ascii=False)}
            [/ASIGNACION]

            [ANALISIS_JURIDICO]
            {estado_final.get('resultado_agente_juridico', 'No aplica')}
            [/ANALISIS_JURIDICO]

            [DOCUMENTO_GENERADO]
            {estado_final.get('resultado_agente_generador_documentos', 'No aplica')}
            [/DOCUMENTO_GENERADO]
            """

            # Guardamos el reporte y actualizamos el estado.
            evidencia.estado = "completado"
            evidencia.reporte_analisis = reporte_final.strip()
            sesion.add(evidencia)
            sesion.commit()
            print(f"Evidencia {id_evidencia} marcada como 'completado' y reporte guardado.")

        except Exception as e:
            print(f"Error durante la ejecucion del grafo para evidencia {id_evidencia}: {e}")
            evidencia.estado = "error"
            evidencia.reporte_analisis = f"Ocurrio un error en el servidor: {str(e)}"
            sesion.add(evidencia)
            sesion.commit()