# Ubicación: backend/api/enrutador_usuario.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, status
import shutil
from pathlib import Path
from sqlmodel import Session, select
from typing import List
import json
from celery.result import AsyncResult
from ..tareas import celery_app
from ..agentes.orquestador_del_grafo import grafo_compilado

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Caso, CasoCreacion, Evidencia, Nota, NotaCreacion, NotaLectura, 
    SolicitudAnalisis, Cuenta, CasoLecturaUsuario, EstadoCaso, CasoDetalleUsuario,
    EvidenciaLecturaSimple,CasoLecturaConEvidencias
)
from ..tareas import procesar_evidencia_tarea
from ..seguridad.jwt_manager import obtener_cuenta_actual

from fpdf import FPDF
from fastapi.responses import Response

# --- INICIO DE LA MODIFICACIÓN ---
# 1. Renombramos a 'router' por consistencia
router = APIRouter(
    prefix="/api/casos",
    tags=["Casos (Ciudadano)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)


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
        # Limpiar chars problemáticos (comillas curvas, etc.)
        body = body.replace('’', "'").replace('“', '"').replace('”', '"').replace('–', '-')
        self.multi_cell(0, 10, body)
        self.ln()

    def sub_title(self, subtitle):
        self.set_font('Arial', '', 11)  # Sin negrita
        self.cell(0, 8, subtitle, 0, 1, 'L')
        self.ln(2)

    def indented_text(self, text, indent=10):
        self.set_x(indent)
        self.multi_cell(0, 10, text)
        self.ln(2)

@router.get("/{id_caso}/reporte-pdf")
def generar_reporte_pdf_ciudadano(id_caso: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    caso = sesion.get(Caso, id_caso)
    if not caso or (not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id):
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    pdf = PDF()
    pdf.add_page()
    
    # Sección 1: Datos del Solicitante
    pdf.chapter_title('1. Datos del Solicitante')
    if caso.usuario and caso.usuario.cuenta:
        info_usuario = (
            f"Nombre: {caso.usuario.nombre}\n"
            f"Cédula: {caso.usuario.cedula}\n"
            f"Email: {caso.usuario.cuenta.email}"
        )
        pdf.chapter_body(info_usuario)

    # Sección 2: Datos Generales del Caso
    pdf.chapter_title('2. Datos Generales del Caso')
    info_caso = (
        f"ID del Caso: {caso.id}\n"
        f"Fecha de Creación: {caso.fecha_creacion.strftime('%Y-%m-%d %H:%M')}\n"
        f"Estado Actual: {caso.estado.replace('_', ' ').title()}"
    )
    pdf.chapter_body(info_caso)

    # Sección 3: Descripción de los Hechos
    pdf.chapter_title('3. Descripción de los Hechos')
    pdf.chapter_body(caso.descripcion_hechos)

    # Sección 4: Análisis Preliminar de la IA
    if caso.reporte_consolidado:
        pdf.chapter_title('4. Análisis Preliminar de la IA')
        
        try:
            # Parsear el JSON string a un diccionario Python
            reporte = json.loads(caso.reporte_consolidado)
            
            # Sección TRIAJE
            if "TRIEJE" in reporte:
                triaje = reporte["TRIEJE"]
                pdf.sub_title('TRIAGE')
                pdf.indented_text(f"Admisible: {'Sí' if triaje['admisible'] else 'No'}")
                pdf.indented_text(f"Justificación: {triaje['justificacion']}")
                pdf.indented_text(f"Hechos Clave: {triaje['hechos_clave']}")
                pdf.indented_text(f"Información Suficiente: {'Sí' if triaje['informacion_suficiente'] else 'No'}")
            
            # Sección COMPETENCIA
            if "COMPETENCIA" in reporte:
                comp = reporte["COMPETENCIA"]
                pdf.sub_title('COMPETENCIA')
                pdf.indented_text(f"Área: {comp['area_competencia']}")
                pdf.indented_text(f"Justificación: {comp['justificacion_breve']}")
            
            # Sección ASIGNACION
            if "ASIGNACION" in reporte:
                asign = reporte["ASIGNACION"]
                pdf.sub_title('ASIGNACIÓN')
                pdf.indented_text(f"Estudiante Asignado: ID {asign['id_estudiante_asignado']}")
                pdf.indented_text(f"Asesor Asignado: ID {asign['id_asesor_asignado']}")
                pdf.indented_text(f"Operación DB: {asign['operacion_db']}")
            
            # Sección ANALISIS_DOCUMENTO
            if "ANALISIS_DOCUMENTO" in reporte:
                doc = reporte["ANALISIS_DOCUMENTO"]
                pdf.sub_title('ANÁLISIS DE DOCUMENTO')
                pdf.indented_text(f"Tipo: {doc['tipo_documento_identificado']}")
                pdf.indented_text("Partes Involucradas: " + ", ".join(doc['partes_involucradas']))
                pdf.indented_text("Fechas Clave: " + ", ".join(doc['fechas_clave']))
                pdf.indented_text(f"Resumen: {doc['resumen_del_objeto']}")
                pdf.indented_text('Puntos Relevantes:')
                for p in doc['puntos_relevantes']:
                    pdf.indented_text(f"- {p}", indent=15)
            
            # Sección ANALISIS_JURIDICO
            if "ANALISIS_JURIDICO" in reporte:
                jur = reporte["ANALISIS_JURIDICO"]
                pdf.sub_title('ANÁLISIS JURÍDICO')
                # Parse simple de Markdown
                lines = jur['contenido'].split('\n')
                for line in lines:
                    if line.startswith('###') or line.startswith('#'):
                        pdf.sub_title(line.strip('# ').strip())
                    elif line.startswith('**'):
                        # Sin negrita, como texto normal
                        pdf.indented_text(line.strip('**').strip())
                    elif line.startswith('*') or line.startswith('-'):
                        pdf.indented_text(f"- {line.strip('* -').strip()}", indent=15)
                    else:
                        pdf.indented_text(line)
                pdf.indented_text('Fuentes:')
                for f in jur['fuentes']:
                    pdf.indented_text(f"- {f}", indent=15)
        
        except json.JSONDecodeError:
            # Fallback
            pdf.chapter_body(caso.reporte_consolidado)

    # Sección 5: Equipo Asignado (si existe)
    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        pdf.chapter_title('5. Equipo Asignado')
        nombre_estudiante = asignacion.estudiante.nombre_completo if asignacion.estudiante else "No disponible"
        nombre_asesor = asignacion.asesor.nombre_completo if asignacion.asesor else "No disponible"
        area = "No definida"
        if asignacion.estudiante and asignacion.estudiante.area:
            area = asignacion.estudiante.area.nombre
        info_asignacion = (
            f"Área de Competencia: {area}\n"
            f"Estudiante a Cargo: {nombre_estudiante}\n"
            f"Asesor Supervisor: {nombre_asesor}"
        )
        pdf.chapter_body(info_asignacion)

    # Convertir a bytes
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
    caso = sesion.get(Caso, id_caso)
    if not caso or (not cuenta_actual.usuario or caso.id_usuario != cuenta_actual.usuario.id):
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    respuesta = CasoDetalleUsuario.model_validate(caso)
    
    # Poblar datos de la asignación si existe
    if caso.asignaciones:
        asignacion = caso.asignaciones[0]
        if asignacion.estudiante:
            respuesta.estudiante_asignado = asignacion.estudiante.nombre_completo
            # --- INICIO DE LA CORRECCION ---
            # Accedemos a la relación .area y luego a su atributo .nombre
            if asignacion.estudiante.area:
                respuesta.area_asignada = asignacion.estudiante.area.nombre
            # --- FIN DE LA CORRECCION ---
        if asignacion.asesor:
            respuesta.asesor_asignado = asignacion.asesor.nombre_completo


    if caso.notas:
        notas_con_autor = []
        for nota in sorted(caso.notas, key=lambda n: n.fecha_creacion, reverse=True):
            nota_api = NotaLectura.model_validate(nota)
            cuenta_autor = sesion.get(Cuenta, nota.id_cuenta_autor)
            if cuenta_autor:
                if cuenta_autor.rol == 'usuario' and cuenta_autor.usuario:
                    # Para el usuario, mostramos "Tú" para sus propias notas
                    nota_api.autor_nombre = "Tú" if cuenta_autor.id == cuenta_actual.id else cuenta_autor.usuario.nombre
                elif cuenta_autor.rol == 'asesor' and cuenta_autor.asesor:
                    nota_api.autor_nombre = f"Asesor: {cuenta_autor.asesor.nombre_completo}"
                elif cuenta_autor.rol == 'estudiante' and cuenta_autor.estudiante:
                    nota_api.autor_nombre = f"Estudiante: {cuenta_autor.estudiante.nombre_completo}"
                elif cuenta_autor.rol == 'sistema':
                    nota_api.autor_nombre = "Sistema"
            notas_con_autor.append(nota_api)
        respuesta.notas = notas_con_autor



    
    # Poblar URLs de evidencias
    if caso.evidencias:
        evidencias_con_autor = []
        for ev in caso.evidencias:
            evidencia_api = EvidenciaLecturaSimple.model_validate(ev)
            # Reconstruimos la URL relativa para el frontend
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



# --- endpoint para subir evidencia simple --- 
@router.post("/{id_caso}/subir-evidencia-simple", response_model=Evidencia)
def subir_evidencia_simple(
    id_caso: int, 
    archivo: UploadFile = File(...), 
    sesion: Session = Depends(obtener_sesion),
    
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
    
):
    # Validar que el caso pertenece al usuario
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




@router.post("/{id_caso}/analizar")
def analizar_caso_completo(
    id_caso: int,
    solicitud: SolicitudAnalisis,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual) # Asegura que solo el dueño del caso lo pueda analizar
):
    """
    Inicia la tarea de análisis y ESPERA a que se complete (síncrono).
    Esta es la lógica original de 'procesar_evidencia_tarea', pero ejecutada en el hilo web.
    """
    print(f"DEBUG: Iniciando análisis SÍNCRONO para el CASO ID: {id_caso} en hilo web.")
    # Validar que el caso pertenece al usuario logueado
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual or caso_actual.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    if not caso_actual.evidencias:
        raise HTTPException(status_code=400, detail="No se pueden analizar casos sin evidencias.")

    try:
        # Preparamos la entrada para el grafo de LangGraph
        rutas_archivos = [ev.ruta_archivo for ev in caso_actual.evidencias]
        print(f"DEBUG: El agente analizara un total de {len(rutas_archivos)} evidencia(s).")
        estado_inicial = {
            "id_caso": id_caso,
            "rutas_archivos_evidencia": rutas_archivos,
            "texto_adicional_usuario": solicitud.texto_adicional_usuario,
        }

        # Invocamos a los agentes (síncrono)
        estado_final = grafo_compilado.invoke(estado_inicial)
        print("DEBUG: El grafo de LangGraph completo su ejecucion.")

        # ==============================================================================
        # INICIO DE LA COPIA: Construimos un diccionario y lo convertimos a JSON
        # AHORA MANEJA CASOS DONDE EL FLUJO TERMINA ANTES (p. ej. en rechazo).
        # ==============================================================================
        reporte_dict = {}

        # Verificamos si cada clave existe en el estado_final antes de asignarla
        # y construimos el reporte_dict dinámicamente
        claves_posibles = [
            "resultado_triaje",
            "resultado_determinador_competencias",
            "resultado_repartidor",
            "resultado_analisis_documento",
            "resultado_analisis_audio",
            "resultado_agente_juridico",
            "solicitud_agente_juridico", # Por si acaso
            "solicitud_agente_documentos", # Por si acaso
            "resultado_agente_generador_documentos" # Por si acaso
        ]

        for clave in claves_posibles:
            if clave in estado_final:
                # Convertimos el nombre clave al formato que espera el frontend/reportes
                # Ej: "resultado_triaje" -> "TRIEJE"
                nombre_reporte = clave.upper().replace("RESULTADO_", "").replace("_", "")
                if nombre_reporte == "TRIAGE": # Corrección ortográfica común
                    nombre_reporte = "TRIEJE"
                reporte_dict[nombre_reporte] = estado_final[clave]

        # Filtramos las claves cuyo valor sea None para un reporte más limpio
        reporte_dict_limpio = {k: v for k, v in reporte_dict.items() if v is not None}

        # Convertimos el diccionario a un string JSON con formato legible
        caso_actual.reporte_consolidado = json.dumps(reporte_dict_limpio, indent=2, ensure_ascii=False)
        # ==============================================================================
        # FIN DE LA COPIA
        # ==============================================================================

        # El estado del caso (RECHAZADO, PENDIENTE_ACEPTACION, etc.) ya fue actualizado
        # por el nodo correspondiente dentro del grafo (por ejemplo, nodo_preparar_respuesta_rechazo).
        # No es necesario actualizarlo aquí manualmente basado en estado_final,
        # ya que el grafo lo hizo internamente y se guardó en la BD en ese momento.
        # Recargamos el objeto caso_actual para asegurar que tenemos el estado final correcto.
        sesion.refresh(caso_actual) # <-- Crucial para obtener el estado actualizado desde la DB

        sesion.add(caso_actual)
        sesion.commit()
        print(f"DEBUG: Reporte consolidado y estado actualizados en el Caso {id_caso} (hilo web).")

        # Devolvemos el estado final para que el frontend lo maneje
        return estado_final

    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: ERROR CRITICO en la ejecución SÍNCRONA para caso {id_caso}: {error_msg}")

        # Opcional: Intentar guardar el error en la base de datos para que el usuario lo vea
        if caso_actual:
            try:
                caso_actual.reporte_consolidado = json.dumps({"error": error_msg})
                # Si el grafo no lo cambió de estado (por ejemplo, si falló antes de llegar a un nodo decisivo)
                # y no está ya rechazado, lo marcamos como cerrado con error.
                if caso_actual.estado not in [EstadoCaso.RECHAZADO, EstadoCaso.CERRADO]:
                    caso_actual.estado = EstadoCaso.CERRADO
                sesion.add(caso_actual)
                sesion.commit()
                print(f"DEBUG: Error guardado en la base de datos para el Caso {id_caso}.")
            except Exception as db_error:
                print(f"DEBUG: Error al guardar el error en la base de datos: {db_error}")

        # Manejar el error específico de archivos si es necesario, como hiciste antes
        if "Unrecognized message part type: media" in error_msg:
             raise HTTPException(status_code=500, detail=f"Error al procesar el archivo enviado: {error_msg}. Es posible que el formato no sea compatible o el archivo esté dañado.")
        else:
            raise HTTPException(status_code=500, detail=f"Error interno al procesar el análisis: {error_msg}")

    

# Asegúrate de que esta función esté dentro del mismo 'router' que las demás.

# @router.get("/{id_caso}/estado-analisis/{id_tarea}")
# def consultar_estado_analisis(
#     id_caso: int,
#     id_tarea: str,
#     sesion: Session = Depends(obtener_sesion),
#     cuenta_actual: Cuenta = Depends(obtener_cuenta_actual) # Asegura que solo el dueño del caso pueda consultar
# ):
#     """
#     Consulta el estado de una tarea de análisis de Celery.
#     """
#     # Validar que el caso pertenece al usuario logueado
#     caso = sesion.get(Caso, id_caso)
#     if not caso or caso.id_usuario != cuenta_actual.usuario.id:
#         raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

#     # Obtener el estado de la tarea de Celery
#     resultado_tarea = AsyncResult(id_tarea, app=celery_app)

#     if resultado_tarea.state == 'PENDING':
#         return {"estado": "en_progreso", "mensaje": "La tarea está pendiente de inicio."}
#     elif resultado_tarea.state == 'PROGRESS':
#         # Opcional: Si Celery reporta progreso, puedes devolverlo aquí
#         return {"estado": "en_progreso", "mensaje": "Analizando evidencias..."}
#     elif resultado_tarea.state == 'SUCCESS':
#         # La tarea terminó exitosamente. Devolvemos el caso actualizado desde la BD.
#         # Asegúrate de que la tarea haya guardado el resultado en la base de datos.
#         caso_actualizado = sesion.get(Caso, id_caso)
#         # Opcional: Puedes devolver solo el estado del caso o el objeto completo
#         return {"estado": "completado", "caso": caso_actualizado}
#     else: # FAILURE u otros estados
#         return {"estado": "error", "mensaje": str(resultado_tarea.info)}






@router.post("/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_usuario(
    id_caso: int,
    solicitud: NotaCreacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un usuario (ciudadano) añadir una nota a su propio caso.
    """
    # 1. Validar que la cuenta tiene un perfil de usuario
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida.")

    # 2. Validar que el caso existe y pertenece al usuario actual (CRÍTICO)
    caso = sesion.get(Caso, id_caso)
    if not caso or caso.id_usuario != cuenta_actual.usuario.id:
        raise HTTPException(status_code=404, detail="Caso no encontrado o sin permisos.")

    # 3. Crear el objeto Nota en la base de datos
    nueva_nota = Nota(
        id_caso=id_caso,
        contenido=solicitud.contenido,
        id_cuenta_autor=cuenta_actual.id,
        rol_autor=cuenta_actual.rol # Se guardará como 'usuario'
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    # 4. Poblar el nombre del autor para la respuesta (opcional pero buena práctica)
    respuesta_api = NotaLectura.model_validate(nueva_nota)
    respuesta_api.autor_nombre = caso.usuario.nombre
    
    return respuesta_api

