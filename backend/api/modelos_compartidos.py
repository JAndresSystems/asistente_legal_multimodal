# backend/api/modelos_compartidos.py

from sqlmodel import Field, SQLModel, Relationship, Column, Text
from typing import Optional, List

# Se eliminan importaciones no utilizadas como datetime, uuid, json, TypeDecorator, Dict, Any
# para mantener el codigo limpio. La logica de JSON no es necesaria aqui.

# =================================================================================
# MODELOS DE TABLAS DE BASE DE DATOS
# =================================================================================

class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    cedula: str = Field(unique=True)
    email: str = Field(unique=True)
    casos: List["Caso"] = Relationship(back_populates="usuario")

class Estudiante(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
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
    id_usuario: int = Field(foreign_key="usuario.id")
    
    # Este es el campo clave que acabamos de añadir a la BD.
    reporte_consolidado: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    usuario: "Usuario" = Relationship(back_populates="casos")
    evidencias: List["Evidencia"] = Relationship(back_populates="caso")
    asignaciones: List["Asignacion"] = Relationship(back_populates="caso")

class Evidencia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    nombre_archivo: str # <-- Se añade esta columna que faltaba
    ruta_archivo: str
    estado: str = Field(default="subido")
    
    
    # Este campo ya no es el principal para el reporte, pero lo mantenemos
    # para no causar errores si alguna parte del codigo aun lo referencia.
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
class CasoCreacion(SQLModel):
    descripcion_hechos: str
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

class PreguntaChat(SQLModel):
    pregunta: str

class RespuestaChat(SQLModel):
    respuesta: str

class SolicitudAnalisis(SQLModel):
    texto_adicional_usuario: str = ""    