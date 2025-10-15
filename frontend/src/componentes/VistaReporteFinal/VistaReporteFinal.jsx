// frontend/src/componentes/VistaReporteFinal/VistaReporteFinal.jsx

import React, { useState, useEffect } from 'react';
import { obtenerDetallesCaso } from '../../servicios/api';
import './VistaReporteFinal.css';

const RenderizadorContenido = ({ contenido }) => {
    /**
     * Docstring:
     * Este componente es inteligente. Revisa si el contenido es un string JSON
     * y lo formatea de forma legible. Si no, lo muestra como texto normal.
     */
    let contenidoParseado;
    let esJson = false;
    
    try {
        contenidoParseado = JSON.parse(contenido);
        esJson = typeof contenidoParseado === 'object' && contenidoParseado !== null;
    } catch (e) {
      // ==================================================================
      // INICIO DE LA CORRECCION DEFINITIVA
      // Se reemplaza print() por console.log() para evitar el dialogo de impresion.
      console.log("Error: ",e);
      // ==================================================================
      console.log("El contenido no es JSON, se mostrara como texto:", contenido);
      // ==================================================================
      // FIN DE LA CORRECCION DEFINITIVA
      // ==================================================================
        contenidoParseado = contenido;
        esJson = false;
    }

    if (esJson) {
        return (
            <div className="contenido-json-legible">
                {Object.entries(contenidoParseado).map(([llave, valor]) => (
                    <p key={llave}>
                        <strong>{llave.replace(/_/g, ' ').toUpperCase()}:</strong>
                        {typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : String(valor)}
                    </p>
                ))}
            </div>
        );
    }

    return <pre className="contenido-texto-plano">{contenidoParseado}</pre>;
};

const parsearReporte = (textoReporte) => {
  if (!textoReporte) return {};
  const secciones = {};
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
  const [caso, setCaso] = useState(null);
  const [cargando, setCargando] = useState(true);

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

  if (cargando) {
    return <div className="vista-reporte-contenedor"><h3>Cargando reporte final...</h3></div>;
  }

  if (!caso || !caso.reporte_consolidado) {
    return <div className="vista-reporte-contenedor"><h3>No se pudo generar el reporte para este caso.</h3></div>;
  }
  
  // Ahora parseamos el reporte consolidado del objeto 'caso'
  const reporteParseado = parsearReporte(caso.reporte_consolidado);

  return (
    <div className="vista-reporte-contenedor">
      <h3>Paso 5: Reporte Final del Caso #{casoId}</h3>
      <p>A continuacion se presenta el analisis detallado y consolidado de su caso.</p>
      
      <div className="reporte-consolidado-contenido">
        {Object.keys(reporteParseado).length > 0 ? (
          Object.entries(reporteParseado).map(([titulo, contenido]) => (
            <div key={titulo} className="seccion-reporte">
              <h4 className="titulo-seccion">{titulo.replace(/_/g, ' ')}</h4>
              <RenderizadorContenido contenido={contenido} />
            </div>
          ))
        ) : (
          <p>El reporte generado no tiene un formato estructurado reconocible.</p>
        )}
      </div>
    </div>
  );
}

export default VistaReporteFinal;