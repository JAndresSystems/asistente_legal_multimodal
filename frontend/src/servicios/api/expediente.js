// Ubicación: frontend/src/servicios/api/expediente.js

import { URL_BASE_BACKEND, obtenerCabeceras } from './config.js';

export const apiDescargarReporteExpedientePDF = async (idCaso) => {
  console.log(`API: Solicitando reporte en PDF para el expediente ${idCaso}`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/api/expedientes/${idCaso}/reporte-pdf`, {
      method: 'GET',
      headers: obtenerCabeceras(),
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const pdfBlob = await respuesta.blob();
    const url = window.URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `reporte_expediente_${idCaso}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);

    return { exito: true };

  } catch (error) {
    console.error("API: Error al descargar el reporte del expediente:", error);
    return { exito: false, mensaje: "No se pudo descargar el reporte." };
  }
};