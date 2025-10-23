// frontend/src/componentes/usuario/VisorReporte/VisorReporte.jsx

import React from 'react';
import './VisorReporte.css';

const SeccionReporte = ({ titulo, datosSeccion }) => {
  let datosObjeto;
  // ==============================================================================
  // INICIO DE LA CORRECCION: Hacemos el parseo a prueba de fallos
  // ==============================================================================
  // Solo intentamos parsear si es un string que parece un objeto o array
  if (typeof datosSeccion === 'string' && (datosSeccion.startsWith('{') || datosSeccion.startsWith('['))) {
    try {
      datosObjeto = JSON.parse(datosSeccion);
    } catch (error) {
      console.log("Error al parsear datos de la sección:", error);
      // Si el parseo falla, lo tratamos como un string simple
      datosObjeto = { "valor": datosSeccion };
    }
  } else if (typeof datosSeccion === 'object' && datosSeccion !== null) {
    // Si ya es un objeto, lo usamos directamente
    datosObjeto = datosSeccion;
  } else {
    // Para strings simples, números, etc., lo envolvemos en un objeto para mostrarlo
    datosObjeto = { "resultado": String(datosSeccion) };
  }
  // ==============================================================================
  // FIN DE LA CORRECCION
  // ==============================================================================

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
    resumen_puntos_clave: 'Resumen del Audio',
    resultado: 'Resultado',
    valor: 'Valor'
  };

  return (
    <>
      <tr className="fila-seccion-titulo">
        <td colSpan="2">{titulo.replace(/_/g, ' ')}</td>
      </tr>
      {Object.entries(datosObjeto).map(([clave, valor]) => {
        if (valor === '' || valor === null) return null;
        
        let contenidoCelda = typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : String(valor);

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

  const titulosSeccion = {
    TRIEJE: 'Resultado del Triaje',
    COMPETENCIA: 'Determinación de Competencia',
    ASIGNACION: 'Resultado de la Asignación',
    ANALISIS_AUDIO: 'Análisis de Audio',
    ANALISIS_JURIDICO: 'Análisis Jurídico'
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

export default VisorReporte;