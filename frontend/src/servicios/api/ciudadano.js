//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\ciudadano.js
import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

export const chatearConAgente = async (textoPregunta) => {
  console.log(`API: Enviando pregunta al chat: "${textoPregunta}"`);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: textoPregunta }),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor en el chat: ${respuesta.status}`); }
    const datosRespuesta = await respuesta.json();
    const respuestaDelAgente = datosRespuesta.respuesta;
    const palabrasClaveDeViabilidad = ["califica", "cumple", "atendemos", "requisitos", "elegibilidad", "procedente", "admisible", "iniciar el registro"];
    const esViable = palabrasClaveDeViabilidad.some(palabra => respuestaDelAgente.toLowerCase().includes(palabra));
    return { texto: respuestaDelAgente, iniciarTriaje: esViable };
  } catch (error) {
    console.error("API: Error al chatear con el agente:", error);
    return { texto: "Lo siento, no pude conectarme con el asistente en este momento.", iniciarTriaje: false };
  }
};

export const crearNuevoCaso = async (datosCaso) => {
  console.log("API: Enviando datos para crear caso:", datosCaso);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosCaso),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al crear el caso:", error);
    throw error;
  }
};

export const apiObtenerMisCasos = async () => {
  console.log("API: Solicitando la lista de casos para el usuario logueado.");
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos/mis-casos`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al obtener los casos del usuario:", error);
    throw error;
  }
};

export const subirEvidencia = async (idCaso, archivo) => {
  const formData = new FormData();
  formData.append("archivo", archivo);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos/${idCaso}/subir-evidencia-simple`, {
      method: 'POST',
      headers: obtenerCabeceras(true),
      body: formData,
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return { exito: true };
  } catch (error) {
    console.error("API: Error al subir la evidencia:", error);
    throw error;
  }
};

export const analizarCaso = async (idCaso, textoAdicional = "") => {
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos/${idCaso}/analizar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify({ texto_adicional_usuario: textoAdicional }),
    });
    if (!respuesta.ok) {
      // Capturamos el status para el error 504
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al solicitar el analisis del caso ${idCaso}:`, error);
    throw error;
  }
};

export const obtenerDetallesCaso = async (idCaso) => {
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos/${idCaso}`, {
      headers: obtenerCabeceras()
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener los detalles del caso ${idCaso}:`, error);
    throw error;
  }
};

export const obtenerEstadoEvidencia = async (idEvidencia) => {
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/evidencias/${idEvidencia}/estado`, {
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener el estado de la evidencia ${idEvidencia}:`, error);
    throw error;
  }
};