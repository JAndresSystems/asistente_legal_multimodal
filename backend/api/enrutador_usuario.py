# Ubicación: backend/api/enrutador_usuario.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, status
import shutil
from pathlib import Path
from sqlmodel import Session, select
from typing import List, Dict, Any
import json

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, Nota, NotaCreacion, NotaLectura, 
    SolicitudAnalisis, Cuenta, CasoLecturaUsuario, EstadoCaso, CasoDetalleUsuario,
    EvidenciaLecturaSimple, CasoLecturaConEvidencias,
    RespuestaChat,PreguntaChat 
)

from ..agentes.agente_orientacion import invocar_agente_orientacion
from ..tareas import procesar_evidencia_sincrono
from ..seguridad.jwt_manager import obtener_cuenta_actual

from fpdf import FPDF
from fastapi.responses import Response

router = APIRouter(
    prefix="/api/casos",
    tags=["Casos (Ciudadano)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)

# --- CLASE PDF (Sin cambios) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Caso - Asistente Legal Multimodal', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        body = body.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
        self.multi_cell(0, 10, body)
        self.ln()

    def sub_title(self, subtitle):
        self.set_font('Arial', '', 11)
        self.cell(0, 8, subtitle, 0, 1, 'L')
        self.ln(2)

    def indented_text(self, text, indent=10):
        self.set_x(indent)
        self.multi_cell(0, 10, text)
        self.ln(2)

# --- ENDPOINTS ---

@router.get("/{id_caso}/reporte-pdf")
def generar_reporte_pdf_ciudadano(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    caso = sesion.get(Caso, id_caso)
    if not caso or (not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id):
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    pdf = PDF()
    pdf.add_page()
    
    # 1. Datos del Solicitante
    pdf.chapter_title('1. Datos del Solicitante')
    if caso.usuario and caso.usuario.cuenta:
        info_usuario = (
            f"Nombre: {caso.usuario.nombre}\n"
            f"Cédula: {caso.usuario.cedula}\n"
            f"Email: {caso.usuario.cuenta.email}"
        )
        pdf.chapter_body(info_usuario)

    # 2. Datos Generales
    pdf.chapter_title('2. Datos Generales del Caso')
    info_caso = (
        f"ID del Caso: {caso.id}\n"
        f"Fecha de Creación: {caso.fecha_creacion.strftime('%Y-%m-%d %H:%M')}\n"
        f"Estado Actual: {caso.estado.replace('_', ' ').title()}"
    )
    pdf.chapter_body(info_caso)

    # 3. Descripción
    pdf.chapter_title('3. Descripción de los Hechos')
    pdf.chapter_body(caso.descripcion_hechos)

    # 4. Análisis IA
    if caso.reporte_consolidado:
        pdf.chapter_title('4. Análisis Preliminar de la IA')
        try:
            reporte = json.loads(caso.reporte_consolidado)
            
            if "TRIEJE" in reporte:
                triaje = reporte["TRIEJE"]
                pdf.sub_title('TRIAGE')
                pdf.indented_text(f"Admisible: {'Sí' if triaje.get('admisible') else 'No'}")
                pdf.indented_text(f"Justificación: {triaje.get('justificacion', '')}")
                pdf.indented_text(f"Hechos Clave: {triaje.get('hechos_clave', '')}")
            
            if "COMPETENCIA" in reporte:
                comp = reporte["COMPETENCIA"]
                pdf.sub_title('COMPETENCIA')
                pdf.indented_text(f"Área: {comp.get('area_competencia', '')}")
                pdf.indented_text(f"Justificación: {comp.get('justificacion_breve', '')}")
            
            if "ASIGNACION" in reporte:
                asign = reporte["ASIGNACION"]
                pdf.sub_title('ASIGNACIÓN')
                pdf.indented_text(f"Estudiante ID: {asign.get('id_estudiante_asignado', '')}")
            
            if "ANALISIS_DOCUMENTO" in reporte:
                doc = reporte["ANALISIS_DOCUMENTO"]
                pdf.sub_title('ANÁLISIS DE DOCUMENTO')
                pdf.indented_text(f"Tipo: {doc.get('tipo_documento_identificado', '')}")
                pdf.indented_text(f"Resumen: {doc.get('resumen_del_objeto', '')}")
            
            if "ANALISIS_JURIDICO" in reporte:
                jur = reporte["ANALISIS_JURIDICO"]
                pdf.sub_title('ANÁLISIS JURÍDICO')
                lines = jur.get('contenido', '').split('\n')
                for line in lines:
                    pdf.indented_text(line)

        except json.JSONDecodeError:
            pdf.chapter_body(caso.reporte_consolidado)

    # 5. Equipo
    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        pdf.chapter_title('5. Equipo Asignado')
        nombre_estudiante = asignacion.estudiante.nombre_completo if asignacion.estudiante else "No disponible"
        nombre_asesor = asignacion.asesor.nombre_completo if asignacion.asesor else "No disponible"
        area = asignacion.estudiante.area.nombre if (asignacion.estudiante and asignacion.estudiante.area) else "No definida"
        
        info_asignacion = (
            f"Área de Competencia: {area}\n"
            f"Estudiante a Cargo: {nombre_estudiante}\n"
            f"Asesor Supervisor: {nombre_asesor}"
        )
        pdf.chapter_body(info_asignacion)

    pdf_bytes = bytes(pdf.output())
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="reporte_caso_{id_caso}.pdf"'}
    )

@router.get("/mis-casos", response_model=List[CasoLecturaUsuario])
def obtener_mis_casos(sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=404, detail="Perfil de usuario no encontrado.")
    casos = sesion.exec(select(Caso).where(Caso.id_usuario == cuenta_actual.usuario.id, Caso.estado != EstadoCaso.RECHAZADO).order_by(Caso.fecha_creacion.desc())).all()
    return casos

@router.post("", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(caso_a_crear: CasoCreacion, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=403, detail="La cuenta no tiene un perfil de usuario asociado.")
    nuevo_caso_db = Caso(descripcion_hechos=caso_a_crear.descripcion_hechos, id_usuario=cuenta_actual.usuario.id)
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

@router.get("/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_caso_por_id(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    """
    Obtiene los detalles del caso.
    MODIFICADO: Incluye filtro de seguridad para que el ciudadano NO vea notas internas.
    """
    caso = sesion.get(Caso, id_caso)
    if not caso or (not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id):
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    respuesta = CasoDetalleUsuario.model_validate(caso)
    
    # Datos de Asignación
    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        if asignacion.estudiante:
            respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
            if asignacion.estudiante.area:
                respuesta.area_asignada = asignacion.estudiante.area.nombre
        if asignacion.asesor:
            respuesta.asesor_asignado = asignacion.asesor.nombre_completo

    # --- BLOQUE DE NOTAS CON FILTRO DE PRIVACIDAD ---
    if caso.notas:
        notas_con_autor = []
        for nota in sorted(caso.notas, key=lambda n: n.fecha_creacion, reverse=True):
            
            # --- FILTRO DE SEGURIDAD ---
            # Si quien consulta es un CIUDADANO (rol='usuario'), 
            # ocultamos notas de 'estudiante' o 'asesor'.
            if cuenta_actual.rol == 'usuario' and nota.rol_autor not in ['usuario', 'sistema']:
                continue 
            # ---------------------------

            nota_api = NotaLectura.model_validate(nota)
            cuenta_autor = sesion.get(Cuenta, nota.id_cuenta_autor)
            
            # Formateo del nombre del autor
            if cuenta_autor:
                if cuenta_autor.rol == 'usuario' and cuenta_autor.usuario:
                    nota_api.autor_nombre = "Tú" if cuenta_autor.id == cuenta_actual.id else cuenta_autor.usuario.nombre
                elif cuenta_autor.rol == 'asesor' and cuenta_autor.asesor:
                    nota_api.autor_nombre = f"Asesor: {cuenta_autor.asesor.nombre_completo}"
                elif cuenta_autor.rol == 'estudiante' and cuenta_autor.estudiante:
                    nota_api.autor_nombre = f"Estudiante: {cuenta_autor.estudiante.nombre_completo}"
                elif cuenta_autor.rol == 'sistema':
                    nota_api.autor_nombre = "Sistema"
            
            notas_con_autor.append(nota_api)
        respuesta.notas = notas_con_autor
    
    # Datos de Evidencias
    if caso.evidencias:
        evidencias_con_autor = []
        for ev in caso.evidencias:
            evidencia_api = EvidenciaLecturaSimple.model_validate(ev)
            evidencia_api.ruta_archivo = str(ev.ruta_archivo).replace("\\", "/").replace("backend/", "/")

            if ev.subido_por_id_cuenta:
                cuenta_autor = sesion.get(Cuenta, ev.subido_por_id_cuenta)
                if cuenta_autor:
                    if cuenta_autor.rol == 'usuario' and cuenta_autor.usuario:
                        evidencia_api.autor_nombre = "Tú" if cuenta_autor.id == cuenta_actual.id else cuenta_autor.usuario.nombre
                    elif cuenta_autor.rol == 'estudiante' and cuenta_autor.estudiante:
                        evidencia_api.autor_nombre = f"Estudiante: {cuenta_autor.estudiante.nombre_completo}"
            evidencias_con_autor.append(evidencia_api)
        respuesta.evidencias = evidencias_con_autor
            
    return respuesta

@router.post("/{id_caso}/subir-evidencia-simple", response_model=Evidencia)
def subir_evidencia_simple(
    id_caso: int, 
    archivo: UploadFile = File(...), 
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual or caso_actual.id_usuario != cuenta_actual.usuario.id: 
        raise HTTPException(status_code=404, detail="El caso no fue encontrado o no tiene permisos.")

    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso, 
        ruta_archivo=str(ruta_archivo_final), 
        estado="subido", 
        nombre_archivo=archivo.filename,
        tipo=archivo.content_type,
        subido_por_id_cuenta=cuenta_actual.id 
    )
    
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    
    return nueva_evidencia_db


# --- CORRECCIÓN CRÍTICA EN LA FUNCIÓN DE ANÁLISIS ---
@router.post("/{id_caso}/analizar", response_model=Dict[str, Any])
def analizar_caso_completo(id_caso: int, solicitud: SolicitudAnalisis, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    """
    Inicia el análisis SÍNCRONO del caso.
    MODIFICADO: Verifica exhaustivamente si el caso fue admitido para forzar 'flujo_terminado=True'.
    """
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    
    if not cuenta_actual.usuario or caso_actual.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=403, detail="No tiene permisos para analizar este caso.")

    tiene_archivos = len(caso_actual.evidencias) > 0
    tiene_texto = bool(solicitud.texto_adicional_usuario and solicitud.texto_adicional_usuario.strip())
    
    if not tiene_archivos and not tiene_texto:
        raise HTTPException(status_code=400, detail="Debe proporcionar evidencias o una descripción para analizar.")
    
    try:
        estado_final_del_grafo = procesar_evidencia_sincrono(
            id_caso=id_caso,
            texto_adicional_usuario=solicitud.texto_adicional_usuario,
            sesion=sesion
        )
        
        # --- LÓGICA ROBUSTA DE EXTRACCIÓN DE ESTADO ---
        
        # 1. Obtenemos los valores originales
        caso_admitido = estado_final_del_grafo.get("caso_admitido", False)
        flujo_terminado = estado_final_del_grafo.get("flujo_terminado", False)
        
        # 2. Verificación de seguridad: Si la decisión del triaje fue ADMISSIBLE, 
        #    entonces el caso ES admitido y el flujo ESTÁ terminado, 
        #    independientemente de si el nodo lo marcó explícitamente.
        resultado_triaje = estado_final_del_grafo.get("resultado_triaje", {})
        if resultado_triaje and resultado_triaje.get("decision_triaje") == "ADMISSIBLE":
            caso_admitido = True
            flujo_terminado = True
            print(f"--- [API] DETECTADO EXITO: Forzando flujo_terminado=True para caso {id_caso}")

        respuesta_limpia = {
            "respuesta_para_usuario": estado_final_del_grafo.get("respuesta_para_usuario"),
            "flujo_terminado": flujo_terminado,
            "caso_admitido": caso_admitido
        }
        
        return respuesta_limpia

    except Exception as e:
        print(f"Error detallado en analizar_caso_completo: {e}")
        raise HTTPException(status_code=500, detail=f"Ocurrió un error interno durante el análisis.")

@router.post("/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_usuario(
    id_caso: int,
    solicitud: NotaCreacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida.")

    caso = sesion.get(Caso, id_caso)
    if not caso or caso.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    nueva_nota = Nota(
        id_caso=id_caso,
        contenido=solicitud.contenido,
        id_cuenta_autor=cuenta_actual.id,
        rol_autor=cuenta_actual.rol 
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    respuesta_api = NotaLectura.model_validate(nueva_nota)
    respuesta_api.autor_nombre = caso.usuario.nombre
    
    return respuesta_api






# --- NUEVO ENDPOINT: CHAT DE ORIENTACIÓN (FALLBACK) ---
@router.post("/{id_caso}/chat-orientacion", response_model=Dict[str, Any])
def conversar_con_orientador(
    id_caso: int,
    solicitud: PreguntaChat, 
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    # 1. Validar
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
    caso = sesion.get(Caso, id_caso)
    if not caso or caso.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")

    # 2. Historial Usuario
    if not caso.historial_conversacion: caso.historial_conversacion = []
    historial = list(caso.historial_conversacion)
    
    historial.append({
        "autor": "usuario",
        "texto": solicitud.pregunta,
        "tipo": "chat_orientacion"
    })
    caso.historial_conversacion = historial

    # 3. Invocar al Agente (Detecta si hay queja)
    respuesta_agente = invocar_agente_orientacion(caso_db=caso, pregunta_usuario=solicitud.pregunta)
    texto_resp = respuesta_agente.get("respuesta_texto", "Error.")
    
    # --- LOGICA DE ALERTA AUTOMÁTICA ---
    if respuesta_agente.get("escalar_a_admin"):
        motivo = respuesta_agente.get("motivo_alerta", "Queja de usuario en chat")
        print(f"⚠️ [ALERTA] Usuario {cuenta_actual.email} solicita atención en caso {id_caso}: {motivo}")
        
        # Creamos una NOTA DE SISTEMA visible para asesores/admin
        nueva_alerta = Nota(
            id_caso=id_caso,
            contenido=f"🚨 [ALERTA AUTOMÁTICA DEL CHAT] El usuario ha reportado un problema: '{motivo}'. Se requiere revisión del Asesor.",
            id_cuenta_autor=cuenta_actual.id, # Vinculado al usuario
            rol_autor="sistema" # Marcado como sistema para filtrado y visibilidad administrativa
        )
        sesion.add(nueva_alerta)
    # -----------------------------------

    # 4. Guardar Respuesta en Historial
    historial.append({
        "autor": "agente_orientacion",
        "texto": texto_resp,
        "tipo": "chat_orientacion"
    })
    
    caso.historial_conversacion = historial
    sesion.add(caso)
    sesion.commit()
    
    return respuesta_agente