# Ubicación: backend/api/enrutador_estudiante.py



from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, status,Form 
import shutil
from pathlib import Path
from sqlmodel import Session, select
from typing import List
import json

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import * # Usamos * por brevedad, ya que son muchas
from ..seguridad.jwt_manager import obtener_cuenta_actual
from ..utilidades.enviador_de_correos import enviar_correo_notificacion

from fpdf import FPDF
from fastapi.responses import Response

# --- INICIO DE LA MODIFICACIÓN ---
# 1. Renombramos a 'router' por consistencia
router = APIRouter(
    prefix="/api/expedientes",
    tags=["Expedientes (Estudiante)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Caso - Asistente Legal Multimodal', 0, 1, 'C')
        self.ln(10)
    # ... (Copie aquí la clase PDF completa que usted creó, tal como en el archivo de usuario)
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





@router.get("/mis-asignaciones", response_model=List[CasoEstudianteDashboard])
def obtener_mis_asignaciones(sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not hasattr(cuenta_actual, 'estudiante') or not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Esta cuenta no tiene un perfil de estudiante asociado.")
    
    id_estudiante = cuenta_actual.estudiante.id
    
    # Obtenemos las asignaciones (que contienen la nota)
    asignaciones = sesion.exec(
        select(Asignacion).where(Asignacion.id_estudiante == id_estudiante)
    ).all()

    resultados = []
    for asig in asignaciones:
        caso = sesion.get(Caso, asig.id_caso)
        if caso:
            resultados.append(
                CasoEstudianteDashboard(
                    id=caso.id,
                    fecha_creacion=caso.fecha_creacion,
                    estado=caso.estado,
                    descripcion_hechos=caso.descripcion_hechos,
                    # Extraemos la nota de la asignación
                    calificacion=asig.calificacion,
                    comentario_docente=asig.comentario_docente
                )
            )
            
    # Ordenamos por fecha descendente
    return sorted(resultados, key=lambda x: x.fecha_creacion, reverse=True)



@router.post("/{id_caso}/aceptar", status_code=status.HTTP_200_OK)
def aceptar_asignacion(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Accion no permitida.")

    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada.")
    if asignacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta asignacion ya ha sido procesada.")

    asignacion.estado = "aceptado"
    caso = sesion.get(Caso, id_caso)
    if caso:
        caso.estado = EstadoCaso.ASIGNADO
        sesion.add(caso)

    sesion.add(asignacion)
    sesion.commit()
    return {"mensaje": f"Caso {id_caso} aceptado exitosamente."}



@router.post("/{id_caso}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_asignacion(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Accion no permitida.")
        
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignacion no encontrada.")
    if asignacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta asignacion ya ha sido procesada.")

    asignacion.estado = "rechazado"
    caso = sesion.get(Caso, id_caso)
    if caso:
        # Devolvemos el caso al estado de revision para una posible reasignacion
        caso.estado = EstadoCaso.EN_REVISION 
        sesion.add(caso)

    sesion.add(asignacion)
    sesion.commit()
    # TODO: En un futuro, aqui se podria disparar una tarea para reasignar el caso.
    return {"mensaje": f"Caso {id_caso} rechazado. Se notificara al administrador."}




@router.post("/{id_caso}/subir-documento", response_model=Evidencia)
def subir_documento_estudiante(
    id_caso: int, 
    archivo: UploadFile = File(...), 
    es_publica: bool = Form(False), # <--- AGREGADO: Recibe la privacidad (False por defecto)
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante subir un documento definiendo su privacidad.
    """
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden subir documentos.")

    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso, 
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tiene permiso para subir documentos a este caso.")

    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso, 
        ruta_archivo=str(ruta_archivo_final), 
        nombre_archivo=archivo.filename,
        tipo=archivo.content_type,
        subido_por_id_cuenta=cuenta_actual.id,
        es_publica=es_publica # <--- GUARDAMOS LA PRIVACIDAD EN LA BASE DE DATOS
    )
  
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    sesion.refresh(nueva_evidencia_db)
    
    return nueva_evidencia_db





@router.post("/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_estudiante(
    id_caso: int,
    solicitud: NotaCreacion, # Ahora recibe es_publica
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=403, detail="Solo los estudiantes pueden crear notas.")

    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso,
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tiene permiso para añadir notas a este caso.")

    nueva_nota = Nota(
        id_caso=id_caso,
        contenido=solicitud.contenido,
        id_cuenta_autor=cuenta_actual.id,
        rol_autor="estudiante", # Se marca como estudiante
        es_publica=solicitud.es_publica, # <--- GUARDAMOS LA PRIVACIDAD
        id_evidencia=solicitud.id_evidencia
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    # Mapeo manual para la respuesta
    return NotaLectura(
        id=nueva_nota.id,
        contenido=nueva_nota.contenido,
        fecha_creacion=nueva_nota.fecha_creacion,
        rol_autor=nueva_nota.rol_autor,
        autor_nombre="Tú"
    )




@router.post("/{id_caso}/enviar-notificacion", status_code=status.HTTP_200_OK)
def enviar_notificacion_a_usuario(
    id_caso: int,
    notificacion: NotificacionCreacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante enviar una notificación por correo al usuario de un caso.
    """
    # 1. Validar que el usuario es un estudiante
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida.")

    # 2. Validar que el estudiante está asignado y ha aceptado el caso
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso,
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    if not asignacion:
        raise HTTPException(status_code=403, detail="No tiene permiso para enviar notificaciones en este caso.")

    # 3. Obtener el correo del usuario (ciudadano)
    caso = asignacion.caso
    if not (caso and caso.usuario and caso.usuario.cuenta):
        raise HTTPException(status_code=404, detail="No se pudo encontrar la información del usuario para notificar.")
    
    email_destinatario = caso.usuario.cuenta.email

    # 4. Construir el contenido del correo y enviarlo
    # Podríamos usar plantillas HTML más avanzadas en el futuro
    contenido_html = f"""
    <html>
        <body>
            <h1>Notificación sobre su caso #{caso.id}</h1>
            <p>Estimado(a) {caso.usuario.nombre},</p>
            <p>Ha recibido un nuevo mensaje del estudiante a cargo de su caso:</p>
            <hr>
            <p><strong>{notificacion.mensaje}</strong></p>
            <hr>
            <p>Para responder o ver los detalles de su caso, por favor ingrese a la plataforma.</p>
            <p>Atentamente,<br>Consultorio Jurídico</p>
        </body>
    </html>
    """
    
    exito = enviar_correo_notificacion(
        destinatario=email_destinatario,
        asunto=f"Actualización sobre su caso #{id_caso}: {notificacion.asunto}",
        contenido_html=contenido_html
    )

    if not exito:
        raise HTTPException(status_code=500, detail="El servicio de correo no pudo enviar la notificación.")

    # 5. Opcional: Crear una nota en la línea de tiempo para registrar que se envió la notificación
    nota_registro = Nota(
        id_caso=id_caso,
        contenido=f"[Notificación Enviada por Email] Asunto: {notificacion.asunto}",
        id_cuenta_autor=cuenta_actual.id,
        rol_autor="sistema" # Usamos un rol especial para notas automáticas
    )
    sesion.add(nota_registro)
    sesion.commit()

    return {"mensaje": "Notificación enviada exitosamente al usuario."}




@router.get("/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_detalle_expediente(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    if not hasattr(cuenta_actual, 'estudiante') or not cuenta_actual.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignación no encontrada o sin permisos.")

    caso = asignacion.caso
    if not caso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso asociado a la asignación no encontrado.")
    
    respuesta = CasoDetalleUsuario.model_validate(caso)

    if asignacion.estudiante:
        respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
        if asignacion.estudiante.area:
            respuesta.area_asignada = asignacion.estudiante.area.nombre
            
    if asignacion.asesor:
        respuesta.asesor_asignado = asignacion.asesor.nombre_completo

    if caso.notas:
        notas_con_autor = []
        for nota in sorted(caso.notas, key=lambda n: n.fecha_creacion, reverse=True):
            nota_api = NotaLectura.model_validate(nota)
            
            # --- CORRECCIÓN CRÍTICA: Asegurar que pase el ID de evidencia ---
            nota_api.id_evidencia = nota.id_evidencia 
            # --------------------------------------------------------------

            cuenta_autor = sesion.get(Cuenta, nota.id_cuenta_autor)
            if cuenta_autor:
                if cuenta_autor.rol == 'usuario' and cuenta_autor.usuario:
                    nota_api.autor_nombre = cuenta_autor.usuario.nombre
                elif cuenta_autor.rol == 'asesor' and cuenta_autor.asesor:
                    nota_api.autor_nombre = cuenta_autor.asesor.nombre_completo
                elif cuenta_autor.rol == 'estudiante' and cuenta_autor.estudiante:
                    nota_api.autor_nombre = "Tú" if cuenta_autor.id == cuenta_actual.id else cuenta_autor.estudiante.nombre_completo
                elif cuenta_autor.rol == 'sistema':
                    nota_api.autor_nombre = "Sistema"
            notas_con_autor.append(nota_api)
        respuesta.notas = notas_con_autor    

    if caso.evidencias:
        evidencias_con_autor = []
        for ev in caso.evidencias:
            evidencia_api = EvidenciaLecturaSimple.model_validate(ev)
            evidencia_api.ruta_archivo = str(ev.ruta_archivo).replace("\\", "/").replace("backend/", "/")

            if ev.subido_por_id_cuenta:
                cuenta_autor = sesion.get(Cuenta, ev.subido_por_id_cuenta)
                if cuenta_autor:
                    if cuenta_autor.rol == 'usuario' and cuenta_autor.usuario:
                        evidencia_api.autor_nombre = f"Usuario: {cuenta_autor.usuario.nombre}"
                    elif cuenta_autor.rol == 'estudiante' and cuenta_autor.estudiante:
                        evidencia_api.autor_nombre = "Tú" if cuenta_autor.id == cuenta_actual.id else cuenta_autor.estudiante.nombre_completo
            evidencias_con_autor.append(evidencia_api)
        respuesta.evidencias = evidencias_con_autor
            
    return respuesta





@router.get("/{id_caso}/reporte-pdf")
def generar_reporte_pdf_expediente(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    # 1. Validación de Permisos para Estudiantes/Asesores (se mantiene)
    if cuenta_actual.rol not in ["estudiante", "asesor"]:
         raise HTTPException(status_code=status.HTTP_4_FORBIDDEN, detail="Acceso denegado.")

    if cuenta_actual.rol == "estudiante":
        asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_estudiante == cuenta_actual.estudiante.id)).first()
    else: # Es un asesor
        id_estudiantes_supervisados = [est.id for est in cuenta_actual.asesor.estudiantes_supervisados]
        asignacion = sesion.exec(select(Asignacion).where(
            Asignacion.id_caso == id_caso,
            (Asignacion.id_asesor == cuenta_actual.asesor.id) | (Asignacion.id_estudiante.in_(id_estudiantes_supervisados))
        )).first()

    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada o sin permisos para este expediente.")

    caso = asignacion.caso
    if not caso:
        raise HTTPException(status_code=404, detail="Caso asociado a la asignación no encontrado.")

    # --- INICIO DE LA MODIFICACIÓN ---
    # 2. Lógica de Generación de PDF (replicando su versión avanzada)
    pdf = PDF()
    pdf.add_page()
    
    # Sección 1: Datos del Solicitante
    pdf.chapter_title('1. Datos del Solicitante')
    if caso.usuario and caso.usuario.cuenta:
        info_usuario = f"Nombre: {caso.usuario.nombre}\nCédula: {caso.usuario.cedula}\nEmail: {caso.usuario.cuenta.email}"
        pdf.chapter_body(info_usuario)

    # Sección 2: Datos Generales del Caso
    pdf.chapter_title('2. Datos Generales del Caso')
    info_caso = f"ID del Caso: {caso.id}\nFecha de Creación: {caso.fecha_creacion.strftime('%Y-%m-%d %H:%M')}\nEstado Actual: {caso.estado.replace('_', ' ').title()}"
    pdf.chapter_body(info_caso)

    # Sección 3: Descripción de los Hechos
    pdf.chapter_title('3. Descripción de los Hechos')
    pdf.chapter_body(caso.descripcion_hechos)
    
    # Sección 4: Análisis Preliminar de la IA (Lógica avanzada de parseo)
    if caso.reporte_consolidado:
        pdf.chapter_title('4. Análisis Preliminar de la IA')
        try:
            reporte = json.loads(caso.reporte_consolidado)
            
            if "TRIEJE" in reporte:
                triaje = reporte["TRIEJE"]
                pdf.sub_title('ANÁLISIS DE TRIAJE')
                pdf.indented_text(f"Admisible: {'Sí' if triaje.get('admisible') else 'No'}")
                pdf.indented_text(f"Justificación: {triaje.get('justificacion', 'N/A')}")
                pdf.indented_text(f"Hechos Clave: {triaje.get('hechos_clave', 'N/A')}")
                pdf.indented_text(f"Información Suficiente: {'Sí' if triaje.get('informacion_suficiente') else 'No'}")
            
            if "COMPETENCIA" in reporte:
                comp = reporte["COMPETENCIA"]
                pdf.sub_title('ANÁLISIS DE COMPETENCIA')
                pdf.indented_text(f"Área: {comp.get('area_competencia', 'N/A')}")
                pdf.indented_text(f"Justificación: {comp.get('justificacion_breve', 'N/A')}")

            if "ANALISIS_JURIDICO" in reporte:
                jur = reporte["ANALISIS_JURIDICO"]
                pdf.sub_title('ANÁLISIS JURÍDICO DEL CASO')
                if jur.get('contenido'):
                    lines = jur['contenido'].split('\n')
                    for line in lines:
                        cleaned_line = line.strip()
                        if cleaned_line.startswith('###'):
                            pdf.sub_title(cleaned_line.strip('# ').strip())
                        elif cleaned_line.startswith('**'):
                            pdf.indented_text(cleaned_line.strip('**').strip())
                        elif cleaned_line.startswith('*') or cleaned_line.startswith('-'):
                            pdf.indented_text(f"- {cleaned_line.strip('* -').strip()}", indent=15)
                        elif cleaned_line:
                            pdf.indented_text(cleaned_line)
                if jur.get('fuentes'):
                    pdf.indented_text('Fuentes Consultadas:')
                    for f in jur['fuentes']:
                        pdf.indented_text(f"- {f}", indent=15)
        
        except (json.JSONDecodeError, TypeError):
            pdf.chapter_body(caso.reporte_consolidado)

    # Sección 5: Equipo Asignado
    pdf.chapter_title('5. Equipo Asignado')
    nombre_estudiante = asignacion.estudiante.nombre_completo if asignacion.estudiante else "No disponible"
    nombre_asesor = asignacion.asesor.nombre_completo if asignacion.asesor else "No disponible"
    area = "No definida"
    if asignacion.estudiante and asignacion.estudiante.area:
        area = asignacion.estudiante.area.nombre
    info_asignacion = f"Área de Competencia: {area}\nEstudiante a Cargo: {nombre_estudiante}\nAsesor Supervisor: {nombre_asesor}"
    pdf.chapter_body(info_asignacion)

    # CORRECCIÓN: Convertir a bytes de la forma correcta
    pdf_bytes = bytes(pdf.output())
    
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="reporte_caso_{id_caso}.pdf"'}
    )




@router.post("/documentos/{id_evidencia}/enviar-a-revision", status_code=status.HTTP_200_OK)
def enviar_documento_a_revision(
    id_evidencia: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un estudiante cambiar el estado de un documento de 'subido' a 'en_revision'.
    """
    # 1. Validar que el usuario es un estudiante
    if not cuenta_actual.estudiante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida para este rol.")

    # 2. Obtener el documento (evidencia) y validar su existencia
    documento = sesion.get(Evidencia, id_evidencia)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

    # 3. Validar que el estudiante tiene permiso sobre el caso de este documento
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == documento.id_caso,
            Asignacion.id_estudiante == cuenta_actual.estudiante.id,
            Asignacion.estado == "aceptado"
        )
    ).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para modificar este documento.")

    # 4. Validar que el documento fue subido por el estudiante
    if documento.subido_por_id_cuenta != cuenta_actual.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo puede enviar a revisión los documentos que usted ha subido.")

    # 5. Validar que el estado actual del documento es 'subido'
    if documento.estado != EstadoEvidencia.SUBIDO.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El documento no se puede enviar a revisión desde el estado actual ('{documento.estado}').")

    # 6. Actualizar el estado y guardar en la base de datos
    documento.estado = EstadoEvidencia.EN_REVISION.value
    sesion.add(documento)
    sesion.commit()
    sesion.refresh(documento)

    return {"mensaje": f"El documento '{documento.nombre_archivo}' ha sido enviado a revisión."}