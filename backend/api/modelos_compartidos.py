#C:\react\asistente_legal_multimodal\backend\api\modelos_compartidos.py
from sqlmodel import Field, SQLModel, Relationship, Column, Text
from typing import Optional, List

# =================================================================================
# MODELOS DE TABLAS DE BASE DE DATOS
# =================================================================================

from enum import Enum

from datetime import datetime

# MODELOS DE TABLAS DE BASE DE DATOS



#  Definimos los estados posibles para un caso

class EstadoCaso(str, Enum):
    """
    Define los unicos valores permitidos para el estado de un caso,
    evitando errores de tipeo en la base de datos y el codigo.
    """
    EN_REVISION = "en_revision"
    ASIGNADO = "asignado"
    RECHAZADO = "rechazado"
    CERRADO = "cerrado"


# --- INICIO DE LA MODIFICACION: Nuevo modelo para Cuentas ---
class Cuenta(SQLModel, table=True):
    """
    Docstring:
    Representa la cuenta de autenticacion de cualquier actor en el sistema.
    Almacena las credenciales de acceso y el rol que determina sus permisos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    contrasena_hash: str
    rol: str = Field(default="usuario") # Roles: "usuario", "estudiante", "asesor", "administrador"
    esta_activo: bool = Field(default=True)

    usuario: Optional["Usuario"] = Relationship(back_populates="cuenta")
    estudiante: Optional["Estudiante"] = Relationship(back_populates="cuenta")


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    cedula: str = Field(unique=True)
    
    # --- INICIO DE LA MODIFICACION: Vinculo con la tabla Cuenta ---
    id_cuenta: int = Field(foreign_key="cuenta.id", unique=True)
    cuenta: Cuenta = Relationship(back_populates="usuario")
    # --- FIN DE LA MODIFICACION ---
    
    casos: List["Caso"] = Relationship(back_populates="usuario")

class Estudiante(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_cuenta: Optional[int] = Field(default=None, foreign_key="cuenta.id", unique=True)
    cuenta: Optional["Cuenta"] = Relationship(back_populates="estudiante")
    nombre_completo: str
    area_especialidad: str
    asignaciones: List["Asignacion"] = Relationship(back_populates="estudiante")

class Asesor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str
    area_especialidad: str
    asignaciones: List["Asignacion"] = Relationship(back_populates="asesor")

class Caso(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion_hechos: str
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    id_usuario: int = Field(foreign_key="usuario.id")
    
    estado: str = Field(default=EstadoCaso.EN_REVISION.value, index=True)
    
    reporte_consolidado: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    usuario: "Usuario" = Relationship(back_populates="casos")
    evidencias: List["Evidencia"] = Relationship(back_populates="caso")
    asignaciones: List["Asignacion"] = Relationship(back_populates="caso")

class Evidencia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    nombre_archivo: str
    ruta_archivo: str
    estado: str = Field(default="subido")
    tipo: str = Field(default="desconocido") # e.g., "documento", "imagen", "video", etc.
    reporte_analisis: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    caso: "Caso" = Relationship(back_populates="evidencias")

class Asignacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    id_estudiante: int = Field(foreign_key="estudiante.id")
    id_asesor: int = Field(foreign_key="asesor.id")
    
    caso: "Caso" = Relationship(back_populates="asignaciones")
    estudiante: "Estudiante" = Relationship(back_populates="asignaciones")
    asesor: "Asesor" = Relationship(back_populates="asignaciones")

# =================================================================================
# MODELOS DE LA API (Para validacion de datos)
# =================================================================================

# --- INICIO DE LA MODIFICACION: Nuevos modelos para autenticacion ---
class CuentaCreacion(SQLModel):
    email: str
    contrasena: str
    nombre: str
    cedula: str

class Token(SQLModel):
    access_token: str
    token_type: str
# --- FIN DE LA MODIFICACION ---

class CasoCreacion(SQLModel):
    descripcion_hechos: str
    # Este campo se eliminará en un paso futuro, ya que el id_usuario
    # se obtendrá del token de autenticación. Por ahora, lo mantenemos.
    id_usuario: int

class EvidenciaLectura(SQLModel):
    id: int
    nombre_archivo: str
    estado: str
    ruta_archivo: str
    
class CasoLectura(SQLModel):
    id: int
    descripcion_hechos: str
    id_usuario: int
    reporte_consolidado: Optional[str]

class CasoLecturaConEvidencias(CasoLectura):
    evidencias: List[EvidenciaLectura] = []



class CasoLecturaUsuario(SQLModel):
    """
    Docstring:
    Modelo de API especifico para devolver la lista de casos
    al panel de control de un usuario. Contiene solo la informacion
    necesaria y segura para esa vista.
    """
    id: int
    fecha_creacion: datetime
    estado: str


class EvidenciaLecturaSimple(SQLModel):
    """
    Docstring:
    Modelo para mostrar solo la informacion basica de una evidencia
    en la vista de detalle del caso.
    """
    id: int
    nombre_archivo: str
    ruta_archivo: str  # Añadido para el frontend

class CasoDetalleUsuario(SQLModel):
    """
    Docstring:
    Modelo de API para devolver todos los detalles de un caso que un
    usuario ciudadano tiene permiso para ver.
    """
    id: int
    estado: str
    descripcion_hechos: str
    fecha_creacion: datetime  # Añadido para el resumen
    reporte_consolidado: Optional[str] = None
    
    # Campos que se llenaran desde las relaciones de la base de datos
    area_asignada: Optional[str] = None
    estudiante_asignado: Optional[str] = None
    asesor_asignado: Optional[str] = None
    
    evidencias: List[EvidenciaLecturaSimple] = []




class PreguntaChat(SQLModel):
    pregunta: str

class RespuestaChat(SQLModel):
    respuesta: str

class SolicitudAnalisis(SQLModel):
    texto_adicional_usuario: str = ""