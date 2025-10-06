/**
 * """
 * Docstring:
 * Este modulo centraliza todas las funciones que interactuan con la API
 * del backend (FastAPI). Abstrae la logica de las llamadas fetch, el
 * manejo de errores y la estructura de los datos JSON para mantener los
 * componentes limpios de logica de comunicacion.
 * """
 */

// ==============================================================================
// Configuracion
// ==============================================================================
// La URL base donde se esta ejecutando nuestro backend de FastAPI.
const URL_BASE_BACKEND = "http://127.0.0.1:8000";


// ==============================================================================
// Funciones de la API
// ==============================================================================

/**
 * """
 * Docstring:
 * Envia una pregunta del usuario al Agente de Atencion en el backend.
 *
 * Args:
 *   textoPregunta (string): El mensaje que el usuario escribio.
 *
 * Returns:
 *   (string): La respuesta de texto generada por el agente de IA.
 *             En caso de error, devuelve un mensaje de error informativo.
 * """
 */
export const chatearConAgente = async (textoPregunta) => {
  console.log(`API: Enviando pregunta al chat: "${textoPregunta}"`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: textoPregunta }),
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor en el chat: ${respuesta.status}`);
    }

    const datosRespuesta = await respuesta.json();
    console.log(`API: Respuesta del chat recibida: "${datosRespuesta.respuesta}"`);
    return datosRespuesta.respuesta;

  } catch (error) {
    console.error("API: Error al chatear con el agente:", error);
    return "Lo siento, no pude conectarme con el asistente en este momento.";
  }
};


/**
 * """
 * Docstring:
 * Envia los datos de un nuevo caso al backend para su creacion.
 *
 * Args:
 *   datosCaso (object): Un objeto con la informacion del caso a crear.
 *
 * Returns:
 *   (object): El objeto del caso recien creado, devuelto por el backend.
 * """
 */
export const crearNuevoCaso = async (datosCaso) => {
  console.log("API: Enviando datos para crear caso:", datosCaso);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosCaso),
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const casoCreado = await respuesta.json();
    console.log("API: Caso creado con exito:", casoCreado);
    return casoCreado;

  } catch (error) {
    console.error("API: Error al crear el caso:", error);
    throw error;
  }
};


/**
 * """
 * Docstring:
 * Solicita al backend la lista completa de todos los casos existentes.
 *
 * Args:
 *   Ninguno.
 *
 * Returns:
 *   (Array<object>): Un array con todos los objetos de los casos.
 * """
 */
export const obtenerCasos = async () => {
  console.log("API: Pidiendo la lista de todos los casos...");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos`);
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    const casos = await respuesta.json();
    console.log("API: Lista de casos recibida.");
    return casos;
  } catch (error) {
    console.error("API: Error al obtener los casos:", error);
    throw error;
  }
};


/**
 * """
 * Docstring:
 * Sube un archivo de evidencia para un caso especifico.
 *
 * Args:
 *   idCaso (number): El ID del caso al que pertenece la evidencia.
 *   archivo (File): El objeto de archivo seleccionado por el usuario.
 *
 * Returns:
 *   (object): El objeto del caso actualizado con la nueva evidencia.
 * """
 */
export const subirEvidencia = async (idCaso, archivo) => {
  const formData = new FormData();
  formData.append("archivo", archivo);

  console.log(`API: Subiendo archivo '${archivo.name}' para el caso ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/${idCaso}/evidencia`, {
      method: 'POST',
      body: formData,
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const casoActualizado = await respuesta.json();
    console.log("API: Evidencia subida. Caso actualizado:", casoActualizado);
    return casoActualizado;
  } catch (error) {
    console.error("API: Error al subir la evidencia:", error);
    throw error;
  }
};


/**
 * """
 * Docstring:
 * Consulta el estado de procesamiento de una evidencia especifica.
 *
 * Args:
 *   idEvidencia (number): El ID de la evidencia a consultar.
 *
 * Returns:
 *   (object): Un objeto con el estado actual de la evidencia.
 * """
 */
export const obtenerEstadoEvidencia = async (idEvidencia) => {
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/evidencias/${idEvidencia}/estado`);
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener estado de evidencia ${idEvidencia}:`, error);
    return { estado: 'error_de_red' };
  }
};