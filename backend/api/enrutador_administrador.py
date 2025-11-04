#C:\react\asistente_legal_multimodal\backend\api\enrutador_administrador.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List



from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Cuenta,
    Estudiante,
    Asesor,
    PersonalCreacion,
    PersonalGestionLectura,
    PersonalEdicion,
    AreaEspecialidad,
    AreaLectura
)
# --- INICIO DE LA MODIFICACION: Corregir la importacion y el nombre de la funcion ---
from ..seguridad.contrasenas import obtener_hash_de_contrasena
# La dependencia correcta esta en jwt_manager y se llama obtener_cuenta_actual
from ..seguridad.jwt_manager import obtener_cuenta_actual
# --- FIN DE LA MODIFICACION ---

router = APIRouter(
    prefix="/api/administrador",
    tags=["Administrador"],
)

# =================================================================================
# FUNCION DE DEPENDENCIA PARA PROTEGER RUTAS
# =================================================================================

def obtener_administrador_actual(
    # --- INICIO DE LA MODIFICACION: Usar el nombre correcto de la funcion ---
    cuenta_actual: Cuenta = Depends(obtener_cuenta_actual),
    # --- FIN DE LA MODIFICACION ---
) -> Cuenta:
    """
    Una funcion de dependencia que reutiliza obtener_cuenta_actual,
    pero que ademas verifica que el rol de la cuenta sea 'administrador'.
    """
    if cuenta_actual.rol != "administrador":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador.",
        )
    return cuenta_actual

# =================================================================================
# ENDPOINTS DE GESTION DE PERSONAL
# =================================================================================

@router.post("/personal", response_model=PersonalGestionLectura, summary="Crear una nueva cuenta de personal")
def crear_personal(datos_personal: PersonalCreacion, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    if sesion.exec(select(Cuenta).where(Cuenta.email == datos_personal.email)).first():
        raise HTTPException(status_code=400, detail="Email ya en uso.")
    
    # --- INICIO DE LA MODIFICACION: Validar que el AreaEspecialidad exista ---
    area = sesion.get(AreaEspecialidad, datos_personal.id_area_especialidad)
    if not area:
        raise HTTPException(status_code=404, detail="El área de especialidad especificada no existe.")
    # --- FIN DE LA MODIFICACION ---

    hash_contrasena = obtener_hash_de_contrasena(datos_personal.contrasena)
    nueva_cuenta = Cuenta(email=datos_personal.email, contrasena_hash=hash_contrasena, rol=datos_personal.rol)
    sesion.add(nueva_cuenta)
    sesion.commit(); sesion.refresh(nueva_cuenta)

    # --- INICIO DE LA MODIFICACION: Usar id_area_especialidad ---
    if datos_personal.rol == "estudiante":
        perfil = Estudiante(nombre_completo=datos_personal.nombre_completo, id_area_especialidad=datos_personal.id_area_especialidad, id_cuenta=nueva_cuenta.id)
    else: # asesor
        perfil = Asesor(nombre_completo=datos_personal.nombre_completo, id_area_especialidad=datos_personal.id_area_especialidad, id_cuenta=nueva_cuenta.id)
    # --- FIN DE LA MODIFICACION ---

    sesion.add(perfil)
    sesion.commit(); sesion.refresh(perfil)
    
    return PersonalGestionLectura(id_cuenta=nueva_cuenta.id, email=nueva_cuenta.email, rol=nueva_cuenta.rol, esta_activo=nueva_cuenta.esta_activo, nombre_completo=perfil.nombre_completo, area_especialidad=area.nombre)


@router.get("/personal", response_model=List[PersonalGestionLectura], summary="Obtener la lista de todo el personal")
def obtener_todo_el_personal(sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    # --- INICIO DE LA CORRECCION ---
    # Obtenemos todos los perfiles, de Estudiantes y Asesores
    perfiles = sesion.exec(select(Estudiante)).all() + sesion.exec(select(Asesor)).all()
    resultado = []
    # Construimos la respuesta asegurándonos de que las relaciones .cuenta y .area existen
    for p in perfiles:
        if p.cuenta and p.area:
            resultado.append(
                PersonalGestionLectura(
                    id_cuenta=p.cuenta.id,
                    email=p.cuenta.email,
                    rol=p.cuenta.rol,
                    esta_activo=p.cuenta.esta_activo,
                    nombre_completo=p.nombre_completo,
                    area_especialidad=p.area.nombre # <-- Usamos .area.nombre
                )
            )
    return resultado




@router.post("/personal/{id_cuenta}/cambiar-estado", response_model=PersonalGestionLectura, summary="Activa o desactiva una cuenta")
def cambiar_estado_cuenta(id_cuenta: int, sesion: Session = Depends(obtener_sesion), admin_actual: Cuenta = Depends(obtener_administrador_actual)):
    if admin_actual.id == id_cuenta: raise HTTPException(status_code=400, detail="Un administrador no puede desactivar su propia cuenta.")
    cuenta = sesion.get(Cuenta, id_cuenta)
    if not cuenta: raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    perfil = cuenta.estudiante or cuenta.asesor
    if not perfil: raise HTTPException(status_code=404, detail="Perfil asociado no encontrado.")
    cuenta.esta_activo = not cuenta.esta_activo
    sesion.add(cuenta)
    sesion.commit(); sesion.refresh(cuenta)
    return PersonalGestionLectura(id_cuenta=cuenta.id, email=cuenta.email, rol=cuenta.rol, esta_activo=cuenta.esta_activo, nombre_completo=perfil.nombre_completo, area_especialidad=perfil.area.nombre)






@router.put("/personal/{id_cuenta}", response_model=PersonalGestionLectura, summary="Editar los datos de una cuenta de personal")
def editar_personal(id_cuenta: int, datos_edicion: PersonalEdicion, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    cuenta_a_editar = sesion.get(Cuenta, id_cuenta)
    if not cuenta_a_editar: raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    perfil_a_editar = cuenta_a_editar.estudiante or cuenta_a_editar.asesor
    if not perfil_a_editar: raise HTTPException(status_code=404, detail="Perfil asociado no encontrado.")

    if datos_edicion.nombre_completo is not None:
        perfil_a_editar.nombre_completo = datos_edicion.nombre_completo
    
    # --- INICIO DE LA MODIFICACION: Usar id_area_especialidad ---
    if datos_edicion.id_area_especialidad is not None:
        area_nueva = sesion.get(AreaEspecialidad, datos_edicion.id_area_especialidad)
        if not area_nueva:
            raise HTTPException(status_code=404, detail="La nueva área de especialidad no existe.")
        perfil_a_editar.id_area_especialidad = datos_edicion.id_area_especialidad
    # --- FIN DE LA MODIFICACION ---

    if datos_edicion.email is not None and datos_edicion.email != cuenta_a_editar.email:
        if sesion.exec(select(Cuenta).where(Cuenta.email == datos_edicion.email)).first():
            raise HTTPException(status_code=400, detail="El nuevo email ya está en uso.")
        cuenta_a_editar.email = datos_edicion.email
    if datos_edicion.contrasena:
        cuenta_a_editar.contrasena_hash = obtener_hash_de_contrasena(datos_edicion.contrasena)
    
    sesion.add(cuenta_a_editar); sesion.add(perfil_a_editar)
    sesion.commit(); sesion.refresh(cuenta_a_editar); sesion.refresh(perfil_a_editar)

    return PersonalGestionLectura(id_cuenta=cuenta_a_editar.id, email=cuenta_a_editar.email, rol=cuenta_a_editar.rol, 
                                  esta_activo=cuenta_a_editar.esta_activo, nombre_completo=perfil_a_editar.nombre_completo, 
                                  area_especialidad=perfil_a_editar.area.nombre)


@router.delete("/personal/{id_cuenta}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar una cuenta de personal")
def eliminar_personal(id_cuenta: int, sesion: Session = Depends(obtener_sesion), admin_actual: Cuenta = Depends(obtener_administrador_actual)):
    if admin_actual.id == id_cuenta: raise HTTPException(status_code=400, detail="Un administrador no puede eliminar su propia cuenta.")
    cuenta = sesion.get(Cuenta, id_cuenta)
    if not cuenta: raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    perfil = cuenta.estudiante or cuenta.asesor
    if perfil: sesion.delete(perfil)
    sesion.delete(cuenta)
    sesion.commit()
    return None



@router.get("/areas-especialidad", response_model=List[AreaLectura], summary="Obtener la lista de todas las áreas de especialidad")
def obtener_areas_especialidad(sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    """Devuelve una lista simple de todas las Áreas de Especialidad disponibles."""
    return sesion.exec(select(AreaEspecialidad).order_by(AreaEspecialidad.nombre)).all()