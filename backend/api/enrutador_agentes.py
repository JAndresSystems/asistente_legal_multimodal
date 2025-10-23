# backend/api/enrutador_agentes.py
from ..api.modelos_compartidos import Cuenta, Caso 
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from pydantic import BaseModel

from ..seguridad.jwt_manager import obtener_cuenta_actual
from ..api.modelos_compartidos import Cuenta
from ..base_de_datos import obtener_sesion

#  nodo del agente y la definicion de su estado.
from ..agentes.nodos_del_grafo import nodo_agente_juridico
from ..agentes.estado_del_grafo import EstadoDelGrafo

# --- MODELOS DE DATOS PARA ESTE ENRUTADOR ---
# Definen la estructura de las peticiones y respuestas para los agentes.

class SolicitudConsultaAgente(BaseModel):
    # El frontend nos dira sobre que caso se hace la pregunta.
    id_caso: int 
    pregunta: str

class RespuestaAgente(BaseModel):
    # La respuesta del agente sera estructurada.
    contenido: str
    fuentes: list[str]

# --- CONFIGURACION DEL ENRUTADOR ---

router_agentes = APIRouter(
    prefix="/agentes",
    tags=["Agentes Auxiliares (IA)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)

# --- ENDPOINT DE CONSULTA AL AGENTE JURIDICO ---

@router_agentes.post("/consulta-juridica", response_model=RespuestaAgente)
def consultar_agente_juridico(
    solicitud: SolicitudConsultaAgente,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Endpoint para que un estudiante realice una consulta al Agente Juridico.
    Ahora busca el contexto del caso antes de invocar al agente.
    """
    if cuenta_actual.rol != "estudiante":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="...")

    # --- INICIO DE LA MODIFICACION: Añadimos contexto del caso ---
    print(f"--- [API /consulta-juridica] Buscando contexto para caso {solicitud.id_caso}...")
    caso = sesion.get(Caso, solicitud.id_caso)
    if not caso:
        raise HTTPException(status_code=404, detail="El caso especificado no fue encontrado.")

    # Pasamos tanto los hechos del caso como la pregunta del estudiante al nodo.
    estado_simulado: EstadoDelGrafo = {
        "id_caso": solicitud.id_caso,
        "pregunta_para_agente_juridico": solicitud.pregunta,
        "hechos_del_caso_para_contexto": caso.descripcion_hechos # Nueva clave
    }
    # --- FIN DE LA MODIFICACION ---

    try:
        resultado_del_nodo = nodo_agente_juridico(estado_simulado)
        respuesta_del_agente = resultado_del_nodo.get("resultado_agente_juridico", {})
        
        contenido = respuesta_del_agente.get("contenido", "El agente no produjo una respuesta.")
        fuentes = respuesta_del_agente.get("fuentes", [])

        return RespuestaAgente(contenido=contenido, fuentes=fuentes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Agente Juridico: {e}")