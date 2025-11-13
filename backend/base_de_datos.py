# backend/base_de_datos.py

import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session

# 1. Cargamos las variables de entorno desde el archivo .env
load_dotenv()

# 2. Leemos las credenciales de la base de datos
db_usuario = os.getenv("DB_USUARIO")
db_contrasena = os.getenv("DB_CONTRASENA")
db_host = os.getenv("DB_HOST")
db_puerto = os.getenv("DB_PUERTO")
db_nombre = os.getenv("DB_NOMBRE")

# 3. Construimos la "URL de Conexión" para PostgreSQL.
#    El formato es: "postgresql://usuario:contraseña@host:puerto/nombre_de_la_bd"
URL_CONEXION_BD = f"postgresql://{db_usuario}:{db_contrasena}@{db_host}:{db_puerto}/{db_nombre}"

# 4. Creamos el motor, que ahora apunta a nuestro servidor de PostgreSQL.
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