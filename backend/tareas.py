# backend/tareas.py

import json
from sqlmodel import Session
from .celery_configuracion import celery_app
from .base_de_datos import motor
from .api.modelos_compartidos import Caso, EstadoCaso
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

@celery_app.task
def procesar_evidencia_tarea(id_caso: int, texto_adicional_usuario: str = ""):
    """
    Docstring:
    Tarea de Celery que procesa un CASO COMPLETO y guarda el resultado
    del análisis como un JSON en el objeto Caso.
    """
    print(f"Iniciando procesamiento consolidado para el CASO ID: {id_caso}")
    
    with Session(motor) as sesion:
        caso = None
        try:
            caso = sesion.get(Caso, id_caso)
            if not caso:
                raise Exception(f"No se pudo encontrar el Caso {id_caso}")

            # Preparamos la entrada para el grafo de LangGraph
            rutas_archivos = [ev.ruta_archivo for ev in caso.evidencias]
            estado_inicial = {
                "id_caso": id_caso,
                "rutas_archivos_evidencia": rutas_archivos,
                "texto_adicional_usuario": texto_adicional_usuario,
            }

            # Invocamos a los agentes
            print(f"El agente analizara un total de {len(rutas_archivos)} evidencia(s).")
            estado_final = grafo_compilado.invoke(estado_inicial)
            print("El grafo de LangGraph completo su ejecucion.")

            # ==============================================================================
            # INICIO DE LA CORRECCION: Construimos un diccionario y lo convertimos a JSON
            # ==============================================================================
            reporte_dict = {
                "TRIEJE": estado_final.get('resultado_triaje'),
                "COMPETENCIA": estado_final.get('resultado_determinador_competencias'),
                "ASIGNACION": estado_final.get('resultado_repartidor'),
                "ANALISIS_DOCUMENTO": estado_final.get('resultado_analisis_documento'),
                "ANALISIS_AUDIO": estado_final.get('resultado_analisis_audio'),
                "ANALISIS_JURIDICO": estado_final.get('resultado_agente_juridico'),
            }
            
            # Filtramos las claves cuyo valor sea None para un reporte más limpio
            reporte_dict_limpio = {k: v for k, v in reporte_dict.items() if v is not None}
            
            # Convertimos el diccionario a un string JSON con formato legible
            caso.reporte_consolidado = json.dumps(reporte_dict_limpio, indent=2, ensure_ascii=False)
            # ==============================================================================
            # FIN DE LA CORRECCION
            # ==============================================================================
            
            # Actualizamos el estado del caso basado en el resultado de los agentes
            resultado_triaje = estado_final.get('resultado_triaje', {})
            if resultado_triaje.get('admisible') is False:
                caso.estado = EstadoCaso.RECHAZADO
            elif estado_final.get('resultado_repartidor'):
                # Si el repartidor corrió, el estado correcto es 'pendiente_aceptacion',
                # que ya fue establecido por el nodo. Aquí lo confirmamos.
                caso.estado = EstadoCaso.PENDIENTE_ACEPTACION
            
            sesion.add(caso)
            sesion.commit()
            print(f"Reporte consolidado y estado actualizados en el Caso {id_caso}.")
            
            return estado_final

        except Exception as e:
            print(f"ERROR CRITICO en la tarea Celery para caso {id_caso}: {e}")
            if caso:
                caso.reporte_consolidado = json.dumps({"error": str(e)})
                caso.estado = EstadoCaso.CERRADO # O un nuevo estado "con_error"
                sesion.add(caso)
                sesion.commit()
            return {"error": str(e)}