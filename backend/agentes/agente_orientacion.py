# Ubicación: backend/agentes/agente_orientacion.py

import json
from typing import List, Dict, Any
from ..herramientas.herramienta_rag import buscar_en_base_de_conocimiento
from ..herramientas.herramientas_lenguaje import generar_respuesta_texto

def _formatear_historial(historial: List[Dict[str, Any]]) -> str:
    if not historial: return "No hay conversación reciente."
    txt = ""
    for msg in historial:
        rol = "Usuario" if msg.get("autor") == "usuario" else "Orientador"
        txt += f"{rol}: {msg.get('texto')}\n"
    return txt

def invocar_agente_orientacion(caso_db: Any, pregunta_usuario: str) -> Dict[str, Any]:
    """
    Agente de Orientación con capacidad de ESCALAMIENTO.
    """
    print(f"\n--- [AGENTE ORIENTACION] Atendiendo consulta sobre Caso #{caso_db.id} ---")

    # 1. Memoria del Caso
    resumen_caso = f"""
    ID CASO: {caso_db.id}
    ESTADO ACTUAL: {caso_db.estado}
    HECHOS DEL CASO: {caso_db.descripcion_hechos}
    FECHA CREACIÓN: {caso_db.fecha_creacion}
    """
    if caso_db.reporte_consolidado:
        try:
            reporte = json.loads(caso_db.reporte_consolidado)
            if "TRIEJE" in reporte:
                resumen_caso += f"\nDECISIÓN TRIAJE: {reporte['TRIEJE'].get('decision_triaje')}"
            if "ASIGNACION" in reporte:
                resumen_caso += f"\nASIGNACIÓN: {reporte['ASIGNACION']}"
        except: pass

    # 2. Contexto Legal (RAG)
    try:
        docs = buscar_en_base_de_conocimiento(consulta=pregunta_usuario, n_resultados=3)
        contexto_legal = "\n".join(docs)
    except:
        contexto_legal = "No disponible."

    # 3. Prompt con Lógica de Escalamiento
    prompt = f"""
    Eres el "Agente de Orientación" del Consultorio Jurídico.
    
    --- DATOS DEL CASO ---
    {resumen_caso}
    --- CONTEXTO LEGAL ---
    {contexto_legal}
    --- HISTORIAL ---
    {_formatear_historial(caso_db.historial_conversacion)[-2000:]} 

    PREGUNTA DEL USUARIO: "{pregunta_usuario}"

    INSTRUCCIONES CRÍTICAS:
    1. Responde de forma empática usando los datos del caso.
    2. **DETECCIÓN DE ALERTAS:** Si el usuario expresa frustración grave, pide cambio de estudiante/asesor, o se queja de que "nadie responde", DEBES activar la bandera de escalamiento.
    3. Si activas la alerta, dile al usuario que has notificado a la administración.

    FORMATO JSON OBLIGATORIO:
    {{
        "respuesta_texto": "Tu respuesta aquí...",
        "escalar_a_admin": true/false,
        "motivo_alerta": "Resumen muy breve de la queja (solo si escalar es true, sino string vacío)"
    }}
    """

    # 4. Generación
    try:
        respuesta_cruda = generar_respuesta_texto(prompt)
        
        # Limpieza y Parseo
        respuesta_cruda = respuesta_cruda.replace("```json", "").replace("```", "").strip()
        inicio = respuesta_cruda.find('{')
        fin = respuesta_cruda.rfind('}')
        
        if inicio != -1 and fin != -1:
            return json.loads(respuesta_cruda[inicio:fin+1])
        
        return {
            "respuesta_texto": respuesta_cruda,
            "escalar_a_admin": False,
            "motivo_alerta": ""
        }

    except Exception as e:
        print(f"--- [AGENTE ORIENTACION] Error: {e}")
        return {
            "respuesta_texto": "Lo siento, estoy teniendo dificultades técnicas momentáneas.",
            "escalar_a_admin": False,
            "motivo_alerta": ""
        }