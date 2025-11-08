#C:\react\asistente_legal_multimodal\backend\api\enrutador_administrador.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List,Dict




from ..base_de_datos import obtener_sesion
from .modelos_compartidos import (
    Cuenta,
    Usuario,
    Estudiante,
    Asesor,
    PersonalCreacion,
    PersonalGestionLectura,
    UsuarioGestionLectura, 
    UsuarioEdicion,
    PersonalEdicion,
    AreaEspecialidad,
    AreaLectura,
    AreaCreacionEdicion,
    SupervisionAsignacion, 
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
    resultado = []
    
    # Procesamos a los estudiantes primero para poder añadir el nombre del supervisor
    estudiantes = sesion.exec(select(Estudiante)).all()
    for p in estudiantes:
        if p.cuenta and p.area:
            # Gracias a la relación, podemos acceder a p.supervisor directamente
            nombre_supervisor = p.supervisor.nombre_completo if p.supervisor else None
            resultado.append(
                PersonalGestionLectura(
                    id_cuenta=p.cuenta.id, email=p.cuenta.email, rol=p.cuenta.rol,
                    esta_activo=p.cuenta.esta_activo, nombre_completo=p.nombre_completo,
                    area_especialidad=p.area.nombre,
                    nombre_supervisor=nombre_supervisor # <-- Añadimos el nuevo dato
                )
            )
            
    # Procesamos a los asesores
    asesores = sesion.exec(select(Asesor)).all()
    for p in asesores:
        if p.cuenta and p.area:
            resultado.append(
                PersonalGestionLectura(
                    id_cuenta=p.cuenta.id, email=p.cuenta.email, rol=p.cuenta.rol,
                    esta_activo=p.cuenta.esta_activo, nombre_completo=p.nombre_completo,
                    area_especialidad=p.area.nombre
                    # No se necesita nombre_supervisor para un asesor, el default es None
                )
            )
            
    return resultado




@router.post("/personal/{id_cuenta}/cambiar-estado", response_model=PersonalGestionLectura, summary="Activa o desactiva una cuenta de personal")
def cambiar_estado_cuenta(id_cuenta: int, sesion: Session = Depends(obtener_sesion), admin_actual: Cuenta = Depends(obtener_administrador_actual)):
    if admin_actual.id == id_cuenta: raise HTTPException(status_code=400, detail="Un administrador no puede desactivar su propia cuenta.")
    cuenta = sesion.get(Cuenta, id_cuenta)
    if not cuenta: raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    
    # Esta lógica asume que la cuenta es de personal
    perfil = cuenta.estudiante or cuenta.asesor
    if not perfil: raise HTTPException(status_code=404, detail="Perfil de personal asociado no encontrado.")
    
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





@router.get("/areas-especialidad", response_model=List[AreaLectura], summary="Obtener la lista de todas las áreas de especialidad")
def obtener_areas_especialidad(sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    """Devuelve una lista simple de todas las Áreas de Especialidad disponibles."""
    return sesion.exec(select(AreaEspecialidad).order_by(AreaEspecialidad.nombre)).all()

@router.post("/areas-especialidad", response_model=AreaLectura, status_code=status.HTTP_201_CREATED, summary="Crear una nueva área de especialidad")
def crear_area_especialidad(datos_area: AreaCreacionEdicion, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    # Verificamos si ya existe un area con ese nombre para evitar duplicados
    area_existente = sesion.exec(select(AreaEspecialidad).where(AreaEspecialidad.nombre == datos_area.nombre)).first()
    if area_existente:
        raise HTTPException(status_code=409, detail="Ya existe un área con este nombre.")
    
    nueva_area = AreaEspecialidad.from_orm(datos_area)
    sesion.add(nueva_area)
    sesion.commit()
    sesion.refresh(nueva_area)
    return nueva_area

@router.put("/areas-especialidad/{id_area}", response_model=AreaLectura, summary="Actualizar el nombre de un área de especialidad")
def actualizar_area_especialidad(id_area: int, datos_area: AreaCreacionEdicion, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    area_a_actualizar = sesion.get(AreaEspecialidad, id_area)
    if not area_a_actualizar:
        raise HTTPException(status_code=404, detail="Área no encontrada.")
    
    # Verificamos si el nuevo nombre ya esta en uso por OTRA area
    conflicto = sesion.exec(select(AreaEspecialidad).where(AreaEspecialidad.nombre == datos_area.nombre, AreaEspecialidad.id != id_area)).first()
    if conflicto:
        raise HTTPException(status_code=409, detail="Ya existe otra área con este nombre.")
        
    area_a_actualizar.nombre = datos_area.nombre
    sesion.add(area_a_actualizar)
    sesion.commit()
    sesion.refresh(area_a_actualizar)
    return area_a_actualizar

@router.delete("/areas-especialidad/{id_area}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar un área de especialidad")
def eliminar_area_especialidad(id_area: int, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    area_a_eliminar = sesion.get(AreaEspecialidad, id_area)
    if not area_a_eliminar:
        raise HTTPException(status_code=404, detail="Área no encontrada.")
        
    # REGLA DE NEGOCIO: No permitir eliminar si hay personal asignado a esta area
    personal_asignado = sesion.exec(select(Estudiante).where(Estudiante.id_area_especialidad == id_area)).first() or \
                        sesion.exec(select(Asesor).where(Asesor.id_area_especialidad == id_area)).first()
    
    if personal_asignado:
        raise HTTPException(status_code=409, detail="No se puede eliminar el área, hay personal asignado a ella.")
        
    sesion.delete(area_a_eliminar)
    sesion.commit()
    return None




# =================================================================================
# ENDPOINTS DE GESTION DE USUARIOS (CIUDADANOS)
# =================================================================================

@router.get("/usuarios", response_model=List[UsuarioGestionLectura], summary="Obtener la lista de todos los usuarios (ciudadanos)")
def obtener_todos_los_usuarios(sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    """
    Devuelve una lista de todos los perfiles de Usuario (ciudadanos) con
    la informacion de su cuenta asociada.
    """
    # Buscamos directamente las cuentas con rol 'usuario' para mayor eficiencia
    cuentas_usuario = sesion.exec(select(Cuenta).where(Cuenta.rol == "usuario")).all()
    resultado = []
    for cuenta in cuentas_usuario:
        # La relación .usuario debería existir si el rol es 'usuario'
        if cuenta.usuario:
            resultado.append(
                UsuarioGestionLectura(
                    id_cuenta=cuenta.id,
                    email=cuenta.email,
                    # El nombre se obtiene desde el perfil de usuario asociado
                    nombre_completo=cuenta.usuario.nombre, 
                    esta_activo=cuenta.esta_activo
                )
            )
    return resultado



@router.post("/usuarios/{id_cuenta}/cambiar-estado", response_model=UsuarioGestionLectura, summary="Activa o desactiva una cuenta de usuario (ciudadano)")
def cambiar_estado_cuenta_usuario(id_cuenta: int, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    cuenta = sesion.get(Cuenta, id_cuenta)
    # Validamos que la cuenta exista y sea de un usuario
    if not cuenta or cuenta.rol != 'usuario':
        raise HTTPException(status_code=404, detail="Cuenta de usuario no encontrada.")
    
    perfil = cuenta.usuario
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil de usuario asociado no encontrado.")

    cuenta.esta_activo = not cuenta.esta_activo
    sesion.add(cuenta)
    sesion.commit()
    sesion.refresh(cuenta)

    return UsuarioGestionLectura(
        id_cuenta=cuenta.id,
        email=cuenta.email,
        nombre_completo=perfil.nombre,
        esta_activo=cuenta.esta_activo
    )



@router.put("/usuarios/{id_cuenta}", response_model=UsuarioGestionLectura, summary="Editar los datos de una cuenta de usuario (ciudadano)")
def editar_usuario(id_cuenta: int, datos_edicion: UsuarioEdicion, sesion: Session = Depends(obtener_sesion), _: Cuenta = Depends(obtener_administrador_actual)):
    """
    Permite al administrador editar el nombre, la cédula y la contraseña de un usuario ciudadano.
    """
    cuenta_a_editar = sesion.get(Cuenta, id_cuenta)
    if not cuenta_a_editar or cuenta_a_editar.rol != 'usuario':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cuenta de usuario no encontrada.")
    
    perfil_a_editar = cuenta_a_editar.usuario
    if not perfil_a_editar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil de usuario asociado no encontrado.")

    # Actualizar los datos del perfil si se proporcionaron
    if datos_edicion.nombre is not None:
        perfil_a_editar.nombre = datos_edicion.nombre
    
    if datos_edicion.cedula is not None and datos_edicion.cedula != perfil_a_editar.cedula:
        # Validar que la nueva cédula no esté ya en uso por otro usuario
        conflicto = sesion.exec(select(Usuario).where(Usuario.cedula == datos_edicion.cedula)).first()
        if conflicto:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La cédula proporcionada ya está en uso.")
        perfil_a_editar.cedula = datos_edicion.cedula
    
    # Actualizar la contraseña si se proporcionó una nueva
    if datos_edicion.contrasena:
        cuenta_a_editar.contrasena_hash = obtener_hash_de_contrasena(datos_edicion.contrasena)
    
    sesion.add(cuenta_a_editar)
    sesion.add(perfil_a_editar)
    sesion.commit()
    sesion.refresh(cuenta_a_editar)
    sesion.refresh(perfil_a_editar)

    return UsuarioGestionLectura(
        id_cuenta=cuenta_a_editar.id,
        email=cuenta_a_editar.email,
        nombre_completo=perfil_a_editar.nombre,
        esta_activo=cuenta_a_editar.esta_activo
    )




@router.post("/supervision/asignar", status_code=status.HTTP_200_OK, response_model=Dict[str, str], summary="Asigna un asesor supervisor a una lista de estudiantes")
def asignar_supervisor_a_estudiantes(
    asignacion: SupervisionAsignacion,
    sesion: Session = Depends(obtener_sesion),
    _: Cuenta = Depends(obtener_administrador_actual)
):
    # Paso 1: "Traducir" el id_cuenta del asesor a su id de perfil.
    asesor = sesion.exec(select(Asesor).join(Cuenta).where(Cuenta.id == asignacion.id_asesor)).first()
    if not asesor:
        raise HTTPException(status_code=404, detail=f"El asesor con id_cuenta {asignacion.id_asesor} no fue encontrado.")
    
    id_perfil_asesor = asesor.id # Este es el ID que va en la columna 'id_asesor_supervisor'.

    # Paso 2: Obtener la lista de IDs de CUENTA de los estudiantes que se deben asignar.
    ids_cuenta_estudiantes_a_asignar = set(asignacion.ids_estudiantes)

    # Paso 3: Desvincular a cualquier estudiante que esté asignado a este asesor pero que NO esté en la nueva lista.
    estudiantes_actuales = sesion.exec(select(Estudiante).where(Estudiante.id_asesor_supervisor == id_perfil_asesor)).all()
    for est in estudiantes_actuales:
        if est.id_cuenta not in ids_cuenta_estudiantes_a_asignar:
            print(f"-> Desvinculando a estudiante ID de cuenta {est.id_cuenta} del asesor {asesor.nombre_completo}")
            est.id_asesor_supervisor = None
            sesion.add(est)

    # Paso 4: Vincular a todos los estudiantes de la nueva lista con este asesor.
    # Esto corregirá automáticamente a los que tenían otro supervisor o no tenían ninguno.
    if ids_cuenta_estudiantes_a_asignar:
        estudiantes_a_vincular = sesion.exec(
            select(Estudiante).join(Cuenta).where(Cuenta.id.in_(ids_cuenta_estudiantes_a_asignar))
        ).all()

        for est in estudiantes_a_vincular:
            if est.id_asesor_supervisor != id_perfil_asesor:
                print(f"-> Vinculando a estudiante ID de cuenta {est.id_cuenta} con el asesor {asesor.nombre_completo}")
                est.id_asesor_supervisor = id_perfil_asesor
                sesion.add(est)
            
    sesion.commit()
    
    return {"mensaje": "Asignación de supervisión actualizada correctamente."}