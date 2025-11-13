# backend/seguridad/jwt_manager.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

# Importamos estos modelos para poder buscar en la base de datos
from ..api.modelos_compartidos import Cuenta
from ..base_de_datos import obtener_sesion

load_dotenv()

# --- CONFIGURACION DE SEGURIDAD JWT ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if SECRET_KEY is None:
    raise RuntimeError("La variable de entorno JWT_SECRET_KEY no está configurada. Por favor, añadala a su archivo .env")

# Esta linea crea un objeto que FastAPI usara para buscar el token.
# Le decimos que la URL para obtener el token es "/login".
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="login")


def crear_token_de_acceso(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def obtener_cuenta_actual(
    token: str = Depends(esquema_oauth2),
    sesion: Session = Depends(obtener_sesion)
) -> Cuenta:
    """
    Docstring:
    Esta es una dependencia de FastAPI. Es nuestro "Guardian".
    1. Extrae el token del encabezado de la peticion.
    2. Decodifica el token para obtener el email del usuario ('sub').
    3. Busca al usuario en la base de datos.
    4. Devuelve el objeto 'Cuenta' completo o lanza un error si algo falla.

    Args:
        token (str): El token JWT inyectado por FastAPI.
        sesion (Session): La sesion de la base de datos.

    Returns:
        Cuenta: El objeto de la cuenta del usuario autenticado.
    """
    credenciales_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credenciales_exception
    except JWTError:
        raise credenciales_exception
    
    cuenta = sesion.exec(select(Cuenta).where(Cuenta.email == email)).first()
    if cuenta is None:
        raise credenciales_exception
    
    if not cuenta.esta_activo:
        raise HTTPException(status_code=400, detail="Cuenta inactiva")

    return cuenta