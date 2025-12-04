# backend/tareas.py
import json
from sqlmodel import Session
from .api.modelos_compartidos import Caso, EstadoCaso
from .agentes.orquestador_del_grafo import grafo_compilado
from .agentes.estado_del_grafo import EstadoDelGrafo

def procesar_evidencia_sincrono(id_caso: int, texto_adicional_usuario: str, sesion: Session):
    """
    Función SÍNCRONA que procesa un CASO COMPLETO.
    MEJORA: 
    1. Preserva la descripción original si es sustancial.
    2. Combina texto del usuario de forma más inteligente, evitando reemplazos indebidos.
    3. Actualiza la descripción DESPUÉS del grafo si la IA genera un mejor resumen.
    """
    print(f"Iniciando procesamiento SÍNCRONO para el CASO ID: {id_caso}")
    
    caso = None
    try:
        caso = sesion.get(Caso, id_caso)
        if not caso:
            raise ValueError(f"No se pudo encontrar el Caso {id_caso}")

        # --- MEJORA DE PRESERVACIÓN Y COMBINACIÓN DE DESCRIPCIÓN ---
        descripcion_actual = caso.descripcion_hechos or ""
        texto_usuario = texto_adicional_usuario or ""
        
        # Definimos umbrales para considerar una descripción como "sustancial"
        umbral_descripcion_sustancial = 100 # Caracteres
        umbral_texto_usuario_significativo = 50 # Caracteres
        
        descripcion_para_estado = descripcion_actual # Valor por defecto
        
        # Si el usuario envía texto nuevo
        if texto_usuario.strip():
            texto_limpio_usuario = texto_usuario.strip()
            
            # Verificamos si el texto del usuario es sustancial (describe hechos, no solo pregunta)
            es_texto_usuario_sustancial = len(texto_limpio_usuario) >= umbral_texto_usuario_significativo
            
            # Verificamos si la descripción actual ya es sustancial
            es_descripcion_actual_sustancial = len(descripcion_actual.strip()) >= umbral_descripcion_sustancial
            
            if es_descripcion_actual_sustancial:
                # La descripción original es valiosa
                if es_texto_usuario_sustancial:
                    # Si el nuevo texto también es sustancial y no está ya en la descripción
                    if texto_limpio_usuario not in descripcion_actual:
                        print(f"--- [TAREAS] (PROCESO) Descripción sustancial existente. Combinando nuevo texto sustancial del usuario.")
                        descripcion_para_estado = descripcion_actual + "\n\nInformación adicional del usuario: " + texto_limpio_usuario
                        # Actualizamos la descripción en la base de datos si cambió
                        if descripcion_para_estado != descripcion_actual:
                            caso.descripcion_hechos = descripcion_para_estado
                            sesion.add(caso)
                            sesion.commit()
                            sesion.refresh(caso)
                    else:
                        print(f"--- [TAREAS] (PROCESO) Nuevo texto del usuario ya estaba en la descripción. Manteniendo actual.")
                else:
                    # El texto del usuario es corto (posiblemente una pregunta o afirmación breve)
                    # No lo combinamos con la descripción principal, pero puede ser útil para el historial
                    print(f"--- [TAREAS] (PROCESO) Texto del usuario corto. Manteniendo descripción original.")
                    # No actualizamos la descripción de hechos en este caso
            else:
                # La descripción actual no es sustancial (vacía, genérica o muy corta)
                if es_texto_usuario_sustancial:
                    # Reemplazamos la descripción con el texto sustancial del usuario
                    print(f"--- [TAREAS] (PROCESO) Descripción original no sustancial. Reemplazando con texto sustancial del usuario.")
                    descripcion_para_estado = texto_limpio_usuario
                    caso.descripcion_hechos = descripcion_para_estado
                    sesion.add(caso)
                    sesion.commit()
                    sesion.refresh(caso)
                else:
                    # Ambos son cortos. Mantenemos el existente o lo actualizamos si es diferente.
                    # Si la descripción actual es vacía o genérica, actualizamos.
                    if not descripcion_actual.strip() or "Inicio de registro" in descripcion_actual:
                         print(f"--- [TAREAS] (PROCESO) Descripción original vacía o genérica. Actualizando con texto del usuario (aunque corto).")
                         descripcion_para_estado = texto_limpio_usuario
                         caso.descripcion_hechos = descripcion_para_estado
                         sesion.add(caso)
                         sesion.commit()
                         sesion.refresh(caso)
                    else:
                        # Ambos son cortos, pero la descripción tiene algo. La dejamos como está.
                        print(f"--- [TAREAS] (PROCESO) Ambos textos cortos, manteniendo descripción original.")
        # Si no hay texto de usuario, simplemente usamos la descripción actual
        else:
            print(f"--- [TAREAS] (PROCESO) No hay texto adicional del usuario. Usando descripción existente.")
        
        # Actualizamos la variable que usaremos para el estado del grafo
        descripcion_para_estado = caso.descripcion_hechos # Refrescamos por si hubo cambios en la BD
        
        # -----------------------------------------------------------------

        # 1. Cargar la memoria a largo plazo desde la base de datos
        inventario_existente = caso.inventario_documentos or []
        historial_existente = caso.historial_conversacion or []
        rutas_archivos = [ev.ruta_archivo for ev in caso.evidencias]
        
        # 2. Construir el estado inicial para el grafo
        estado_inicial = {
            "id_caso": id_caso,
            "descripcion_hechos": descripcion_para_estado, # <-- Usamos la descripción ya procesada
            "rutas_archivos_evidencia": rutas_archivos,
            "inventario_documentos": inventario_existente,
            "historial_chat": historial_existente
        }
        
        # Añadimos el mensaje actual del usuario al historial del grafo *si existe*
        if texto_usuario:
            estado_inicial["historial_chat"].append({
                "autor": "usuario",
                "texto": texto_usuario
            })

        print(f"CONTEXTO: Pasando descripción ({len(descripcion_para_estado)} chars) y {len(rutas_archivos)} archivos.")
        
        # 3. Invocar el grafo
        estado_final = grafo_compilado.invoke(estado_inicial)
        print("El grafo de LangGraph completó su ejecución.")

        # 4. Actualizar la base de datos con los resultados
        reporte_dict = {
            "TRIEJE": estado_final.get('resultado_triaje'),
            "COMPETENCIA": estado_final.get('resultado_determinador_competencias'),
            "ASIGNACION": estado_final.get('resultado_repartidor'),
        }
        
        reporte_dict_limpio = {k: v for k, v in reporte_dict.items() if v is not None}
        caso.reporte_consolidado = json.dumps(reporte_dict_limpio, indent=2, ensure_ascii=False)
        
        # Guardamos la memoria conversacional actualizada
        caso.inventario_documentos = estado_final.get("inventario_documentos", inventario_existente)
        caso.historial_conversacion = estado_final.get("historial_chat", historial_existente)
        print(f"MEMORIA: Guardando {len(caso.historial_conversacion)} mensajes en la BD.")

        # Lógica de Estado y Refinamiento Final
        resultado_triaje = estado_final.get('resultado_triaje', {})
        decision = resultado_triaje.get('decision_triaje')
        
        if decision == "NO_ADMISSIBLE":
            caso.estado = EstadoCaso.RECHAZADO
            caso.justificacion_rechazo = resultado_triaje.get("justificacion", "No cumple requisitos.")
            
        elif decision == "ADMISSIBLE" or estado_final.get('resultado_repartidor'):
            caso.estado = EstadoCaso.PENDIENTE_ACEPTACION
            
            # --- REFINAMIENTO (Post-Procesamiento) ---
            # Si la IA generó un resumen estructurado ("hechos_clave") que es mejor 
            # que lo que escribió el usuario, actualizamos la descripción final.
            hechos_clave = resultado_triaje.get("hechos_clave")
            if hechos_clave and len(hechos_clave) > 20:
                print(f"--- [TAREAS] Refinando descripción del caso con resumen estructurado de IA.")
                caso.descripcion_hechos = hechos_clave
            # -----------------------------------------
        
        sesion.add(caso)
        sesion.commit()
        sesion.refresh(caso) 
        print(f"Reporte, estado y MEMORIA actualizados en el Caso {id_caso}.")

        # 5. Devolver el estado final para que la API pueda responder
        return estado_final

    except Exception as e:
        print(f"ERROR CRITICO en el procesamiento síncrono para caso {id_caso}: {e}")
        if caso:
            caso.reporte_consolidado = json.dumps({"error": str(e)})
            caso.estado = EstadoCaso.CERRADO
            sesion.add(caso)
            sesion.commit()
        raise e