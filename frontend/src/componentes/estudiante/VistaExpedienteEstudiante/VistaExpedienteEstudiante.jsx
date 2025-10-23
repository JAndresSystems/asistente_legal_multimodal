// frontend/src/componentes/estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante.jsx

import React, { useState, useEffect } from 'react';
import { apiObtenerDetalleExpediente } from '../../../servicios/api';
import './VistaExpedienteEstudiante.css';

// Componente auxiliar para mostrar el reporte JSON de forma legible y segura
const VisorReporteIA = ({ reporteJson }) => {
  try {
    const reporteObjeto = JSON.parse(reporteJson);
    return (
      <div className="visor-reporte-ia">
        <h4>Reporte de Análisis IA</h4>
        <pre>{JSON.stringify(reporteObjeto, null, 2)}</pre>
      </div>
    );
  } catch (error) {
    console.error("Error al parsear el reporte JSON:", error);
    return (
      <div className="visor-reporte-ia">
        <h4>Reporte de Análisis IA</h4>
        <p>El reporte no tiene un formato JSON válido o aún no ha sido generado.</p>
        <pre>{reporteJson}</pre>
      </div>
    );
  }
};

const VistaExpedienteEstudiante = ({ expedienteId, onVolver }) => {
  const [expediente, setExpediente] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

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
                  {/* --- INICIO DE LA CORRECCION FINAL --- */}
                  {/* Usamos la propiedad correcta que nos envia la API */}
                  {evidencia.nombre_archivo}
                  {/* --- FIN DE LA CORRECCION FINAL --- */}
                </a>
                {/* NOTA: evidencia.tipo no está en el modelo EvidenciaLecturaSimple,
                    por lo que no lo mostraremos por ahora para evitar errores. */}
              </li>
            ))}
          </ul>
        ) : (
          <p>No se han aportado evidencias para este caso.</p>
        )}
      </div>

      {expediente.reporte_consolidado && (
        <div className="expediente-seccion">
          <VisorReporteIA reporteJson={expediente.reporte_consolidado} />
        </div>
      )}

    </div>
  );
};

export default VistaExpedienteEstudiante;