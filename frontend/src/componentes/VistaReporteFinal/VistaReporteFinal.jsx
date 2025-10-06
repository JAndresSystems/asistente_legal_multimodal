import React, { useState, useEffect } from 'react';
import { obtenerDetallesCaso } from '../../servicios/api';
import './VistaReporteFinal.css';

/**
 * """
 * Docstring:
 * Parsea el texto del reporte de analisis, que viene como un string
 * unico, y lo divide en un objeto con secciones basadas en etiquetas.
 *
 * Args:
 *   textoReporte (string): El string completo del reporte_analisis.
 *
 * Returns:
 *   (Object): Un objeto donde cada clave es el nombre de una seccion
 *             (ej. 'TRIAGE') y el valor es su contenido.
 * """
 */
const parsearReporte = (textoReporte) => {
  if (!textoReporte) return {};
  const secciones = {};
  // Expresion regular para encontrar todas las etiquetas [ETIQUETA]...[/ETIQUETA]
  const regex = /\[(.*?)\]([\s\S]*?)\[\/\1\]/g;
  let match;
  while ((match = regex.exec(textoReporte)) !== null) {
    const nombreSeccion = match[1];
    const contenidoSeccion = match[2].trim();
    secciones[nombreSeccion] = contenidoSeccion;
  }
  return secciones;
};


function VistaReporteFinal({ casoId }) {
  /**
   * """
   * Docstring:
   * Muestra el reporte final y estructurado del analisis de todas las
   * evidencias de un caso.
   *
   * Args:
   *   casoId (number): El ID del caso del cual se mostrara el reporte.
   * """
   */
  const [caso, setCaso] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [acordeonActivo, setAcordeonActivo] = useState(null); // ID de la evidencia activa

  useEffect(() => {
    const cargarDatosDelCaso = async () => {
      if (!casoId) return;
      try {
        const datosCaso = await obtenerDetallesCaso(casoId);
        setCaso(datosCaso);
      } catch (error) {
        console.error("REPORTE: Error al cargar los datos del caso", error);
      } finally {
        setCargando(false);
      }
    };
    cargarDatosDelCaso();
  }, [casoId]);

  const manejarClickAcordeon = (idEvidencia) => {
    setAcordeonActivo(acordeonActivo === idEvidencia ? null : idEvidencia);
  };

  if (cargando) {
    return <div className="vista-reporte-contenedor"><h3>Cargando reporte final...</h3></div>;
  }

  if (!caso) {
    return <div className="vista-reporte-contenedor"><h3>No se pudieron cargar los datos del caso.</h3></div>;
  }

  return (
    <div className="vista-reporte-contenedor">
      <h3>Paso 5: Reporte Final del Caso #{casoId}</h3>
      <p>A continuacion se presenta el analisis detallado de cada una de las evidencias proporcionadas.</p>
      
      <div className="acordeon-contenedor">
        {caso.evidencias.map((evidencia) => {
          const estaAbierto = acordeonActivo === evidencia.id;
          const reporteParseado = parsearReporte(evidencia.reporte_analisis);

          return (
            <div key={evidencia.id} className="item-acordeon">
              <div 
                className={`cabecera-acordeon ${estaAbierto ? 'activo' : ''}`}
                onClick={() => manejarClickAcordeon(evidencia.id)}
              >
                <span className="titulo-evidencia">{evidencia.ruta_archivo.split('\\').pop().split('/').pop()}</span>
                <span className={`icono-acordeon ${estaAbierto ? 'abierto' : ''}`}>&#9656;</span>
              </div>
              <div className={`panel-acordeon ${estaAbierto ? 'abierto' : ''}`}>
                {Object.keys(reporteParseado).length > 0 ? (
                  Object.entries(reporteParseado).map(([titulo, contenido]) => (
                    <div key={titulo} className="seccion-reporte">
                      <h4 className="titulo-seccion">{titulo.replace(/_/g, ' ')}</h4>
                      <pre className="detalle-reporte">{contenido}</pre>
                    </div>
                  ))
                ) : (
                  <p>No se encontró un reporte estructurado para esta evidencia.</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default VistaReporteFinal;