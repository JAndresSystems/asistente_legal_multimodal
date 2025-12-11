//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\asesor.js
import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

/**
 * Llama al endpoint para obtener los datos del dashboard del asesor.
 */
export const apiObtenerDashboardAsesor = async () => {
  console.log("API: Solicitando datos completos del dashboard para el asesor.");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/dashboard`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al obtener los datos del dashboard:", error);
    throw error;
  }
};

/**
 * Llama al endpoint para que un asesor obtenga los detalles de un expediente.
 * @param {number} idCaso El ID del caso a consultar.
 */
export const apiObtenerDetalleExpedienteAsesor = async (idCaso) => {
  console.log(`API: Asesor solicitando detalles para el expediente ID: ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener el detalle del expediente ${idCaso} para el asesor:`, error);
    throw error;
  }
};

/**
 * Llama al endpoint para que un asesor cree una nota de supervisión.
 * @param {number} idCaso El ID del caso.
 * @param {string} contenido El texto de la nota.
 */
// En frontend/src/servicios/api/asesor.js

export const apiCrearNotaAsesor = async (idCaso, contenido, esPublica = false, idEvidencia = null) => {
  try {
    const response = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}/crear-nota`, {
      method: 'POST',
      headers: obtenerCabeceras(), // Usamos la función helper que ya maneja el token correctamente
      body: JSON.stringify({ 
          contenido: contenido,
          es_publica: esPublica,
          id_evidencia: idEvidencia 
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Error al crear nota de asesor');
    }
    return await response.json();
  } catch (error) {
    console.error("API: Error al crear nota de asesor:", error);
    throw error;
  }
};

/**
 * Llama al endpoint para que un asesor marque un caso como 'cerrado'.
 * @param {number} idCaso El ID del caso a finalizar.
 */

export const apiFinalizarCaso = async (idCaso, calificacion, comentario) => {
  console.log(`API: Finalizando caso ${idCaso} con nota ${calificacion}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}/finalizar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify({
          calificacion: parseFloat(calificacion), // Aseguramos float
          comentario: comentario
      })
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || 'Error al finalizar el caso');
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al finalizar caso:", error);
    throw error;
  }
};

/**
 * Llama al endpoint para obtener una lista de todos los estudiantes disponibles.
 */
export const apiObtenerEstudiantes = async () => {
  console.log("API: Solicitando la lista de todos los estudiantes.");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/estudiantes-disponibles`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al obtener la lista de estudiantes:", error);
    throw error;
  }
};


/**
 * Llama al endpoint para que un asesor reasigne un caso a un nuevo estudiante.
 * @param {number} idCaso El ID del caso a reasignar.
 * @param {number} idNuevoEstudiante El ID del estudiante que recibirá el caso.
 */
/**
 * Llama al endpoint para reasignar un caso automáticamente.
 * Ahora envía la calificación del estudiante saliente.
 */
export const apiReasignarCaso = async (idCaso, datosReasignacion) => {
  console.log(`API: Asesor reasignando el caso ${idCaso}. Datos:`, datosReasignacion);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}/reasignar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosReasignacion),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al reasignar el caso ${idCaso}:`, error);
    throw error;
  }
};

/**
 * Llama al endpoint para que un asesor apruebe un documento.
 * @param {number} idEvidencia El ID del documento a aprobar.
 */
export const apiAprobarDocumento = async (idEvidencia) => {
  console.log(`API: Asesor aprobando el documento ID: ${idEvidencia}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/documentos/${idEvidencia}/aprobar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al aprobar el documento ${idEvidencia}:`, error);
    throw error;
  }
};

/**
 * Llama al endpoint para que un asesor solicite cambios en un documento.
 * @param {number} idEvidencia El ID del documento a rechazar.
 */
export const apiSolicitarCambiosDocumento = async (idEvidencia) => {
  console.log(`API: Asesor solicitando cambios para el documento ID: ${idEvidencia}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/documentos/${idEvidencia}/solicitar-cambios`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al solicitar cambios para el documento ${idEvidencia}:`, error);
    throw error;
  }
};