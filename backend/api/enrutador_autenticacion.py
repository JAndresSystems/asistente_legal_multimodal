# backend/api/enrutador_autenticacion.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import Cuenta, Usuario, Token, CuentaCreacion
from ..seguridad.contrasenas import obtener_hash_de_contrasena, verificar_contrasena
from ..seguridad.jwt_manager import crear_token_de_acceso

router_auth = APIRouter(tags=["Autenticacion"])

@router_auth.post("/registro", response_model=Usuario)
def registrar_nueva_cuenta(datos_cuenta: CuentaCreacion, sesion: Session = Depends(obtener_sesion)):
    """
    Endpoint para registrar una nueva cuenta de usuario.
    
    Args:
        datos_cuenta (CuentaCreacion): Datos de la cuenta a crear, incluyendo email, contrasena, nombre y cedula.
        sesion (Session): Sesión de la base de datos inyectada por FastAPI.

    Returns:
        Usuario: El perfil de usuario creado.

    Raises:
        HTTPException: Si el email ya existe (400) o si hay un error en los datos (400).
    """
    cuenta_existente = sesion.exec(select(Cuenta).where(Cuenta.email == datos_cuenta.email)).first()
    if cuenta_existente:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una cuenta registrada con este correo electronico.")
    contrasena_hasheada = obtener_hash_de_contrasena(datos_cuenta.contrasena)
    nueva_cuenta = Cuenta(email=datos_cuenta.email, contrasena_hash=contrasena_hasheada, rol="usuario")
    nuevo_usuario = Usuario(nombre=datos_cuenta.nombre, cedula=datos_cuenta.cedula, cuenta=nueva_cuenta)
    sesion.add(nuevo_usuario)
    sesion.commit()
    sesion.refresh(nuevo_usuario)
    return nuevo_usuario

@router_auth.post("/login", response_model=Token)
def iniciar_sesion_y_obtener_token(form_data: OAuth2PasswordRequestForm = Depends(), sesion: Session = Depends(obtener_sesion)):
    """
    Endpoint para iniciar sesión y obtener un token JWT.

    Args:
        form_data (OAuth2PasswordRequestForm): Datos de formulario con username (email) y password.
        sesion (Session): Sesión de la base de datos inyectada por FastAPI.

    Returns:
        Token: Token de acceso y tipo (bearer).

    Raises:
        HTTPException: Si las credenciales son incorrectas (401).
    """
    cuenta = sesion.exec(select(Cuenta).where(Cuenta.email == form_data.username)).first()
    if not cuenta or not verificar_contrasena(form_data.password, cuenta.contrasena_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Correo electronico o contraseña incorrectos", headers={"WWW-Authenticate": "Bearer"})
    
    # Ahora el token no solo sabrá QUIÉN es el usuario (sub), sino QUÉ es (rol).
    datos_para_el_token = {"sub": cuenta.email, "rol": cuenta.rol}
    
    tiempo_expiracion = timedelta(minutes=60)
    token_de_acceso = crear_token_de_acceso(data=datos_para_el_token, expires_delta=tiempo_expiracion)
    return {"access_token": token_de_acceso, "token_type": "bearer"}