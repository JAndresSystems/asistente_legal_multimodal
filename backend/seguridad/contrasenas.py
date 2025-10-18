# backend\seguridad\contrasenas.py

from passlib.context import CryptContext

# 1. Creamos un contexto de criptografia.
#    Le decimos que el esquema de hashing por defecto sera "bcrypt".
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contrasena(contrasena_plana: str, contrasena_hash: str) -> bool:
    """
    Docstring:
    Compara una contraseña en texto plano con su version hasheada para ver si coinciden.

    Args:
        contrasena_plana (str): La contraseña que el usuario envia en el login.
        contrasena_hash (str): La contraseña hasheada que esta guardada en la BD.

    Returns:
        bool: True si las contraseñas coinciden, False en caso contrario.
    """
    return pwd_context.verify(contrasena_plana, contrasena_hash)

def obtener_hash_de_contrasena(contrasena: str) -> str:
    """
    Docstring:
    Toma una contraseña en texto plano y devuelve su version hasheada y segura.

    Args:
        contrasena (str): La contraseña en texto plano.

    Returns:
        str: La contraseña hasheada, lista para ser guardada en la BD.
    """
    return pwd_context.hash(contrasena)