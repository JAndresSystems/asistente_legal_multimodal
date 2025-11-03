# backend/api/enrutador_agentes.py

import os

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
from ..herramientas.herramienta_documentos import generar_documento_desde_plantilla

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

class SolicitudGeneracionDocumento(BaseModel):
    id_caso: int
    nombre_plantilla: str # ej. "derecho_de_peticion.docx"

class RespuestaGeneracionDocumento(BaseModel):
    url_descarga: str
    nombre_archivo: str


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
    Endpoint para que un estudiante O ASESOR realice una consulta al Agente Juridico.
    """
    # --- INICIO DE LA MODIFICACION: Permitir acceso al asesor ---
    roles_permitidos = ["estudiante", "asesor"]
    if cuenta_actual.rol not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de estudiante o asesor."
        )
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
    


# --- endpoint para el Agente de Documentos ---
@router_agentes.post("/generar-documento", response_model=RespuestaGeneracionDocumento)
def generar_documento_agente(
    solicitud: SolicitudGeneracionDocumento,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Endpoint para que un estudiante O ASESOR solicite la generacion de un documento.
    """
    # --- Permitir acceso al asesor ---
    roles_permitidos = ["estudiante", "asesor"]
    if cuenta_actual.rol not in roles_permitidos:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de estudiante o asesor."
        )
    caso = sesion.get(Caso, solicitud.id_caso)
    if not caso or not caso.usuario:
        raise HTTPException(status_code=404, detail="Caso o usuario asociado no encontrado.")

    datos_para_plantilla = {
        "{{NOMBRE_COMPLETO_USUARIO}}": caso.usuario.nombre,
        "{{CEDULA_USUARIO}}": caso.usuario.cedula,
        "{{HECHOS_DEL_CASO}}": caso.descripcion_hechos,
    }

    ruta_archivo_generado = generar_documento_desde_plantilla(
        nombre_plantilla=solicitud.nombre_plantilla,
        datos_reemplazo=datos_para_plantilla,
        id_caso=str(solicitud.id_caso)
    )

    # --- INICIO DE LA CORRECCION: Manejo de errores robusto ---
    # Convertimos a minusculas para detectar cualquier tipo de error ("Error:", "error", "ERROR")
    if "error" in ruta_archivo_generado.lower():
        raise HTTPException(status_code=500, detail=ruta_archivo_generado)
    # --- FIN DE LA CORRECCION ---

    nombre_archivo = os.path.basename(ruta_archivo_generado) # Forma más segura de obtener el nombre del archivo
    url_descarga = f"/archivos_subidos/{solicitud.id_caso}/{nombre_archivo}"
    
    return RespuestaGeneracionDocumento(url_descarga=url_descarga, nombre_archivo=nombre_archivo)