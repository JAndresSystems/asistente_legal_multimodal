# backend/api/enrutador_principal.py

from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
import shutil
from pathlib import Path
import uuid
from sqlmodel import Session, select
from ..base_de_datos import obtener_sesion
from .modelos_compartidos import Caso, CasoCreacion, Evidencia, CasoLecturaConEvidencias
# La siguiente línea se ha eliminado porque el grafo ya no se invoca directamente aquí.
# from ..agentes.orquestador_del_grafo import grafo_compilado

# ¡NUEVA IMPORTACIÓN! Importamos la tarea de Celery que creamos en el paso anterior.
from ..tareas import procesar_evidencia_tarea

router = APIRouter(tags=["Casos"])

@router.post("/casos", response_model=CasoLecturaConEvidencias, status_code=201)
def crear_caso(sesion: Session = Depends(obtener_sesion), caso_a_crear: CasoCreacion = ...):
    nuevo_caso_db = Caso.model_validate(caso_a_crear)
    sesion.add(nuevo_caso_db)
    sesion.commit()
    sesion.refresh(nuevo_caso_db)
    return nuevo_caso_db

@router.get("/casos", response_model=list[CasoLecturaConEvidencias])
def listar_casos(sesion: Session = Depends(obtener_sesion)):
    casos = sesion.exec(select(Caso)).all()
    return casos

@router.post("/casos/{id_caso}/evidencia", response_model=CasoLecturaConEvidencias)
def subir_evidencia(sesion: Session = Depends(obtener_sesion), id_caso: uuid.UUID = ..., archivo: UploadFile = File(...)):
    """
    Endpoint para subir un archivo de evidencia.

    Este endpoint ahora funciona de forma asíncrona:
    1. Guarda el archivo en el disco.
    2. Crea un registro de 'Evidencia' en la base de datos con el estado 'encolado'.
    3. Delega el trabajo pesado de procesamiento a una tarea de Celery.
    4. Responde inmediatamente al cliente con el estado actual del caso.
    """
    caso_actual = sesion.get(Caso, id_caso)
    if not caso_actual:
        raise HTTPException(status_code=404, detail="El caso no fue encontrado")
    
    # --- Guarda el archivo en el disco como antes ---
    ruta_guardado_caso = Path("backend/archivos_subidos") / str(id_caso)
    ruta_guardado_caso.mkdir(parents=True, exist_ok=True)
    ruta_archivo_final = ruta_guardado_caso / archivo.filename
    with open(ruta_archivo_final, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
        
    # --- LÓGICA MODIFICADA PARA TAREAS ASÍNCRONAS ---

    # 1. Crear un registro de evidencia en la BD con estado 'encolado'.
    #    Ya no ejecutamos el grafo aquí. Solo guardamos la información básica.
    nueva_evidencia_db = Evidencia(
        id_caso=id_caso,
        nombre_archivo=archivo.filename,
        ruta_archivo=str(ruta_archivo_final),
        tipo_contenido=archivo.content_type,
        estado_procesamiento="encolado" #  estado inicial
    )
    
    sesion.add(nueva_evidencia_db)
    sesion.commit()
    # Hacemos un 'refresh' para obtener el id_evidencia que la BD acaba de generar.
    sesion.refresh(nueva_evidencia_db)
    # Hacemos otro 'refresh' al caso para que su lista de evidencias se actualice.
    sesion.refresh(caso_actual)

    # 2. ¡EL PASO CLAVE! Enviar la tarea a la cola de Celery.
    #    Usamos .delay() para encolar la tarea. Celery la recogerá y ejecutará en segundo plano.
    #    Es crucial pasar el ID como un string, ya que es la forma más segura de pasar
    #    parámetros a las tareas.
    print(f"INFO: [API] Encolando tarea para la evidencia: {nueva_evidencia_db.id_evidencia}")
    procesar_evidencia_tarea.delay(str(nueva_evidencia_db.id_evidencia))

    # 3. La API responde inmediatamente al usuario.
    #    El frontend recibirá la nueva evidencia con el estado 'encolado', y podrá
    #    actualizar su estado más tarde si lo implementamos.
    return caso_actual



@router.get("/evidencias/{id_evidencia}/estado", response_model=dict)
def obtener_estado_evidencia(sesion: Session = Depends(obtener_sesion), id_evidencia: uuid.UUID = ...):
    """
    Endpoint dedicado para consultar rápidamente el estado de procesamiento de una evidencia.

    El frontend utilizará este endpoint para hacer "polling" (preguntar periódicamente)
    y saber cuándo un análisis en segundo plano ha terminado.

    Args:
        sesion (Session): La sesión de la base de datos.
        id_evidencia (uuid.UUID): El ID de la evidencia a consultar.

    Returns:
        dict: Un diccionario que contiene el estado actual, por ejemplo:
              {"estado_procesamiento": "completado"}
    """
    evidencia = sesion.get(Evidencia, id_evidencia)
    if not evidencia:
        raise HTTPException(status_code=404, detail="La evidencia no fue encontrada")
    
    return {"estado_procesamiento": evidencia.estado_procesamiento}