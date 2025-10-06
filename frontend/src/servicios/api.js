/**
 * """
 * Docstring:
 * Este modulo centraliza todas las funciones que interactuan con la API
 * del backend (FastAPI). Abstrae la logica de las llamadas fetch, el
 * manejo de errores y la estructura de los datos JSON.
 * """
 */

// ==============================================================================
// Configuracion
// ==============================================================================
const URL_BASE_BACKEND = "http://127.0.0.1:8000";


// ==============================================================================
// Funciones de la API
// ==============================================================================

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
    let respuestaDelAgente = datosRespuesta.respuesta;
    console.log(`API: Respuesta original recibida: "${respuestaDelAgente}"`);

    const palabrasClaveDeViabilidad = ["califica", "cumple", "atendemos", "requisitos", "elegibilidad", "procedente", "admisible"];
    const respuestaEnMinusculas = respuestaDelAgente.toLowerCase();
    const esViable = palabrasClaveDeViabilidad.some(palabra => respuestaEnMinusculas.includes(palabra));

    if (esViable) {
      console.log("API (Simulacion): Se detecto un caso viable. Añadiendo señal.");
      respuestaDelAgente += " [INICIAR_CASO]";
    }
    
    return respuestaDelAgente;

  } catch (error) {
    console.error("API: Error al chatear con el agente:", error);
    return "Lo siento, no pude conectarme con el asistente en este momento.";
  }
};

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
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al subir la evidencia:", error);
    throw error;
  }
};

// --- NUEVA FUNCION AÑADIDA EN ESTE PASO ---
/**
 * """
 * Docstring:
 * Obtiene todos los detalles de un caso especifico, incluyendo la lista
 * de sus evidencias y el estado de cada una.
 *
 * Args:
 *   idCaso (number): El ID del caso a consultar.
 *
 * Returns:
 *   (object): El objeto completo del caso con sus evidencias.
 * """
 */
export const obtenerDetallesCaso = async (idCaso) => {
  console.log(`API: Solicitando detalles para el caso ID: ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/${idCaso}`);
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener los detalles del caso ${idCaso}:`, error);
    throw error;
  }
};