// frontend/src/componentes/VisorReporte/VisorReporte.jsx

import React from 'react';
import './VisorReporte.css';

// ==============================================================================
// INICIO DE LA CORRECCION: Logica de renderizado mejorada
// ==============================================================================

// Componente auxiliar para renderizar los detalles de cada seccion del reporte
const SeccionReporte = ({ titulo, datosSeccion }) => {
  // Intentamos parsear los datos si son un string, si no, los usamos directamente
  let datosObjeto;
  try {
    datosObjeto = typeof datosSeccion === 'string' ? JSON.parse(datosSeccion) : datosSeccion;
  } catch (error) {
    console.log("Error al parsear datos de sección:", error);
    // Si falla el parseo de una sub-seccion, mostramos el texto original
    return (
      <>
        <tr className="fila-seccion-titulo">
          <td colSpan="2">{titulo.replace(/_/g, ' ')}</td>
        </tr>
        <tr>
          <th>Error</th>
          <td><pre className="reporte-error">{String(datosSeccion)}</pre></td>
        </tr>
      </>
    );
  }

  // Mapeamos claves tecnicas a etiquetas amigables para el usuario
  const etiquetas = {
    admisible: '¿Es Admisible?',
    justificacion: 'Justificación',
    hechos_clave: 'Resumen de Hechos Clave',
    informacion_suficiente: '¿Información Suficiente?',
    pregunta_para_usuario: 'Pregunta Adicional',
    area_competencia: 'Área de Competencia',
    justificacion_breve: 'Justificación de Competencia',
    id_estudiante_asignado: 'ID Estudiante Asignado',
    id_asesor_asignado: 'ID Asesor Asignado',
    operacion_db: 'Resultado de la Asignación',
    transcripcion_completa: 'Transcripción del Audio',
    resumen_puntos_clave: 'Resumen del Audio'
  };

  return (
    <>
      <tr className="fila-seccion-titulo">
        <td colSpan="2">{titulo.replace(/_/g, ' ')}</td>
      </tr>
      {Object.entries(datosObjeto).map(([clave, valor]) => {
        if (valor === '' || valor === null) return null;
        
        let contenidoCelda;
        if (typeof valor === 'boolean') {
          contenidoCelda = valor ? 'Sí' : 'No';
        } else {
          contenidoCelda = String(valor);
        }

        return (
          <tr key={clave}>
            <th>{etiquetas[clave] || clave.replace(/_/g, ' ')}</th>
            <td>{contenidoCelda}</td>
          </tr>
        );
      })}
    </>
  );
};

function VisorReporte({ jsonString }) {
  let datosGenerales;
  try {
    datosGenerales = JSON.parse(jsonString);
  } catch (error) {
    console.error("Error al parsear el JSON del reporte:", error);
    return <pre className="reporte-error">{jsonString}</pre>;
  }

  // Mapeamos las claves principales del reporte a titulos de seccion
  const titulosSeccion = {
    resultado_triaje: 'TRIaje',
    resultado_determinador_competencias: 'COMPETENCIA',
    resultado_repartidor: 'ASIGNACION',
    resultado_analisis_audio: 'ANALISIS AUDIO',
    resultado_agente_juridico: 'ANALISIS JURIDICO'
  };

  return (
    <div className="visor-reporte-contenedor">
      <table className="tabla-reporte">
        <tbody>
          {Object.entries(datosGenerales).map(([clavePrincipal, datosDeSeccion]) => (
            <SeccionReporte
              key={clavePrincipal}
              titulo={titulosSeccion[clavePrincipal] || clavePrincipal.toUpperCase()}
              datosSeccion={datosDeSeccion}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ==============================================================================
// FIN DE LA CORRECCION
// ==============================================================================

export default VisorReporte;