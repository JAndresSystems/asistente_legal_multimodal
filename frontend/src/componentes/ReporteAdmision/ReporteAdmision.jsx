// frontend/src/componentes/ReporteAdmision/ReporteAdmision.jsx

import React, { useState, useMemo } from 'react';
import './ReporteAdmision.css';

// Componente auxiliar para renderizar objetos JSON de forma legible
const JsonViewer = ({ data }) => {
  // Primero, intentamos parsear el string como si fuera JSON
  try {
    const parsedData = JSON.parse(data);
    // Si tiene exito, lo formateamos de forma bonita
    return <pre className="json-viewer">{JSON.stringify(parsedData, null, 2)}</pre>;
  } catch (error) {
    // Si falla el parseo, significa que es texto plano, asi que lo mostramos tal cual.
    print(error.message.String)
    return <p className="texto-plano">{String(data)}</p>;
  }
};

// Componente para una seccion individual del acordeon
const PanelAcordeon = ({ titulo, contenido, estaAbierto, alHacerClick }) => {
  // No renderizamos el panel si no tiene contenido o si es "No aplica"
  if (!contenido || contenido.trim().toLowerCase() === 'no aplica' || contenido.trim() === 'null') {
    return null;
  }
  return (
    <div className="panel-acordeon">
      <button className="panel-cabecera" onClick={alHacerClick}>
        <span>{titulo}</span>
        <span className="indicador-acordeon">{estaAbierto ? '−' : '+'}</span>
      </button>
      {estaAbierto && (
        <div className="panel-contenido">
          {/* El JsonViewer decide si formatea como JSON o como texto plano */}
          <JsonViewer data={contenido} />
        </div>
      )}
    </div>
  );
};

// Componente principal del Reporte
const ReporteAdmision = ({ reporteTexto }) => {
  // El estado ahora controla el titulo del panel activo
  const [panelActivo, setPanelActivo] = useState('Triaje'); // El panel de Triaje estara abierto por defecto

  // Usamos useMemo para parsear el reporte una sola vez y no en cada renderizado.
  // Esta es la nueva logica de parseo basada en etiquetas [ETIQUETA]...[/ETIQUETA]
  const secciones = useMemo(() => {
    if (!reporteTexto) return {};

    const parsearSeccion = (etiqueta) => {
      const regex = new RegExp(`\\[${etiqueta}\\]([\\s\\S]*?)\\[/${etiqueta}\\]`, 'i');
      const match = reporteTexto.match(regex);
      return match ? match[1].trim() : null;
    };
    
    return {
      'Triaje': parsearSeccion('TRIAJE'),
      'Análisis de Documento': parsearSeccion('ANALISIS_DOCUMENTO'),
      'Análisis de Audio': parsearSeccion('ANALISIS_AUDIO'),
      'Determinación de Competencia': parsearSeccion('COMPETENCIA'),
      'Asignación de Equipo': parsearSeccion('ASIGNACION'),
      'Análisis Jurídico Preliminar': parsearSeccion('ANALISIS_JURIDICO'),
      'Documento Generado': parsearSeccion('DOCUMENTO_GENERADO'),
    };
  }, [reporteTexto]);

  const manejarClickPanel = (tituloPanel) => {
    // Si hacemos clic en el panel que ya esta abierto, se cierra. Si no, se abre el nuevo.
    setPanelActivo(panelActivo === tituloPanel ? null : tituloPanel);
  };
  
  // Si no hay texto de reporte, no mostramos nada.
  if (!reporteTexto) {
    return <div className="reporte-contenedor"><p>El reporte de análisis aparecerá aquí una vez que la evidencia sea procesada.</p></div>;
  }

  return (
    <div className="reporte-contenedor">
      <h3 className="reporte-titulo-principal">Reporte de Análisis del Sistema</h3>
      <div className="acordeon">
        {/* Mapeamos cada seccion parseada a un panel del acordeon */}
        {Object.entries(secciones).map(([titulo, contenido]) => (
          <PanelAcordeon
            key={titulo}
            titulo={titulo}
            contenido={contenido}
            estaAbierto={panelActivo === titulo}
            alHacerClick={() => manejarClickPanel(titulo)}
          />
        ))}
      </div>
    </div>
  );
};

export default ReporteAdmision;