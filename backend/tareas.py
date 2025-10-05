# backend/tareas.py

from sqlmodel import Session, select
# CAMBIO CLAVE: Se corrige la importacion a relativa (se añade un punto).
# Esto le dice a Python que busque 'celery_configuracion.py' en la misma carpeta que este archivo.
from .celery_configuracion import celery_app
from .base_de_datos import motor
from .api.modelos_compartidos import Evidencia
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

@celery_app.task
def procesar_evidencia_tarea(id_evidencia: int):
    """
    Tarea de Celery que orquesta el procesamiento de una evidencia en segundo plano.

    Esta funcion es el punto de entrada al nucleo de IA del sistema.
    Su mision es:
    1. Recuperar la informacion de la evidencia desde la base de datos.
    2. Preparar el "expediente digital" inicial (EstadoDelGrafo).
    3. Invocar el grafo de LangGraph para que los agentes hagan su trabajo.
    4. Recibir el resultado final del grafo.
    5. Construir un reporte y guardarlo en la base de datos, actualizando el estado.

    Args:
        id_evidencia (int): El ID de la evidencia que se debe procesar.
    """
    print(f"Iniciando procesamiento para la evidencia con ID: {id_evidencia}")

    with Session(motor) as sesion:
        # Paso 1: Recuperar la evidencia de la BD.
        declaracion = select(Evidencia).where(Evidencia.id == id_evidencia)
        evidencia = sesion.exec(declaracion).one_or_none()

        if not evidencia:
            print(f"Error critico: No se encontro la evidencia con ID {id_evidencia}")
            return

        # Paso 2: Construir el estado_inicial para el grafo.
        estado_inicial: EstadoDelGrafo = {
            "id_caso": evidencia.id_caso,
            "rutas_archivos_evidencia": [evidencia.ruta_archivo],
            "solicitud_agente_juridico": "Basado en la evidencia, cual es el marco legal aplicable y los pasos a seguir?",
            "solicitud_agente_documentos": {"tipo_documento": "derecho_de_peticion"},
            "resultado_triaje": None,
            "resultado_determinador_competencias": None,
            "resultado_repartidor": None,
            "resultado_agente_juridico": None,
            "resultado_agente_generador_documentos": None,
        }

        print("Estado inicial para el grafo construido exitosamente.")
        print(estado_inicial)

        try:
            # Paso 3: Invocar el grafo compilado.
            estado_final = grafo_compilado.invoke(estado_inicial)
            print("El grafo de LangGraph completo su ejecucion.")
            print("Estado Final recibido:")
            print(estado_final)

            # Paso 4: Construir el reporte_final a partir del estado_final.
            reporte_final = f"""
            --- REPORTE DE ADMISION Y ANALISIS PRELIMINAR ---

            [CASO_ID]
            {estado_final.get('id_caso', 'No disponible')}
            [/CASO_ID]

            [TRIAJE]
            {estado_final.get('resultado_triaje', 'No ejecutado')}
            [/TRIAJE]

            [COMPETENCIA]
            {estado_final.get('resultado_determinador_competencias', 'No ejecutado')}
            [/COMPETENCIA]

            [ASIGNACION]
            {estado_final.get('resultado_repartidor', 'No ejecutado')}
            [/ASIGNACION]

            [ANALISIS_JURIDICO]
            {estado_final.get('resultado_agente_juridico', 'No ejecutado')}
            [/ANALISIS_JURIDICO]

            [DOCUMENTO_GENERADO]
            {estado_final.get('resultado_agente_generador_documentos', 'No ejecutado')}
            [/DOCUMENTO_GENERADO]
            """

            # Paso 5: Guardar el reporte y actualizar el estado de la evidencia.
            evidencia.estado = "completado"
            evidencia.reporte_analisis = reporte_final.strip()
            sesion.add(evidencia)
            sesion.commit()
            print(f"Evidencia {id_evidencia} marcada como 'completado' y reporte guardado.")

        except Exception as e:
            # En caso de un error en el grafo, lo registramos y actualizamos el estado.
            print(f"Error durante la ejecucion del grafo para evidencia {id_evidencia}: {e}")
            evidencia.estado = "error"
            evidencia.reporte_analisis = f"Ocurrio un error en el servidor al procesar la evidencia: {str(e)}"
            sesion.add(evidencia)
            sesion.commit()