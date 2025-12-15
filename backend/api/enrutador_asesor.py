#C:\react\asistente_legal_multimodal\backend\api\enrutador_asesor.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List

from ..base_de_datos import obtener_sesion
from ..seguridad.jwt_manager import obtener_cuenta_actual
from .modelos_compartidos import (
    Cuenta, Asesor, Asignacion, Caso, Estudiante, Evidencia,
    EstudianteLecturaSimple, SolicitudReasignacion, CasoSupervisadoLectura,
    CasoDetalleUsuario, EvidenciaLecturaSimple, Nota, NotaCreacion, NotaLectura,
    EstadoCaso, EstadoEvidencia, DashboardAsesorData, MetricaEstudiante,SolicitudCierreCaso 
)

from ..agentes.nodos_del_grafo import encontrar_persona_con_menos_carga

# Se añade "/api" al prefijo para estandarizar todas las rutas del backend y
# solucionar el error '404 Not Found' que estabas experimentando.
router_asesor = APIRouter(
    prefix="/api/asesor",
    tags=["Asesor (Supervisor)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)


# --- Dependencia de Seguridad Mejorada ---
# Creamos una dependencia reutilizable que no solo obtiene la cuenta actual,
# sino que tambien valida que el rol sea 'asesor' y que su perfil exista.
# Esto soluciona el bug de logica y nos permite limpiar y simplificar el
# codigo repetitivo en cada endpoint.
def obtener_asesor_actual(cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)) -> Asesor:
    """
    Dependencia de FastAPI que valida el rol 'asesor' y devuelve el perfil
    de Asesor asociado a la cuenta actual del token.
    """
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado. Se requiere rol de asesor.")
    
    # La logica correcta es acceder a la relacion directa 'asesor' de la cuenta.
    asesor = cuenta_actual.asesor
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado para esta cuenta.")
    
    return asesor



@router_asesor.get("/dashboard", response_model=DashboardAsesorData)
def obtener_dashboard_asesor(
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    """
    Endpoint Dashboard Asesor.
    CORREGIDO: Muestra TODOS los casos (incluidos cerrados) en la lista principal,
    pero calcula la carga de trabajo SOLO con los activos.
    """
    # 1. LISTA PRINCIPAL (Historial completo sin duplicados)
    # Buscamos asignaciones que sean la "última vigente" o la "histórica cerrada".
    # Filtramos para que NO muestre "reasignado" (que son del pasado y ya no le tocan).
    query_casos = (
        select(Caso, Estudiante.nombre_completo)
        .join(Asignacion, Caso.id == Asignacion.id_caso)
        .join(Estudiante, Asignacion.id_estudiante == Estudiante.id)
        .where(Asignacion.id_asesor == asesor_actual.id)
        # CORRECCIÓN: Permitimos 'cerrado' para que aparezca en el historial
        .where(Asignacion.estado.in_(["pendiente", "aceptado", "en_progreso", "cerrado"])) 
        .order_by(Caso.fecha_creacion.desc())
    )
    resultados_casos = sesion.exec(query_casos).all()
    
    lista_procesada = []
    
    # 2. Procesar alertas
    for caso, nombre_est in resultados_casos:
        tiene_alerta = False
        if caso.notas:
            for nota in caso.notas:
                if nota.rol_autor == "sistema" and ("ALERTA" in nota.contenido or "🚨" in nota.contenido):
                    tiene_alerta = True
                    break
        
        lista_procesada.append(
            CasoSupervisadoLectura(
                id=caso.id, 
                descripcion_hechos=caso.descripcion_hechos, 
                estado=caso.estado, 
                fecha_creacion=caso.fecha_creacion, 
                nombre_estudiante=nombre_est,
                tiene_alerta=tiene_alerta
            )
        )

    # 3. Métricas de Carga (SOLO ACTIVOS)
    estados_activos = [
        EstadoCaso.ASIGNADO.value, 
        EstadoCaso.PENDIENTE_ACEPTACION.value,
        EstadoCaso.EN_REVISION.value
    ]
    
    query_metricas = (
        select(Estudiante.nombre_completo, func.count(Caso.id).label("total_casos"))
        .join(Asignacion, Estudiante.id == Asignacion.id_estudiante, isouter=True)
        .join(Caso, Asignacion.id_caso == Caso.id, isouter=True)
        .where(Asignacion.id_asesor == asesor_actual.id)
        .where(Asignacion.estado.in_(["pendiente", "aceptado"]))
        .where(Caso.estado.in_(estados_activos)) # Solo cuenta casos vivos
        .group_by(Estudiante.nombre_completo)
        .order_by(func.count(Caso.id).desc())
    )
    metricas_raw = sesion.exec(query_metricas).all()
    metricas = [MetricaEstudiante(nombre_estudiante=nombre, casos_asignados=total) for nombre, total in metricas_raw]
    
    return DashboardAsesorData(casos_supervisados=lista_procesada, metricas_carga_trabajo=metricas)

@router_asesor.get("/expedientes/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_detalle_expediente_asesor(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    """Obtiene la vista detallada de un expediente que el asesor supervisa."""
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor_actual.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente no encontrado o no tiene permiso para acceder a él.")

    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente no encontrado.")
    
    # Preparamos la respuesta base
    respuesta = CasoDetalleUsuario.model_validate(caso)
    
    # 1. Enriquecer las evidencias con el nombre del autor
    evidencias_enriquecidas = []
    for ev in caso.evidencias:
        autor_nombre = "Autor Desconocido"
        if ev.subido_por: 
            if ev.subido_por.rol == 'usuario' and ev.subido_por.usuario:
                autor_nombre = f"Usuario: {ev.subido_por.usuario.nombre}"
            elif ev.subido_por.rol == 'estudiante' and ev.subido_por.estudiante:
                autor_nombre = f"Estudiante: {ev.subido_por.estudiante.nombre_completo}"
        
        evidencias_enriquecidas.append(
            EvidenciaLecturaSimple(
                id=ev.id,
                nombre_archivo=ev.nombre_archivo,
                ruta_archivo=str(ev.ruta_archivo).replace("\\", "/").replace("backend/", "/"),
                estado=ev.estado,
                autor_nombre=autor_nombre
            )
        )
    respuesta.evidencias = evidencias_enriquecidas

    # 2. Enriquecer las notas con el nombre del autor
    notas_enriquecidas = []
    for nota in caso.notas:
        autor_nombre = "Autor Desconocido"
        if nota.autor: 
            if nota.autor.rol == 'usuario' and nota.autor.usuario:
                autor_nombre = nota.autor.usuario.nombre
            elif nota.autor.rol == 'estudiante' and nota.autor.estudiante:
                autor_nombre = nota.autor.estudiante.nombre_completo
            elif nota.autor.rol == 'asesor' and nota.autor.asesor:
                autor_nombre = nota.autor.asesor.nombre_completo

        notas_enriquecidas.append(
            NotaLectura(
                id=nota.id,
                contenido=nota.contenido,
                fecha_creacion=nota.fecha_creacion,
                rol_autor=nota.rol_autor,
                autor_nombre=autor_nombre,
                es_publica=nota.es_publica,
                # --- CORRECCIÓN CRÍTICA: Incluir el ID de evidencia ---
                id_evidencia=nota.id_evidencia 
                # -----------------------------------------------------
            )
        )
    respuesta.notas = sorted(notas_enriquecidas, key=lambda n: n.fecha_creacion, reverse=True)

    # 3. Añadir información de la asignación
    if caso.asignaciones:
        asignacion_info = caso.asignaciones[0]
        if asignacion_info.estudiante: respuesta.estudiante_asignado = asignacion_info.estudiante.nombre_completo
        if asignacion_info.asesor: respuesta.asesor_asignado = asignacion_info.asesor.nombre_completo
            
    return respuesta


@router_asesor.post("/expedientes/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_asesor(
    id_caso: int,
    solicitud: NotaCreacion, # Recibe contenido, es_publica e id_evidencia
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor_actual.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para añadir notas a este caso.")

    nueva_nota = Nota(
        id_caso=id_caso, 
        contenido=solicitud.contenido, 
        id_cuenta_autor=cuenta_actual.id, 
        rol_autor=cuenta_actual.rol,
        # --- NUEVOS CAMPOS ---
        es_publica=solicitud.es_publica,
        id_evidencia=solicitud.id_evidencia
        # ---------------------
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    return NotaLectura(
        id=nueva_nota.id,
        contenido=nueva_nota.contenido,
        fecha_creacion=nueva_nota.fecha_creacion,
        rol_autor=nueva_nota.rol_autor,
        autor_nombre=asesor_actual.nombre_completo,
        es_publica=nueva_nota.es_publica,
        id_evidencia=nueva_nota.id_evidencia
    )


@router_asesor.post("/expedientes/{id_caso}/finalizar", status_code=status.HTTP_200_OK)
def finalizar_caso(
    id_caso: int,
    datos_cierre: SolicitudCierreCaso,
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    """
    Cierra el caso y guarda la calificación del estudiante ACTUAL.
    """
    # 1. Buscar la asignación ACTIVA (La que no ha sido reasignada ni rechazada)
    # ESTO ES CRÍTICO: Si no filtramos por estado, podría calificar al estudiante anterior.
    asignacion = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso, 
            Asignacion.id_asesor == asesor_actual.id,
            Asignacion.estado.in_(["pendiente", "aceptado", "en_progreso"]) # <--- FILTRO CLAVE
        )
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=403, detail="No se encontró una asignación activa para calificar en este caso.")

    # 2. Buscar el caso
    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    
    # 3. Guardar la Evaluación Académica
    if datos_cierre.calificacion < 0 or datos_cierre.calificacion > 5:
        raise HTTPException(status_code=400, detail="La calificación debe ser entre 0 y 5.")

    asignacion.calificacion = datos_cierre.calificacion
    asignacion.comentario_docente = datos_cierre.comentario
    # Opcional: Cambiamos el estado de la asignación a 'cerrado' para limpieza interna
    asignacion.estado = "cerrado" 
    
    # 4. Cerrar el caso globalmente
    caso.estado = EstadoCaso.CERRADO.value
    
    # 5. Crear nota automática de cierre en el historial
    nota_cierre = Nota(
        id_caso=id_caso,
        contenido=f"🏁 CASO FINALIZADO.\nCalificación Final: {datos_cierre.calificacion}/5.0\nComentario: {datos_cierre.comentario}",
        id_cuenta_autor=asesor_actual.cuenta.id,
        rol_autor="sistema",
        es_publica=False # Privado para el equipo
    )
    
    sesion.add(asignacion)
    sesion.add(caso)
    sesion.add(nota_cierre)
    sesion.commit()
    
    return {"mensaje": f"El caso #{id_caso} ha sido evaluado y cerrado exitosamente."}


@router_asesor.get("/estudiantes-disponibles", response_model=List[EstudianteLecturaSimple])
def obtener_estudiantes_disponibles(
    sesion: Session = Depends(obtener_sesion),
    _: Asesor = Depends(obtener_asesor_actual)
):
    """
    Devuelve una lista de todos los estudiantes del sistema.
    """
    estudiantes = sesion.exec(select(Estudiante)).all()
    
    # --- INICIO DE LA CORRECCION ---
    # Construimos la respuesta manualmente para asegurar que tenga el formato correcto.
    resultado = []
    for est in estudiantes:
        if est.area: # Asegurarse de que la relación existe
            resultado.append(
                EstudianteLecturaSimple(
                    id=est.id,
                    nombre_completo=est.nombre_completo,
                    area_especialidad=est.area.nombre # <-- Usamos .area.nombre
                )
            )
    return resultado


@router_asesor.post("/expedientes/{id_caso}/reasignar", status_code=status.HTTP_200_OK)
def reasignar_caso(
    id_caso: int,
    solicitud: SolicitudReasignacion,
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    """
    Reasigna un caso automáticamente con lógica anti-bucle:
    1. Califica al estudiante actual.
    2. Busca un nuevo estudiante EXCLUYENDO a los que ya tuvieron este caso.
    3. Si no quedan estudiantes disponibles, lanza un error.
    """
    # 1. Obtener la asignación actual (la que está activa)
    asignacion_actual = sesion.exec(
        select(Asignacion).where(
            Asignacion.id_caso == id_caso, 
            Asignacion.id_asesor == asesor_actual.id,
            Asignacion.estado.in_(["pendiente", "aceptado", "en_progreso"]) # Estados activos
        )
    ).first()
    
    if not asignacion_actual:
        raise HTTPException(status_code=403, detail="No se puede reasignar: No supervisa este caso o ya está cerrado.")

    estudiante_saliente = asignacion_actual.estudiante
    id_area_caso = estudiante_saliente.id_area_especialidad

    # 2. Cerrar/Calificar la asignación actual
    asignacion_actual.estado = "reasignado"
    asignacion_actual.calificacion = solicitud.calificacion_saliente
    asignacion_actual.comentario_docente = f"[REASIGNADO] {solicitud.comentario_saliente}"
    sesion.add(asignacion_actual)

    # --- LÓGICA INTELIGENTE DE BÚSQUEDA (ANTI-BUCLE) ---
    
    # A. Identificar a TODOS los estudiantes que ya han tenido este caso
    historial_asignaciones = sesion.exec(
        select(Asignacion).where(Asignacion.id_caso == id_caso)
    ).all()
    ids_estudiantes_excluidos = [a.id_estudiante for a in historial_asignaciones]
    
    # B. Buscar candidatos: Estudiantes del MISMO ÁREA que NO estén en la lista de excluidos
    #    y ordenarlos por carga de trabajo (menor a mayor).
    
    # Consulta:
    # 1. Traer estudiantes del área.
    # 2. Filtrar los que NO están en la lista de excluidos.
    # 3. Hacer un Left Join con Asignaciones activas para contar su carga actual.
    query_candidatos = (
        select(Estudiante, func.count(Asignacion.id).label("carga"))
        .join(Asignacion, (Estudiante.id == Asignacion.id_estudiante) & (Asignacion.estado.in_(["pendiente", "aceptado"])), isouter=True)
        .where(Estudiante.id_area_especialidad == id_area_caso)
        .where(Estudiante.id.not_in(ids_estudiantes_excluidos)) # <--- EL FILTRO CLAVE
        .group_by(Estudiante.id)
        .order_by(func.count(Asignacion.id).asc()) # Menos carga primero
    )
    
    candidato_optimo = sesion.exec(query_candidatos).first()

    # C. Verificar si encontramos a alguien
    if not candidato_optimo:
        # Si no hay nadie, hacemos rollback de la calificación (opcional) o lanzamos error.
        # Aquí lanzamos error para que el asesor sepa que no puede reasignar más.
        raise HTTPException(
            status_code=409, # Conflict
            detail="No es posible reasignar: Ya no quedan más estudiantes disponibles en esta área que no hayan tenido este caso."
        )

    nuevo_estudiante = candidato_optimo[0] # El primer elemento de la tupla (Estudiante, carga)

    # 4. Crear NUEVA asignación para el nuevo estudiante
    nueva_asignacion = Asignacion(
        id_caso=id_caso,
        id_estudiante=nuevo_estudiante.id,
        id_asesor=asesor_actual.id,
        estado="pendiente"
    )
    sesion.add(nueva_asignacion)

    # 5. Registrar en Historial del Caso
    nota_sistema = Nota(
        id_caso=id_caso,
        contenido=(
            f"🔄 CASO REASIGNADO por Supervisor.\n"
            f"Saliente: {estudiante_saliente.nombre_completo} (Nota: {solicitud.calificacion_saliente}/5.0).\n"
            f"Entrante: {nuevo_estudiante.nombre_completo}."
        ),
        id_cuenta_autor=asesor_actual.cuenta.id,
        rol_autor="sistema",
        es_publica=False
    )
    sesion.add(nota_sistema)

    # Actualizar estado del caso
    caso = sesion.get(Caso, id_caso)
    caso.estado = EstadoCaso.PENDIENTE_ACEPTACION.value
    sesion.add(caso)

    sesion.commit()
    
    return {"mensaje": f"Caso reasignado exitosamente a {nuevo_estudiante.nombre_completo}."}

def validar_permiso_sobre_documento(id_evidencia: int, sesion: Session, asesor_actual: Asesor) -> Evidencia:
    """Función de utilidad para validar permisos del asesor sobre un documento."""
    documento = sesion.get(Evidencia, id_evidencia)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
    
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == documento.id_caso, Asignacion.id_asesor == asesor_actual.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No supervisa el caso de este documento.")
    return documento


@router_asesor.post("/documentos/{id_evidencia}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_documento(
    id_evidencia: int,
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    documento = validar_permiso_sobre_documento(id_evidencia, sesion, asesor_actual)
    if documento.estado != EstadoEvidencia.EN_REVISION.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden aprobar documentos 'en revisión'.")
    documento.estado = EstadoEvidencia.APROBADO.value
    sesion.add(documento)
    sesion.commit()
    return {"mensaje": "Documento aprobado."}


@router_asesor.post("/documentos/{id_evidencia}/solicitar-cambios", status_code=status.HTTP_200_OK)
def solicitar_cambios_documento(
    id_evidencia: int,
    sesion: Session = Depends(obtener_sesion),
    asesor_actual: Asesor = Depends(obtener_asesor_actual)
):
    documento = validar_permiso_sobre_documento(id_evidencia, sesion, asesor_actual)
    if documento.estado != EstadoEvidencia.EN_REVISION.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Acción no válida para el estado actual del documento.")
    documento.estado = EstadoEvidencia.CAMBIOS_SOLICITADOS.value
    sesion.add(documento)
    sesion.commit()
    return {"mensaje": "Solicitud de cambios enviada."}