import React from 'react';
import './ReporteAdmision.css';

// Función auxiliar para parsear el reporte. Busca valores después de un título.
const parsearValor = (texto, titulo) => {
  // Crea una expresión regular para encontrar el título seguido de dos puntos y un espacio.
  // Captura todo hasta el final de la línea.
  const regex = new RegExp(`${titulo}:\\s*(.*)`);
  const match = texto.match(regex);
  return match ? match[1] : 'No disponible';
};

const ReporteAdmision = ({ reporteTexto }) => {
  if (!reporteTexto || !reporteTexto.includes("--- REPORTE DE ADMISIÓN AUTOMÁTICA ---")) {
    // Si no hay texto o no es un reporte, muestra el texto plano.
    return <pre className="reporte-texto-plano">{reporteTexto}</pre>;
  }

  // Parseamos cada campo del reporte usando nuestra función auxiliar.
  const veredicto = parsearValor(reporteTexto, 'VEREDICTO DEL TRIAJE');
  const justificacion = parsearValor(reporteTexto, 'Justificación');
  const area = parsearValor(reporteTexto, 'Área de Competencia Determinada');
  const idEstudiante = parsearValor(reporteTexto, '- ID Estudiante');
  const idAsesor = parsearValor(reporteTexto, '- ID Asesor');

  const esAdmisible = veredicto.includes('ADMISIBLE');

  return (
    <div className="reporte-contenedor">
      <h4 className="reporte-titulo">Reporte de Admisión Automática</h4>
      
      <div className="reporte-seccion">
        <div className="reporte-campo">
          <strong>Veredicto del Triaje:</strong>
          <span className={esAdmisible ? 'etiqueta-admisible' : 'etiqueta-no-admisible'}>
            {veredicto}
          </span>
        </div>
        <div className="reporte-campo">
          <strong>Justificación:</strong>
          <p>{justificacion}</p>
        </div>
      </div>

      {esAdmisible && (
        <div className="reporte-seccion">
          <h5 className="reporte-subtitulo">Clasificación y Asignación</h5>
          <div className="reporte-campo">
            <strong>Área de Competencia:</strong>
            <span>{area}</span>
          </div>
          <div className="reporte-campo">
            <strong>Equipo Asignado (Simulado):</strong>
            <ul>
              <li>Estudiante ID: {idEstudiante}</li>
              <li>Asesor ID: {idAsesor}</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReporteAdmision;