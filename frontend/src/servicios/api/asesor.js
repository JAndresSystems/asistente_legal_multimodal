//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\asesor.js
import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

/**
 * Docstring:
 * Llama al endpoint para obtener los datos completos del dashboard del asesor,
 * incluyendo la lista de casos y las métricas de carga de trabajo.
 */
export const apiObtenerDashboardAsesor = async () => {
  console.log("API: Solicitando datos completos del dashboard para el asesor.");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/dashboard`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve { casos_supervisados, metricas_carga_trabajo }
  } catch (error) {
    console.error("API: Error al obtener los datos del dashboard:", error);
    throw error;
  }
};


/**
 * Docstring:
 * Llama al endpoint para que un asesor obtenga los detalles completos
 * de un expediente especifico que supervisa.
 * @param {number} idCaso El ID del caso a consultar.
 */
export const apiObtenerDetalleExpedienteAsesor = async (idCaso) => {
  console.log(`API: Asesor solicitando detalles para el expediente ID: ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/expedientes/${idCaso}`, {
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
 * Docstring:
 * Llama al endpoint para que un asesor cree una nota de supervisión en un caso.
 * @param {number} idCaso El ID del caso al que se adjunta la nota.
 * @param {string} contenido El texto de la nota.
 */
export const apiCrearNotaAsesor = async (idCaso, contenido) => {
  console.log(`API: Asesor creando nota en el caso ${idCaso}`);
  
  const cuerpoDeLaPeticion = {
    contenido: contenido,
  };

  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/expedientes/${idCaso}/crear-nota`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(cuerpoDeLaPeticion),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve el objeto de la nueva nota creada
  } catch (error) {
    console.error(`API: Error al crear la nota de supervisor para el caso ${idCaso}:`, error);
    throw error;
  }
};




/**
 * Docstring:
 * Llama al endpoint para que un asesor marque un caso como 'cerrado'.
 * @param {number} idCaso El ID del caso a finalizar.
 */
export const apiFinalizarCaso = async (idCaso) => {
  console.log(`API: Asesor solicitando finalizar el caso ID: ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/expedientes/${idCaso}/finalizar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      // No se necesita cuerpo (body) para esta petición
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve { mensaje, caso }
  } catch (error) {
    console.error(`API: Error al finalizar el caso ${idCaso}:`, error);
    throw error;
  }
};



/**
 * Docstring:
 * Llama al endpoint para obtener una lista de todos los estudiantes disponibles
 * en el sistema, para la funcionalidad de reasignacion.
 */
export const apiObtenerEstudiantes = async () => {
  console.log("API: Solicitando la lista de todos los estudiantes.");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/estudiantes-disponibles`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve la lista de estudiantes
  } catch (error) {
    console.error("API: Error al obtener la lista de estudiantes:", error);
    throw error;
  }
};



/**
 * Docstring:
 * Llama al endpoint para que un asesor reasigne un caso a un nuevo estudiante.
 * @param {number} idCaso El ID del caso a reasignar.
 * @param {number} idNuevoEstudiante El ID del estudiante que recibirá el caso.
 */
export const apiReasignarCaso = async (idCaso, idNuevoEstudiante) => {
  console.log(`API: Asesor reasignando el caso ${idCaso} al estudiante ${idNuevoEstudiante}`);
  
  const cuerpoDeLaPeticion = {
    id_nuevo_estudiante: idNuevoEstudiante,
  };

  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/expedientes/${idCaso}/reasignar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(cuerpoDeLaPeticion),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve { mensaje: "..." }
  } catch (error) {
    console.error(`API: Error al reasignar el caso ${idCaso}:`, error);
    throw error;
  }
};





/**
 * Docstring:
 * Llama al endpoint para que un asesor apruebe un documento.
 * @param {number} idEvidencia El ID del documento (evidencia) a aprobar.
 */
export const apiAprobarDocumento = async (idEvidencia) => {
  console.log(`API: Asesor aprobando el documento ID: ${idEvidencia}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/documentos/${idEvidencia}/aprobar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve { mensaje: "..." }
  } catch (error) {
    console.error(`API: Error al aprobar el documento ${idEvidencia}:`, error);
    throw error;
  }
};

/**
 * Docstring:
 * Llama al endpoint para que un asesor solicite cambios en un documento.
 * @param {number} idEvidencia El ID del documento (evidencia) a rechazar.
 */
export const apiSolicitarCambiosDocumento = async (idEvidencia) => {
  console.log(`API: Asesor solicitando cambios para el documento ID: ${idEvidencia}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/asesor/documentos/${idEvidencia}/solicitar-cambios`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve { mensaje: "..." }
  } catch (error) {
    console.error(`API: Error al solicitar cambios para el documento ${idEvidencia}:`, error);
    throw error;
  }
};