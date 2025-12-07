#C:\react\asistente_legal_multimodal\backend\api\modelos_compartidos.py
from sqlmodel import Field, SQLModel, Relationship, Column, Text, JSON
from typing import Dict, Optional, List

# =================================================================================
# MODELOS DE TABLAS DE BASE DE DATOS
# =================================================================================
from typing import Optional, List, Any
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
    PENDIENTE_ACEPTACION = "pendiente_aceptacion"
    ASIGNADO = "asignado"
    RECHAZADO = "rechazado"
    CERRADO = "cerrado"

class EstadoEvidencia(str, Enum):
    """
    Define los estados del ciclo de vida de un documento en el flujo de revisión.
    """
    SUBIDO = "subido"
    EN_REVISION = "en_revision"
    APROBADO = "aprobado"
    CAMBIOS_SOLICITADOS = "cambios_solicitados"


class AreaEspecialidad(SQLModel, table=True):
    """
    Representa una única área de especialidad del derecho.
    Esto centraliza los nombres y evita errores de tipeo en el resto del sistema.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True)

    estudiantes: List["Estudiante"] = Relationship(back_populates="area")
    asesores: List["Asesor"] = Relationship(back_populates="area")    


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
    asesor: Optional["Asesor"] = Relationship(back_populates="cuenta")


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
    id_area_especialidad: int = Field(foreign_key="areaespecialidad.id")
    area: AreaEspecialidad = Relationship(back_populates="estudiantes")
    asignaciones: List["Asignacion"] = Relationship(back_populates="estudiante")
    id_asesor_supervisor: Optional[int] = Field(default=None, foreign_key="asesor.id")
    supervisor: Optional["Asesor"] = Relationship(back_populates="estudiantes_supervisados")

class Asesor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_cuenta: Optional[int] = Field(default=None, foreign_key="cuenta.id", unique=True)
    cuenta: Optional["Cuenta"] = Relationship(back_populates="asesor")
    nombre_completo: str
    id_area_especialidad: int = Field(foreign_key="areaespecialidad.id")
    area: AreaEspecialidad = Relationship(back_populates="asesores")
    asignaciones: List["Asignacion"] = Relationship(back_populates="asesor")
    estudiantes_supervisados: List["Estudiante"] = Relationship(back_populates="supervisor")


class Nota(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    contenido: str = Field(sa_column=Column(Text))
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # Campo nuevo para distinguir el tipo de nota
    rol_autor: str = Field(default="estudiante")
    id_caso: int = Field(foreign_key="caso.id")
    id_cuenta_autor: int = Field(foreign_key="cuenta.id")

    # 1. Privacidad: Si es True, el Usuario ciudadano puede verla. Si es False, solo equipo interno.
    es_publica: bool = Field(default=False) # False = Solo equipo interno, True = Visible al usuario
    id_evidencia: Optional[int] = Field(default=None, foreign_key="evidencia.id") # Para hilos

    caso: "Caso" = Relationship(back_populates="notas")
    autor: "Cuenta" = Relationship() 
     # Relación opcional para acceder al documento padre
    evidencia: Optional["Evidencia"] = Relationship()

class Caso(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion_hechos: str
    fecha_creacion: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    id_usuario: int = Field(foreign_key="usuario.id")
    
    estado: str = Field(default=EstadoCaso.EN_REVISION.value, index=True)
    justificacion_rechazo: Optional[str] = Field(default=None, sa_column=Column(Text))
    reporte_consolidado: Optional[str] = Field(default=None, sa_column=Column(Text))
    inventario_documentos: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    
    historial_conversacion: Optional[List[Dict[str, Any]]] = Field(default_factory=list, sa_column=Column(JSON))

    usuario: "Usuario" = Relationship(back_populates="casos")
    evidencias: List["Evidencia"] = Relationship(back_populates="caso")
    asignaciones: List["Asignacion"] = Relationship(back_populates="caso")
    notas: List["Nota"] = Relationship(back_populates="caso")
    

class Evidencia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    nombre_archivo: str
    ruta_archivo: str
    # El estado ahora usará los valores definidos en el Enum EstadoEvidencia
    estado: str = Field(default=EstadoEvidencia.SUBIDO.value, index=True)
    tipo: str = Field(default="desconocido")
    reporte_analisis: Optional[str] = Field(default=None, sa_column=Column(Text))
    subido_por_id_cuenta: Optional[int] = Field(default=None, foreign_key="cuenta.id")
    caso: "Caso" = Relationship(back_populates="evidencias")
    subido_por: Optional["Cuenta"] = Relationship()

class Asignacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    id_estudiante: int = Field(foreign_key="estudiante.id")
    id_asesor: int = Field(foreign_key="asesor.id")
    estado: str = Field(default="pendiente", index=True)
    calificacion: Optional[int] = Field(default=None) # Escala 1 a 5
    comentario_docente: Optional[str] = Field(default=None, sa_column=Column(Text))
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
    perfil: Optional[Any] = None
# --- FIN DE LA MODIFICACION ---

class CasoCreacion(SQLModel):
    descripcion_hechos: str
    # Este campo se eliminará en un paso futuro, ya que el id_usuario
    # se obtendrá del token de autenticación. Por ahora, lo mantenemos.
    id_usuario: Optional[int] = None

class NotaCreacion(SQLModel):
    """
    Modelo para validar los datos que llegan al crear una nueva nota.
    """
    contenido: str
    es_publica: bool = False # Por defecto es privado (interno)
    id_evidencia: Optional[int] = None # Opcional, para atar el comentario a un doc

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
    id: int
    nombre_archivo: str
    ruta_archivo: str
    estado: str  # <-- Campo añadido para que el frontend conozca el estado de la evidencia
    autor_nombre: Optional[str] = None # Añadimos el nombre del autor


class NotaLectura(SQLModel):
    id: int
    contenido: str
    fecha_creacion: datetime
    rol_autor: str  # Añadido para identificar si es nota de estudiante o asesor
    autor_nombre: Optional[str] = None
    es_publica: bool = False # <--- AGREGAR ESTO PARA QUE EL FRONTEND LO VEA
    # En el futuro podríamos añadir: autor_nombre: str




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
    justificacion_rechazo: Optional[str] = None
    # Campos que se llenaran desde las relaciones de la base de datos
    area_asignada: Optional[str] = None
    estudiante_asignado: Optional[str] = None
    asesor_asignado: Optional[str] = None
    
    evidencias: List[EvidenciaLecturaSimple] = []
    notas: List[NotaLectura] = []




class PreguntaChat(SQLModel):
    pregunta: str
    # Añadimos un campo opcional para recibir el historial del chat.
    historial_chat: Optional[List[Dict[str, str]]] = None

class RespuestaChat(SQLModel):
    respuesta: str

class SolicitudAnalisis(SQLModel):
    texto_adicional_usuario: str = ""


class RespuestaAnalisisIniciado(SQLModel):
    """Modelo de respuesta al iniciar un análisis asíncrono."""
    mensaje: str
    id_tarea: str

class EstadoTarea(SQLModel):
    """Modelo de respuesta para consultar el estado de una tarea de Celery."""
    id_tarea: str
    estado: str  # PENDING, SUCCESS, FAILURE
    resultado: Optional[Any] = None

class CasoSupervisadoLectura(SQLModel):
    """
    Docstring:
    Modelo de API especifico para devolver la lista de casos
    en el dashboard del asesor. Incluye la informacion del caso
    y el nombre del estudiante asignado.
    """
    id: int
    descripcion_hechos: str
    estado: str
    fecha_creacion: datetime
    nombre_estudiante: str
    tiene_alerta: bool = False


class EstudianteLecturaSimple(SQLModel):
    """
    Docstring:
    Modelo de API para devolver una lista simple de estudiantes,
    util para mostrarlos en un menu desplegable de reasignacion.
    """
    id: int
    nombre_completo: str
    area_especialidad: str    



class SolicitudReasignacion(SQLModel):
    """
    Docstring:
    Modelo para validar la peticion de reasignar un caso.
    Espera recibir el ID del nuevo estudiante.
    """
    id_nuevo_estudiante: int    


class MetricaEstudiante(SQLModel):
    """
    Representa una única métrica de carga de trabajo para un estudiante.
    """
    nombre_estudiante: str
    casos_asignados: int

class DashboardAsesorData(SQLModel):
    """
    El modelo de respuesta completo para el dashboard del asesor.
    Combina la lista detallada de casos y las métricas de carga de trabajo.
    """
    casos_supervisados: List[CasoSupervisadoLectura]
    metricas_carga_trabajo: List[MetricaEstudiante]



class PersonalCreacion(SQLModel):
    """
    Modelo para validar los datos que envia el administrador para crear
    una nueva cuenta de Estudiante o Asesor.
    """
    email: str
    contrasena: str
    nombre_completo: str
    id_area_especialidad: int
    rol: str # Debe ser 'estudiante' o 'asesor'

class PersonalGestionLectura(SQLModel):
    """
    Modelo de respuesta para la lista de personal.
    Combina datos de la cuenta (email, rol, estado) y del perfil (nombre, area).
    """
    id_cuenta: int
    email: str
    rol: str
    esta_activo: bool
    nombre_completo: str
    area_especialidad: str
    nombre_supervisor: Optional[str] = None


class UsuarioGestionLectura(SQLModel):
    """
    Modelo de respuesta para la lista de usuarios (ciudadanos) en el panel de admin.
    """
    id_cuenta: int
    email: str
    nombre_completo: str # El nombre viene de la tabla Usuario
    esta_activo: bool



class UsuarioEdicion(SQLModel):
    """
    Modelo para validar los datos que envía el administrador para editar
    una cuenta de usuario (ciudadano). Todos los campos son opcionales.
    """
    nombre: Optional[str] = None
    cedula: Optional[str] = None
    contrasena: Optional[str] = None


class PersonalEdicion(SQLModel):
    """
    Modelo para validar los datos que envia el administrador para editar
    una cuenta existente. Todos los campos son opcionales, permitiendo
    actualizaciones parciales (ej. solo cambiar la contraseña).
    """
    nombre_completo: Optional[str] = None
    id_area_especialidad: Optional[int] = None
    email: Optional[str] = None
    # Solo se debe proporcionar si se desea cambiar la contraseña.
    contrasena: Optional[str] = None    


class AreaLectura(SQLModel):
    id: int
    nombre: str    


class AreaCreacionEdicion(SQLModel):
    """
    Modelo para validar los datos que envia el administrador para
    crear una nueva area o editar una existente.
    """
    nombre: str    


class SupervisionAsignacion(SQLModel):
    """
    Modelo para la petición de asignar una lista de estudiantes a un asesor.
    """
    id_asesor: int
    ids_estudiantes: List[int]



class NotificacionCreacion(SQLModel):
    """
    Modelo para validar los datos que envía el estudiante para notificar al usuario.
    """
    asunto: str
    mensaje: str



class SolicitudCierreCaso(SQLModel):
    calificacion: int
    comentario: str