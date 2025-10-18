# backend/api/enrutador_autenticacion.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta

from ..base_de_datos import obtener_sesion
from .modelos_compartidos import Cuenta, Usuario, Token, CuentaCreacion

# ==============================================================================
# INICIO DE LA CORRECCION: Actualizamos las rutas de importacion
# ==============================================================================
from ..seguridad.contrasenas import obtener_hash_de_contrasena, verificar_contrasena
from ..seguridad.jwt_manager import crear_token_de_acceso
# ==============================================================================
# FIN DE LA CORRECCION
# ==============================================================================

# --- CONFIGURACION DEL ENRUTADOR ---
router_auth = APIRouter(tags=["Autenticacion"])

# --- ENDPOINTS ---

@router_auth.post("/registro", response_model=Usuario)
def registrar_nueva_cuenta(
    datos_cuenta: CuentaCreacion, 
    sesion: Session = Depends(obtener_sesion)
):
    """
    Docstring:
    Endpoint para que un nuevo usuario (ciudadano) se registre en el sistema.
    Crea la Cuenta de autenticacion y el perfil de Usuario asociado.
    """
    cuenta_existente = sesion.exec(select(Cuenta).where(Cuenta.email == datos_cuenta.email)).first()
    if cuenta_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta registrada con este correo electronico.",
        )

    contrasena_hasheada = obtener_hash_de_contrasena(datos_cuenta.contrasena)

    nueva_cuenta = Cuenta(
        email=datos_cuenta.email,
        contrasena_hash=contrasena_hasheada,
        rol="usuario"
    )
    
    nuevo_usuario = Usuario(
        nombre=datos_cuenta.nombre,
        cedula=datos_cuenta.cedula,
        cuenta=nueva_cuenta
    )

    sesion.add(nuevo_usuario)
    sesion.commit()
    sesion.refresh(nuevo_usuario)

    return nuevo_usuario

@router_auth.post("/login", response_model=Token)
def iniciar_sesion_y_obtener_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    sesion: Session = Depends(obtener_sesion)
):
    """
    Docstring:
    Endpoint para la autenticacion de usuarios. Recibe email (username) y contraseña.
    Si las credenciales son validas, devuelve un token de acceso JWT.
    """
    cuenta = sesion.exec(select(Cuenta).where(Cuenta.email == form_data.username)).first()

    if not cuenta or not verificar_contrasena(form_data.password, cuenta.contrasena_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electronico o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tiempo_expiracion = timedelta(minutes=30)
    token_de_acceso = crear_token_de_acceso(
        data={"sub": cuenta.email}, expires_delta=tiempo_expiracion
    )

    return {"access_token": token_de_acceso, "token_type": "bearer"}