# backend/base_de_datos.py

import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session


# 1. Intentamos obtener la URL de conexión directamente desde el entorno (ideal para Render)
URL_CONEXION_BD = os.getenv("DATABASE_URL")

# 2. Si no se encuentra, asumimos un entorno de desarrollo local y cargamos .env
if not URL_CONEXION_BD:
    print("SETUP-DATABASE: No se encontró DATABASE_URL. Intentando cargar desde el archivo .env...")
    load_dotenv()
    
    DB_USUARIO = os.getenv("DB_USUARIO")
    DB_CONTRASENA = os.getenv("DB_CONTRASENA")
    DB_HOST = os.getenv("DB_HOST")
    DB_PUERTO = os.getenv("DB_PUERTO")
    DB_NOMBRE = os.getenv("DB_NOMBRE")
    
    # Verificamos que todas las variables locales necesarias existan
    if not all([DB_USUARIO, DB_CONTRASENA, DB_HOST, DB_PUERTO, DB_NOMBRE]):
        print("SETUP-DATABASE-ERROR: Faltan una o más variables de base de datos en el archivo .env")
        URL_CONEXION_BD = None # Nos aseguramos que sea None si faltan datos
    else:
        URL_CONEXION_BD = f"postgresql://{DB_USUARIO}:{DB_CONTRASENA}@{DB_HOST}:{DB_PUERTO}/{DB_NOMBRE}"
        print("SETUP-DATABASE: URL de conexión construida desde .env")

# 3. Verificación final y CRÍTICA. Si después de todo, la URL no es válida, detenemos el programa.
if not URL_CONEXION_BD:
    raise ValueError("ERROR CRÍTICO: La URL de conexión a la base de datos (DATABASE_URL) no pudo ser configurada. El programa no puede continuar.")

# 4. Si la URL es válida, creamos el motor.
# Esta línea ahora solo se ejecutará si URL_CONEXION_BD es un string válido.
motor = create_engine(URL_CONEXION_BD, echo=False)



def inicializar_base_de_datos():
    """
    Crea todas las tablas en la base de datos PostgreSQL si no existen.
    La lógica es la misma que antes, solo que ahora opera sobre el nuevo 'motor'.
    """
    print("SETUP-DATABASE: Conectando a PostgreSQL y creando tablas si es necesario...")
    SQLModel.metadata.create_all(motor)
    print("SETUP-DATABASE: ¡Tablas listas en PostgreSQL!")


def obtener_sesion():
    """
    Genera una nueva sesión de base de datos. Esta función no necesita cambios.
    """
    with Session(motor) as sesion:
        yield sesion