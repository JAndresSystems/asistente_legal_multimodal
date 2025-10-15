# backend/tareas.py

import json
from sqlmodel import Session
from .celery_configuracion import celery_app
from .base_de_datos import motor
from .api.modelos_compartidos import Evidencia, Caso
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

@celery_app.task
def procesar_evidencia_tarea(id_caso: int, texto_adicional_usuario: str = ""):
    """
    Docstring:
    Tarea de Celery que procesa un CASO COMPLETO, consciente de todas sus
    evidencias. El resultado del analisis se guarda en el propio objeto Caso.
    """
    print(f"Iniciando procesamiento consolidado para el CASO ID: {id_caso}")
    
    with Session(motor) as sesion:
        # Definimos 'caso' fuera del try para que este disponible en el except
        caso = None
        try:
            caso = sesion.get(Caso, id_caso)
            if not caso:
                raise Exception(f"No se pudo encontrar el Caso {id_caso}")

            # Marcamos todas las evidencias como 'procesando'
            for evidencia in caso.evidencias:
                evidencia.estado = "procesando"
                sesion.add(evidencia)
            sesion.commit()

            todas_las_rutas = [ev.ruta_archivo for ev in caso.evidencias]
            nombres_archivos = [ev.nombre_archivo for ev in caso.evidencias]
            print(f"El agente analizara un total de {len(todas_las_rutas)} evidencia(s) para el caso.")

            # Estado inicial completo, tal como estaba en su version original
            estado_inicial: EstadoDelGrafo = {
                "id_caso": id_caso,
                "rutas_archivos_evidencia": todas_las_rutas,
                "texto_adicional_usuario": texto_adicional_usuario,
                "solicitud_agente_juridico": (
                    "Realiza un analisis juridico inicial sobre el caso, identificando figuras legales, "
                    "pasos a seguir y fundamentando con normatividad."
                ),
                "resultado_triaje": None,
                "resultado_analisis_documento": None,
                "resultado_analisis_audio": None,
                "resultado_determinador_competencias": None,
                "resultado_repartidor": None,
                "resultado_agente_juridico": None,
            }

            estado_final = grafo_compilado.invoke(estado_inicial)
            print("El grafo de LangGraph completo su ejecucion.")

            # Incluimos la lista de archivos en el reporte
            archivos_analizados_str = "\n".join([f"- {nombre}" for nombre in nombres_archivos])
            reporte_final = f"""
            [ARCHIVOS_ANALIZADOS]
            {archivos_analizados_str}
            [/ARCHIVOS_ANALIZADOS]
            
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

            # Guardamos el reporte en el Caso y marcamos las evidencias como completadas
            caso.reporte_consolidado = reporte_final.strip()
            sesion.add(caso)
            for evidencia in caso.evidencias:
                evidencia.estado = "completado"
                sesion.add(evidencia)
            sesion.commit()
            print(f"Reporte consolidado guardado en el Caso {id_caso}.")

            return estado_final

        except Exception as e:
            print(f"Error durante la ejecucion del grafo para caso {id_caso}: {e}")
            if caso:
                caso.reporte_consolidado = f"[ERROR]\nError: {str(e)}\n[/ERROR]"
                sesion.add(caso)
                for evidencia in caso.evidencias:
                    evidencia.estado = "error"
                    sesion.add(evidencia)
                sesion.commit()
            return {"error": str(e)}