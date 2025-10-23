// frontend/src/componentes/estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante.jsx

import React, { useState, useEffect } from 'react';
// --- INICIO DE LA MODIFICACION ---
import { apiObtenerDetalleExpediente, apiConsultarAgenteJuridico } from '../../../servicios/api';
// --- FIN DE LA MODIFICACION ---
import './VistaExpedienteEstudiante.css';

// Componente auxiliar para mostrar el reporte JSON de forma legible y segura
// const VisorReporteIA = ({ reporteJson }) => {
//   try {
//     const reporteObjeto = JSON.parse(reporteJson);
//     return (
//       <div className="visor-reporte-ia">
//         <h4>Reporte de Análisis IA</h4>
//         <pre>{JSON.stringify(reporteObjeto, null, 2)}</pre>
//       </div>
//     );
//   } catch (error) {
//     console.error("Error al parsear el reporte JSON:", error);
//     return (
//       <div className="visor-reporte-ia">
//         <h4>Reporte de Análisis IA</h4>
//         <p>El reporte no tiene un formato JSON válido o aún no ha sido generado.</p>
//         <pre>{reporteJson}</pre>
//       </div>
//     );
//   }
// };


const VisorReporteEstructurado = ({ reporteJson }) => {
  try {
    const reporte = JSON.parse(reporteJson);

    // Funcion auxiliar para renderizar una seccion del reporte
    const renderizarSeccion = (titulo, data) => {
      if (!data) return null;
      return (
        <div className="reporte-seccion">
          <h4>{titulo}</h4>
          {Object.entries(data).map(([clave, valor]) => {
            if (typeof valor === 'object' && valor !== null) return null; // Omitir objetos anidados por ahora
            const claveLegible = clave.replace(/_/g, ' ');
            const valorLegible = typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : String(valor);
            return (
              <p key={clave}><strong>{claveLegible}:</strong> {valorLegible}</p>
            );
          })}
        </div>
      );
    };

    return (
      <div className="visor-reporte-estructurado">
        <h3>Reporte de Análisis IA</h3>
        {renderizarSeccion("Fase de Triaje", reporte.TRIEJE)}
        {renderizarSeccion("Determinación de Competencia", reporte.COMPETENCIA)}
        {renderizarSeccion("Asignación de Caso", reporte.ASIGNACION)}
        {renderizarSeccion("Análisis Jurídico Inicial", reporte.ANALISIS_JURIDICO)}
      </div>
    );
  } catch (error) {
    console.error("Error al parsear el reporte JSON:", error);
    return (
      <div className="visor-reporte-ia">
        <h4>Reporte de Análisis IA (Formato no reconocido)</h4>
        <pre>{reporteJson}</pre>
      </div>
    );
  }
};



const VistaExpedienteEstudiante = ({ expedienteId, onVolver }) => {
  const [expediente, setExpediente] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  // --- INICIO DE LA MODIFICACION: Estados para el Agente Juridico ---
  const [preguntaAgente, setPreguntaAgente] = useState('');
  const [respuestaAgente, setRespuestaAgente] = useState(null);
  const [cargandoAgente, setCargandoAgente] = useState(false);
  const [errorAgente, setErrorAgente] = useState('');
  // --- FIN DE LA MODIFICACION ---

  useEffect(() => {
    const cargarExpediente = async () => {
      if (!expedienteId) return;
      try {
        setCargando(true);
        setError('');
        const datosExpediente = await apiObtenerDetalleExpediente(expedienteId);
        setExpediente(datosExpediente);
      } catch (err) {
        setError(err.message || 'Ocurrió un error al cargar el expediente.');
      } finally {
        setCargando(false);
      }
    };
    cargarExpediente();
  }, [expedienteId]);

  // --- INICIO DE LA MODIFICACION: Funcion para manejar la consulta al agente ---
  const handleConsultarAgente = async (e) => {
    e.preventDefault(); // Evita que la pagina se recargue al enviar el formulario
    if (!preguntaAgente.trim()) return; // No enviar preguntas vacias

    setCargandoAgente(true);
    setErrorAgente('');
    setRespuestaAgente(null);

    try {
      const respuesta = await apiConsultarAgenteJuridico(expedienteId, preguntaAgente);
      setRespuestaAgente(respuesta);
    } catch (err) {
      setErrorAgente(err.message || 'Ocurrió un error al consultar al agente.');
    } finally {
      setCargandoAgente(false);
    }
  };
  // --- FIN DE LA MODIFICACION ---

  if (cargando) {
    return <div className="vista-expediente-cargando">Cargando expediente...</div>;
  }

  if (error) {
    return <div className="vista-expediente-error">Error: {error} <button onClick={onVolver}>Volver</button></div>;
  }

  if (!expediente) {
    return <div className="vista-expediente-cargando">No se encontró el expediente.</div>;
  }

  const baseURL = 'http://127.0.0.1:8000';

  return (
    <div className="vista-expediente-contenedor">
      <button onClick={onVolver} className="boton-volver">&larr; Volver al Dashboard</button>
      
      <h2>Detalle del Expediente #{expediente.id}</h2>
      
      <div className="expediente-metadata">
        <p><strong>Fecha de Creación:</strong> {new Date(expediente.fecha_creacion).toLocaleString('es-CO')}</p>
        <p><strong>Estado:</strong> <span className={`estado-caso estado-${expediente.estado}`}>{expediente.estado.replace('_', ' ')}</span></p>
      </div>

      <div className="expediente-seccion">
        <h3>Descripción de los Hechos</h3>
        <p>{expediente.descripcion_hechos}</p>
      </div>

      <div className="expediente-seccion">
        <h3>Evidencias Aportadas por el Usuario</h3>
        {expediente.evidencias && expediente.evidencias.length > 0 ? (
          <ul className="lista-evidencias">
            {expediente.evidencias.map((evidencia) => (
              <li key={evidencia.id}>
                <a 
                  href={`${baseURL}${evidencia.ruta_archivo}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                >
                  {evidencia.nombre_archivo}
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p>No se han aportado evidencias para este caso.</p>
        )}
      </div>

      {/* --- INICIO DE LA MODIFICACION: Usamos el nuevo visor de reporte estructurado --- */}
      {expediente.reporte_consolidado && (
        <div className="expediente-seccion">
          <VisorReporteEstructurado reporteJson={expediente.reporte_consolidado} />
        </div>
      )}
      {/* --- FIN DE LA MODIFICACION --- */}

      <div className="expediente-seccion">
        <h3>Asistente Jurídico (IA)</h3>
        <p>Realice una consulta sobre este caso al agente especializado en Derecho Privado.</p>
        
        <form onSubmit={handleConsultarAgente} className="agente-formulario">
          <textarea
            value={preguntaAgente}
            onChange={(e) => setPreguntaAgente(e.target.value)}
            placeholder="Escriba su pregunta aquí..."
            className="agente-textarea"
            disabled={cargandoAgente}
          />
          <button type="submit" className="agente-boton-enviar" disabled={cargandoAgente}>
            {cargandoAgente ? 'Consultando...' : 'Consultar'}
          </button>
        </form>

        <div className="agente-area-respuesta">
          {cargandoAgente && <p>Procesando su consulta...</p>}
          {errorAgente && <p className="agente-error">Error: {errorAgente}</p>}
          {respuestaAgente && (
            <div className="agente-respuesta-formateada">
              <h4>Respuesta del Agente:</h4>
              <p>{respuestaAgente.contenido}</p>
              <h5>Fuentes Citadas:</h5>
              <ul>
                {respuestaAgente.fuentes.map((fuente, index) => (
                  <li key={index}>{fuente}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VistaExpedienteEstudiante;