#C:\react\asistente_legal_multimodal\backend\api\enrutador_asesor.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select,func 
from typing import List

from ..base_de_datos import obtener_sesion
from ..seguridad.jwt_manager import obtener_cuenta_actual
from .modelos_compartidos import (
    Cuenta,
    Asesor,
    Asignacion,
    Caso,
    Estudiante,
    Evidencia,
    EstudianteLecturaSimple, 
    SolicitudReasignacion, 
    CasoSupervisadoLectura,
    CasoDetalleUsuario,
    EvidenciaLecturaSimple,
    Nota,                 
    NotaCreacion,         
    NotaLectura,    
    EstadoCaso,
    EstadoEvidencia,
    DashboardAsesorData, 
    MetricaEstudiante  
)

# --- CONFIGURACION DEL ENRUTADOR PARA EL ASESOR ---

router_asesor = APIRouter(
    prefix="/asesor",
    tags=["Asesor (Supervisor)"],
    dependencies=[Depends(obtener_cuenta_actual)]
)

# --- ENDPOINTS DEL ASESOR ---

@router_asesor.get("/dashboard", response_model=DashboardAsesorData)
def obtener_dashboard_asesor(
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Endpoint para que un asesor obtenga los datos completos de su dashboard:
    1. La lista de todos los casos que supervisa.
    2. Las métricas de carga de trabajo de sus estudiantes.
    """
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario no encontrado.")
    
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado.")

    # Consulta 1: Obtener la lista detallada de casos supervisados
    query_casos = (
        select(Caso, Estudiante.nombre_completo)
        .join(Asignacion, Caso.id == Asignacion.id_caso)
        .join(Estudiante, Asignacion.id_estudiante == Estudiante.id)
        .where(Asignacion.id_asesor == asesor.id)
        .order_by(Caso.fecha_creacion.desc())
    )
    resultados_casos = sesion.exec(query_casos).all()
    lista_casos_supervisados = [
        CasoSupervisadoLectura(id=c.id, descripcion_hechos=c.descripcion_hechos, estado=c.estado, fecha_creacion=c.fecha_creacion, nombre_estudiante=ne)
        for c, ne in resultados_casos
    ]

    # Consulta 2: Calcular las métricas de carga de trabajo de estudiantes activos
    estados_activos = [EstadoCaso.ASIGNADO.value, EstadoCaso.PENDIENTE_ACEPTACION.value]
    query_metricas = (
        select(Estudiante.nombre_completo, func.count(Caso.id).label("total_casos"))
        .join(Asignacion, Estudiante.id == Asignacion.id_estudiante, isouter=True)
        .join(Caso, Asignacion.id_caso == Caso.id, isouter=True)
        .where(Asignacion.id_asesor == asesor.id)
        .where(Caso.estado.in_(estados_activos))
        .group_by(Estudiante.nombre_completo)
        .order_by(func.count(Caso.id).desc())
    )
    resultados_metricas = sesion.exec(query_metricas).all()
    lista_metricas = [
        MetricaEstudiante(nombre_estudiante=nombre, casos_asignados=total)
        for nombre, total in resultados_metricas
    ]
    
    return DashboardAsesorData(
        casos_supervisados=lista_casos_supervisados,
        metricas_carga_trabajo=lista_metricas
    )



@router_asesor.get("/expedientes/{id_caso}", response_model=CasoDetalleUsuario)
def obtener_detalle_expediente_asesor(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario no encontrado.")
    
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado.")

    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente no encontrado o no tiene permiso para acceder a él.")

    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente no encontrado.")
    
    respuesta = CasoDetalleUsuario.model_validate(caso)
    
    if caso.evidencias:
        respuesta.evidencias = []
        for evidencia in caso.evidencias:
            ruta_normalizada = str(evidencia.ruta_archivo).replace("\\", "/")
            prefijo = "backend/archivos_subidos/"
            ruta_relativa = ruta_normalizada[len(prefijo):] if ruta_normalizada.startswith(prefijo) else ruta_normalizada
            url_final_archivo = f"/archivos_subidos/{ruta_relativa}"
            respuesta.evidencias.append(
                EvidenciaLecturaSimple(
                    id=evidencia.id,
                    nombre_archivo=evidencia.nombre_archivo,
                    ruta_archivo=url_final_archivo,
                    estado=evidencia.estado  # <-- ESTA ES LA LÍNEA QUE FALTABA
                )
            )

    if caso.asignaciones:
        asignacion_info = caso.asignaciones[0]
        if asignacion_info.estudiante:
            respuesta.estudiante_asignado = asignacion_info.estudiante.nombre_completo
        if asignacion_info.asesor:
            respuesta.asesor_asignado = asignacion_info.asesor.nombre_completo
            
    return respuesta



@router_asesor.post("/expedientes/{id_caso}/crear-nota", response_model=NotaLectura, status_code=status.HTTP_201_CREATED)
def crear_nota_asesor(
    id_caso: int,
    solicitud: NotaCreacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un asesor añadir una nota de supervision a un caso.
    """
    # 1. Validar rol y encontrar perfil del asesor (reutilizamos la misma logica)
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario no encontrado.")
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado.")

    # 2. Validacion de seguridad: El asesor debe estar asignado al caso.
    asignacion = sesion.exec(
        select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor.id)
    ).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403, detail="No tiene permiso para añadir notas a este caso.")

    # 3. Creacion del objeto Nota en la base de datos
    nueva_nota = Nota(
        id_caso=id_caso,
        contenido=solicitud.contenido,
        id_cuenta_autor=cuenta_actual.id,
        rol_autor=cuenta_actual.rol  # <-- CAMBIO CLAVE AQUI: Se guarda "asesor"
    )
    sesion.add(nueva_nota)
    sesion.commit()
    sesion.refresh(nueva_nota)
    
    return nueva_nota




@router_asesor.post("/expedientes/{id_caso}/finalizar", status_code=status.HTTP_200_OK)
def finalizar_caso(
    id_caso: int,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un asesor marcar un caso como 'cerrado'.
    """
    # 1. Validar rol y encontrar perfil del asesor
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")
    if not cuenta_actual.usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario no encontrado.")
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado.")

    # 2. Validacion de seguridad: El asesor debe estar asignado al caso.
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403, detail="No tiene permiso para modificar este caso.")

    # 3. Obtener el caso y modificar su estado
    caso = sesion.get(Caso, id_caso)
    if not caso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado.")
    
    if caso.estado == EstadoCaso.CERRADO.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El caso ya se encuentra finalizado.")

    caso.estado = EstadoCaso.CERRADO.value # <-- CAMBIO CLAVE
    
    sesion.add(caso)
    sesion.commit()
    sesion.refresh(caso)
    
    return {"mensaje": f"El caso #{id_caso} ha sido marcado como finalizado.", "caso": caso}



@router_asesor.get("/estudiantes-disponibles", response_model=List[EstudianteLecturaSimple])
def obtener_estudiantes_disponibles(
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Devuelve una lista de todos los estudiantes del sistema.
    Util para que un asesor pueda seleccionar a quien reasignar un caso.
    """
    # 1. Validar que el rol del usuario sea 'asesor'.
    if cuenta_actual.rol != "asesor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de asesor."
        )

    # 2. Obtener todos los estudiantes de la base de datos.
    estudiantes = sesion.exec(select(Estudiante).order_by(Estudiante.nombre_completo)).all()
    
    # 3. FastAPI se encargará de convertir la lista de objetos Estudiante
    #    a una lista de objetos EstudianteLecturaSimple gracias al response_model.
    return estudiantes




@router_asesor.post("/expedientes/{id_caso}/reasignar", status_code=status.HTTP_200_OK)
def reasignar_caso(
    id_caso: int,
    solicitud: SolicitudReasignacion,
    sesion: Session = Depends(obtener_sesion),
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)
):
    """
    Permite a un asesor cambiar el estudiante asignado a un caso.
    """
    # 1. Validacion de seguridad (rol de asesor y supervision del caso)
    if cuenta_actual.rol != "asesor": raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    if not cuenta_actual.usuario: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == id_caso, Asignacion.id_asesor == asesor.id)).first()
    if not asignacion: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No supervisa este caso.")

    # 2. Validacion de datos de entrada
    nuevo_estudiante = sesion.get(Estudiante, solicitud.id_nuevo_estudiante)
    if not nuevo_estudiante:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El estudiante seleccionado no existe.")

    if asignacion.id_estudiante == nuevo_estudiante.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El caso ya está asignado a este estudiante.")

    # 3. Logica de Reasignacion
    # Actualizamos la asignacion existente
    asignacion.id_estudiante = nuevo_estudiante.id
    asignacion.estado = "pendiente" # <-- CAMBIO CLAVE: El nuevo estudiante debe aceptar

    # Actualizamos el estado del caso para que aparezca en el dashboard del nuevo estudiante
    caso = sesion.get(Caso, id_caso)
    if caso:
        caso.estado = EstadoCaso.PENDIENTE_ACEPTACION.value # <-- CAMBIO CLAVE
        sesion.add(caso)

    sesion.add(asignacion)
    sesion.commit()
    
    return {"mensaje": f"El caso #{id_caso} ha sido reasignado a {nuevo_estudiante.nombre_completo}. Queda pendiente de su aceptación."}





def validar_permiso_sobre_documento(id_evidencia: int, sesion: Session, cuenta_actual: Cuenta) -> Evidencia:
    """Función de utilidad para validar permisos del asesor sobre un documento."""
    if cuenta_actual.rol != "asesor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acción no permitida.")
    
    documento = sesion.get(Evidencia, id_evidencia)
    if not documento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")
        
    asesor = sesion.exec(select(Asesor).where(Asesor.nombre_completo == cuenta_actual.usuario.nombre)).first()
    if not asesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de asesor no encontrado.")

    asignacion = sesion.exec(select(Asignacion).where(Asignacion.id_caso == documento.id_caso, Asignacion.id_asesor == asesor.id)).first()
    if not asignacion:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No supervisa el caso de este documento.")
        
    return documento

@router_asesor.post("/documentos/{id_evidencia}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_documento(id_evidencia: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    documento = validar_permiso_sobre_documento(id_evidencia, sesion, cuenta_actual)
    
    if documento.estado != EstadoEvidencia.EN_REVISION.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Solo se pueden aprobar documentos 'en revisión'. Estado actual: '{documento.estado}'.")
        
    documento.estado = EstadoEvidencia.APROBADO.value
    sesion.add(documento)
    sesion.commit()
    
    return {"mensaje": f"El documento '{documento.nombre_archivo}' ha sido aprobado."}

@router_asesor.post("/documentos/{id_evidencia}/solicitar-cambios", status_code=status.HTTP_200_OK)
def solicitar_cambios_documento(id_evidencia: int, sesion: Session = Depends(obtener_sesion), cuenta_actual: Cuenta = Depends(obtener_cuenta_actual)):
    documento = validar_permiso_sobre_documento(id_evidencia, sesion, cuenta_actual)

    if documento.estado != EstadoEvidencia.EN_REVISION.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se pueden solicitar cambios para este documento. Estado actual: '{documento.estado}'.")

    documento.estado = EstadoEvidencia.CAMBIOS_SOLICITADOS.value
    sesion.add(documento)
    sesion.commit()
    
    return {"mensaje": f"Se han solicitado cambios para el documento '{documento.nombre_archivo}'."}