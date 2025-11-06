//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\estudiante.js
import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

export const apiObtenerMisAsignaciones = async () => {
  console.log("API: Solicitando la lista de casos asignados para el estudiante.");
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/mis-asignaciones`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al obtener las asignaciones del estudiante:", error);
    throw error;
  }
};

export const apiObtenerDetalleExpediente = async (idCaso) => {
  console.log(`API: Solicitando detalles para el expediente ID: ${idCaso}`);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener el detalle del expediente ${idCaso}:`, error);
    throw error;
  }
};

// NOTA: Las rutas de /agentes tambien deben estandarizarse si no lo estan ya. Asumimos que si.
export const apiConsultarAgenteJuridico = async (idCaso, pregunta) => {
  console.log(`API: Enviando pregunta al Agente Juridico para el caso ${idCaso}: "${pregunta}"`);
  try {
    const cuerpoDeLaPeticion = { id_caso: idCaso, pregunta: pregunta };
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/agentes/consulta-juridica`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(cuerpoDeLaPeticion),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al consultar al Agente Juridico:", error);
    throw error;
  }
};

export const apiGenerarDocumento = async (idCaso, nombrePlantilla) => {
  console.log(`API: Solicitando generar documento '${nombrePlantilla}' para el caso ${idCaso}`);
  try {
    const cuerpoDeLaPeticion = { id_caso: idCaso, nombre_plantilla: nombrePlantilla };
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/agentes/generar-documento`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(cuerpoDeLaPeticion),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al generar el documento:", error);
    throw error;
  }
};

export const apiAceptarAsignacion = async (idCaso) => {
  console.log(`API: Aceptando asignacion para el caso ${idCaso}`);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}/aceptar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al aceptar el caso ${idCaso}:`, error);
    throw error;
  }
};

export const apiRechazarAsignacion = async (idCaso) => {
  console.log(`API: Rechazando asignacion para el caso ${idCaso}`);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}/rechazar`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al rechazar el caso ${idCaso}:`, error);
    throw error;
  }
};

export const apiSubirDocumentoEstudiante = async (idCaso, archivo) => {
  console.log(`API: Estudiante subiendo el archivo '${archivo.name}' al caso ${idCaso}`);
  const formData = new FormData();
  formData.append("archivo", archivo);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}/subir-documento`, {
      method: 'POST',
      headers: obtenerCabeceras(true),
      body: formData,
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al subir el documento para el caso ${idCaso}:`, error);
    throw error;
  }
};

export const apiCrearNotaEstudiante = async (idCaso, contenido) => {
  console.log(`API: Estudiante creando nota en el caso ${idCaso}`);
  const cuerpoDeLaPeticion = { contenido: contenido };
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}/crear-nota`, {
      method: 'POST',
      headers: obtenerCabeceras(),
      body: JSON.stringify(cuerpoDeLaPeticion),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al crear la nota para el caso ${idCaso}:`, error);
    throw error;
  }
};

export const apiEnviarParaRevision = async (idEvidencia) => {
  console.log(`API: Estudiante enviando a revisión el documento ID: ${idEvidencia}`);
  try {
    // MODIFICACION: Se añade /api
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/documentos/${idEvidencia}/enviar-a-revision`, {
      method: 'POST',
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al enviar a revisión el documento ${idEvidencia}:`, error);
    throw error;
  }
};



