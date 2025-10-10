import json
from sqlmodel import Session
from .celery_configuracion import celery_app
from .base_de_datos import motor
from .api.modelos_compartidos import Evidencia
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

@celery_app.task
def procesar_evidencia_tarea(id_evidencia: int):
    print(f"Iniciando procesamiento para la evidencia con ID: {id_evidencia}")
    with Session(motor) as sesion:
        evidencia = sesion.get(Evidencia, id_evidencia)
        if not evidencia: return
        evidencia.estado = "procesando"; sesion.add(evidencia); sesion.commit()

        estado_inicial: EstadoDelGrafo = {
            "id_caso": evidencia.id_caso,
            "rutas_archivos_evidencia": [evidencia.ruta_archivo],
            "solicitud_agente_juridico": (
                "Realiza un analisis juridico inicial sobre el caso, identificando figuras legales, "
                "pasos a seguir y fundamentando con normatividad."
            ),
            "resultado_triaje": None, "resultado_analisis_documento": None, "resultado_analisis_audio": None,
            "resultado_determinador_competencias": None, "resultado_repartidor": None, "resultado_agente_juridico": None,
        }

        try:
            estado_final = grafo_compilado.invoke(estado_inicial)
            print("El grafo de LangGraph completo su ejecucion.")

            # --- LOGICA DE REPORTE FINAL Y DEFINITIVA ---
            reporte_final = f"""
            [TRIAJE]
            {json.dumps(estado_final.get('resultado_triaje', {}), indent=2, ensure_ascii=False)}
            [/TRIAJE]

            [ANALISIS_DOCUMENTO]
            {json.dumps(estado_final.get('resultado_analisis_documento'), indent=2, ensure_ascii=False) if estado_final.get('resultado_analisis_documento') else 'No aplica'}
            [/ANALISIS_DOCUMENTO]

            [ANALISIS_AUDIO]
            {json.dumps(estado_final.get('resultado_analisis_audio'), indent=2, ensure_ascii=False) if estado_final.get('resultado_analisis_audio') else 'No aplica'}
            [/ANALISIS_AUDIO]

            [COMPETENCIA]
            {json.dumps(estado_final.get('resultado_determinador_competencias', {}), indent=2, ensure_ascii=False)}
            [/COMPETENCIA]

            [ASIGNACION]
            {json.dumps(estado_final.get('resultado_repartidor', {}), indent=2, ensure_ascii=False)}
            [/ASIGNACION]

            [ANALISIS_JURIDICO_INICIAL]
            {estado_final.get('resultado_agente_juridico', 'No se genero un analisis juridico inicial.')}
            [/ANALISIS_JURIDICO_INICIAL]
            """

            evidencia.estado = "completado"
            evidencia.reporte_analisis = reporte_final.strip()
            sesion.add(evidencia); sesion.commit()
            print(f"Evidencia {id_evidencia} marcada como 'completado' y reporte guardado.")
        except Exception as e:
            print(f"Error durante la ejecucion del grafo para evidencia {id_evidencia}: {e}")
            evidencia.estado = "error"; evidencia.reporte_analisis = f"[ERROR]\nError: {str(e)}\n[/ERROR]"; sesion.add(evidencia); sesion.commit()