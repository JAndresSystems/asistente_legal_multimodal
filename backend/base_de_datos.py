import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session


# Lógica de doble entorno para la conexión a la BD


# 1. Intentamos obtener la URL de conexión directamente del entorno (para Render).
URL_CONEXION_BD = os.getenv("DATABASE_URL")

# 2. Si no la encontramos, asumimos que estamos en un entorno local y cargamos desde .env.
if not URL_CONEXION_BD:
    print("INFO:     No se encontró DATABASE_URL. Cargando desde archivo .env local...")
    load_dotenv()
    
    # Leemos las credenciales individuales del archivo .env
    db_usuario = os.getenv("DB_USUARIO")
    db_contrasena = os.getenv("DB_CONTRASENA")
    db_host = os.getenv("DB_HOST")
    db_puerto = os.getenv("DB_PUERTO")
    db_nombre = os.getenv("DB_NOMBRE")

    # Construimos la URL de Conexión para PostgreSQL.
    URL_CONEXION_BD = f"postgresql://{db_usuario}:{db_contrasena}@{db_host}:{db_puerto}/{db_nombre}"



# 3. Creamos el motor, que ahora usará la URL de conexión correcta para el entorno actual.
motor = create_engine(URL_CONEXION_BD, echo=False)


def inicializar_base_de_datos():
    """
    Crea todas las tablas en la base de datos si no existen.
    """
    print("SETUP-DATABASE: Conectando a la base de datos y creando tablas si es necesario...")
    SQLModel.metadata.create_all(motor)
    print("SETUP-DATABASE: ¡Tablas listas!")


def obtener_sesion():
    """
    Genera una nueva sesión de base de datos.
    """
    with Session(motor) as sesion:
        yield sesion