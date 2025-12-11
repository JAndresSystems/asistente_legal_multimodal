// frontend/src/servicios/api/asesor.js
import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

/**
 * 📊 DASHBOARD ASESOR
 * Obtiene el resumen de casos activos, pendientes de revisión y métricas de carga
 * para el panel principal del Asesor.
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
 * 📂 DETALLE DE EXPEDIENTE
 * Recupera la información completa de un caso específico: hechos, línea de tiempo,
 * evidencias y notas, para la vista de detalle.
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
 * 📝 CREAR NOTA / FEEDBACK
 * Permite al asesor dejar comentarios en el expediente.
 * - Puede ser una nota general o atada a una evidencia (idEvidencia).
 * - Puede ser pública (visible al ciudadano) o privada (solo equipo).
 */
export const apiCrearNotaAsesor = async (idCaso, contenido, esPublica = false, idEvidencia = null) => {
  
  // Seguridad: Validación manual del token para asegurar la sesión
  const token = localStorage.getItem('authToken') || localStorage.getItem('token_auth');
  
  if (!token) {
      throw new Error("No se encontró sesión activa.");
  }

  // CORRECCIÓN: Usamos URL_BASE_BACKEND en lugar de 127.0.0.1
  const response = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}/crear-nota`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
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
};

/**
 * ⚖️ FINALIZAR CASO
 * Cierra el expediente y asigna una calificación académica al estudiante.
 * Requiere una nota (float) y un comentario de retroalimentación.
 */
export const apiFinalizarCaso = async (idCaso, calificacion, comentario) => {
  console.log(`API: Finalizando caso ${idCaso} con nota ${calificacion}`);
  
  const token = localStorage.getItem('authToken') || localStorage.getItem('token_auth');
  
  if (!token) {
      throw new Error("No se encontró el token de sesión. Por favor inicie sesión nuevamente.");
  }

  // CORRECCIÓN: Usamos URL_BASE_BACKEND en lugar de 127.0.0.1
  const respuesta = await fetch(`${URL_BASE_BACKEND}/api/asesor/expedientes/${idCaso}/finalizar`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
        calificacion: parseFloat(calificacion),
        comentario: comentario
    })
  });

  if (!respuesta.ok) {
    const errorData = await respuesta.json();
    throw new Error(errorData.detail || 'Error al finalizar el caso');
  }
  return await respuesta.json();
};

/**
 * 👥 LISTAR ESTUDIANTES
 * Obtiene la lista de estudiantes disponibles (útil para consultas de carga).
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
 * 🔄 REASIGNACIÓN INTELIGENTE
 * Libera al estudiante actual (con calificación) y solicita al sistema
 * que asigne uno nuevo automáticamente basado en la carga laboral.
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
 * ✅ APROBAR DOCUMENTO
 * Cambia el estado de una evidencia a "Aprobado", validando el trabajo del estudiante.
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
 * ❌ SOLICITAR CAMBIOS
 * Rechaza un documento y notifica al estudiante que debe subir una nueva versión.
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

/**
 * 📥 DESCARGAR REPORTE PDF
 * Genera el documento oficial del caso en formato PDF y fuerza la descarga en el navegador.
 */
export const apiDescargarReporteExpedientePDF = async (idCaso) => {
    console.log("Descargando reporte PDF asesor...");
    try {
        const respuesta = await fetch(`${URL_BASE_BACKEND}/api/casos/${idCaso}/reporte-pdf`, {
            method: 'GET',
            headers: obtenerCabeceras(),
        });
        if (!respuesta.ok) throw new Error("Error al descargar PDF");
        
        // Convertimos la respuesta en un archivo descargable
        const blob = await respuesta.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Reporte_Caso_${idCaso}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        return { exito: true };
    } catch (e) {
        return { exito: false, mensaje: e.message };
    }
};