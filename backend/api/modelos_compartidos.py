from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
from sqlalchemy import Column, Text
from sqlalchemy.types import TypeDecorator

# =================================================================================
# SECCIÓN 1: "TRADUCTOR" PERSONALIZADO PARA LA BASE DE DATOS (Se mantiene intacto)
# =================================================================================

class JsonType(TypeDecorator):
    impl = Text
    cache_ok = True
    def process_bind_param(self, value: Optional[Any], dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value)
        return None
    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[Any]:
        if value is not None:
            return json.loads(value)
        return None

# =================================================================================
# SECCIÓN 2: MODELOS DE TABLAS DE BASE DE DATOS
# =================================================================================

### --- NUEVOS MODELOS AÑADIDOS --- ###

class Estudiante(SQLModel, table=True):
    id_estudiante: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str
    area_competencia: str
    asignaciones: List["Asignacion"] = Relationship(back_populates="estudiante")

class Asesor(SQLModel, table=True):
    id_asesor: Optional[int] = Field(default=None, primary_key=True)
    nombre_completo: str
    area_competencia: str
    asignaciones: List["Asignacion"] = Relationship(back_populates="asesor")

class Asignacion(SQLModel, table=True):
    id_asignacion: Optional[int] = Field(default=None, primary_key=True)
    # Foreign Keys respetando sus nombres de columna
    id_caso: uuid.UUID = Field(foreign_key="caso.id_caso")
    id_estudiante: int = Field(foreign_key="estudiante.id_estudiante")
    id_asesor: int = Field(foreign_key="asesor.id_asesor")
    
    # Relaciones inversas
    caso: "Caso" = Relationship(back_populates="asignaciones")
    estudiante: "Estudiante" = Relationship(back_populates="asignaciones")
    asesor: "Asesor" = Relationship(back_populates="asignaciones")


### --- MODELOS EXISTENTES (MODIFICADO) --- ###

class Caso(SQLModel, table=True):
    id_caso: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    titulo: str
    resumen: Optional[str] = Field(default=None)
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    evidencias: List["Evidencia"] = Relationship(back_populates="caso")
    
    ### --- LÍNEA AÑADIDA --- ###
    # Añadimos la relación para poder ver las asignaciones de un caso.
    asignaciones: List["Asignacion"] = Relationship(back_populates="caso")

class Evidencia(SQLModel, table=True):
    # Este modelo no necesita cambios, se mantiene tal como lo tenías.
    id_evidencia: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    id_caso: uuid.UUID = Field(foreign_key="caso.id_caso")
    nombre_archivo: str
    ruta_archivo: str
    tipo_contenido: str
    estado_procesamiento: str = Field(default="pendiente")
    texto_extraido: Optional[str] = Field(default=None, sa_column=Column(Text))
    entidades_extraidas: Optional[List[Dict]] = Field(default=None, sa_column=Column(JsonType))
    informacion_recuperada: Optional[List[str]] = Field(default=None, sa_column=Column(JsonType))
    borrador_estrategia: Optional[str] = Field(default=None, sa_column=Column(Text))
    verificacion_calidad: Optional[Dict] = Field(default=None, sa_column=Column(JsonType))
    caso: "Caso" = Relationship(back_populates="evidencias")

# =================================================================================
# SECCIÓN 3: MODELOS DE LA API (Se mantiene intacto)
# =================================================================================

class CasoCreacion(SQLModel):
    titulo: str
    resumen: Optional[str] = None

class EvidenciaLectura(SQLModel):
    id_evidencia: uuid.UUID
    nombre_archivo: str
    # ... (resto de campos se mantienen)
    ruta_archivo: str
    tipo_contenido: str
    estado_procesamiento: str
    texto_extraido: Optional[str]
    entidades_extraidas: Optional[List[Dict]]
    informacion_recuperada: Optional[List[str]]
    borrador_estrategia: Optional[str]
    verificacion_calidad: Optional[Dict]


class CasoLectura(SQLModel):
    id_caso: uuid.UUID
    titulo: str
    resumen: Optional[str]
    fecha_creacion: datetime

class CasoLecturaConEvidencias(CasoLectura):
    evidencias: List[EvidenciaLectura] = []