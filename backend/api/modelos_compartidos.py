# backend/api/modelos_compartidos.py

from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
from sqlalchemy import Column, Text
from sqlalchemy.types import TypeDecorator

class JsonType(TypeDecorator):
    impl = Text
    cache_ok = True
    def process_bind_param(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        if value is not None: return json.dumps(value)
        return None
    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Any]:
        if value is not None: return json.loads(value)
        return None

# =================================================================================
# SECCIÓN 2: MODELOS DE TABLAS DE BASE DE DATOS (Con corrección)
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
    usuario: Usuario = Relationship(back_populates="casos")
    evidencias: List["Evidencia"] = Relationship(back_populates="caso")
    asignaciones: List["Asignacion"] = Relationship(back_populates="caso")

class Evidencia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    ruta_archivo: str
    estado: str = Field(default="encolado")
    reporte_analisis: Optional[str] = Field(default=None, sa_column=Column(Text))
    caso: "Caso" = Relationship(back_populates="evidencias")

class Asignacion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_caso: int = Field(foreign_key="caso.id")
    id_estudiante: int = Field(foreign_key="estudiante.id")
    id_asesor: int = Field(foreign_key="asesor.id")
    
    caso: "Caso" = Relationship(back_populates="asignaciones")
    estudiante: "Estudiante" = Relationship(back_populates="asignaciones")
    # --- ESTA ES LA LÍNEA CORREGIDA ---
    # Antes, por error, podia decir 'back_populates="asesor"'.
    # Lo correcto es que apunte a la lista 'asignaciones' en el modelo Asesor.
    asesor: "Asesor" = Relationship(back_populates="asignaciones")

# =================================================================================
# SECCIÓN 3: MODELOS DE LA API (Estables)
# =================================================================================
class CasoCreacion(SQLModel):
    descripcion_hechos: str
    id_usuario: int

class EvidenciaLectura(SQLModel):
    id: int
    ruta_archivo: str
    estado: str
    reporte_analisis: Optional[str]

class CasoLectura(SQLModel):
    id: int
    descripcion_hechos: str
    id_usuario: int

class CasoLecturaConEvidencias(CasoLectura):
    evidencias: List[EvidenciaLectura] = []


# --- PARA EL CHAT ---

class PreguntaChat(SQLModel):
    """Define la estructura del JSON que el frontend debe enviar para el chat."""
    pregunta: str

class RespuestaChat(SQLModel):
    """Define la estructura del JSON que el backend devolvera en el chat."""
    respuesta: str    