// C:\react\asistente_legal_multimodal\frontend\src\componentes\usuario\VistaDetalleCaso\VistaDetalleCaso.jsx

import React, { useState, useEffect, useCallback } from 'react';
import { obtenerDetallesCaso } from '../../../servicios/api';
import FormularioSubirEvidencia from '../FormularioSubirEvidencia/FormularioSubirEvidencia';
import VisorReporte from '../VisorReporte/VisorReporte';
import './VistaDetalleCaso.css';

function VistaDetalleCaso({ casoId, onVolverAlDashboard }) {
  const [caso, setCaso] = useState(null);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  // Se envuelve la función de carga en useCallback.
  // Esto asegura que la función no se recree en cada renderizado,
  // a menos que su dependencia (casoId) cambie.
  const cargarDatosDelCaso = useCallback(async () => {
    if (!casoId) {
      setError("No se ha proporcionado un ID de caso.");
      setEstaCargando(false);
      return;
    }
    try {
      setEstaCargando(true);
      const detallesDelCaso = await obtenerDetallesCaso(casoId);
      setCaso(detallesDelCaso);
      setError(null);
    } catch (err) {
      setError("No se pudieron cargar los detalles del caso. " + err.message);
    } finally {
      setEstaCargando(false);
    }
  }, [casoId]);

  // El useEffect ahora puede incluir 'cargarDatosDelCaso' en sus dependencias
  // de forma segura, eliminando la advertencia de eslint.
  useEffect(() => {
    cargarDatosDelCaso();
  }, [cargarDatosDelCaso]);

  // Este manejador simplemente vuelve a llamar a la función de carga de datos.
  const manejarSubidaCompletada = () => {
    console.log("Evidencia subida. Refrescando datos del caso...");
    cargarDatosDelCaso();
  };
  
  if (estaCargando) {
    return <div className="detalle-contenedor"><p>Cargando información del caso...</p></div>;
  }

  if (error) {
    return (
      <div className="detalle-contenedor">
        <p className="mensaje-error">{error}</p>
        <button onClick={onVolverAlDashboard} className="boton-volver">
          &larr; Volver a Mis Casos
        </button>
      </div>
    );
  }

  if (!caso) {
    return null;
  }
  
  const URL_BASE_BACKEND = "http://127.0.0.1:8000";

  return (
    <div className="detalle-contenedor">
      <button onClick={onVolverAlDashboard} className="boton-volver">&larr; Volver a Mis Casos</button>
      <h1>Detalles del Caso #{caso.id}</h1>

      <div className="seccion-detalle">
        <h2>Resumen del Caso</h2>
        <div className="info-resumen">
          <div className="info-item">
            <strong>Estado Actual:</strong>
            {caso.estado && typeof caso.estado === 'string' ? (
              <span className={`estado-caso ${caso.estado}`}>{caso.estado.replace('_', ' ')}</span>
            ) : (
              <span className="estado-caso pendiente">No definido</span>
            )}
          </div>
          <div className="info-item"><strong>Área Asignada:</strong><span>{caso.area_asignada || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Estudiante a Cargo:</strong><span>{caso.estudiante_asignado || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Asesor Supervisor:</strong><span>{caso.asesor_asignado || 'Pendiente'}</span></div>
        </div>
      </div>

      <div className="seccion-detalle">
        <h2>Descripción de los Hechos</h2>
        <p className="descripcion-hechos">{caso.descripcion_hechos}</p>
      </div>
      
      {caso.reporte_consolidado && (
        <div className="seccion-detalle">
          <h2>Informe Final de Agentes</h2>
          <VisorReporte jsonString={caso.reporte_consolidado} />
        </div>
      )}

      <hr className="separador-seccion" />
      <div className="seccion-detalle">
        <h2>Añadir Nueva Evidencia</h2>
        <FormularioSubirEvidencia
          casoId={caso.id}
          onSubidaCompletada={manejarSubidaCompletada}
        />
      </div>
      <hr className="separador-seccion" />
      <div className="seccion-detalle">
        <h4>Evidencias Adjuntas</h4>
        {caso.evidencias && caso.evidencias.length > 0 ? (
          <ul className="lista-evidencias">
            {caso.evidencias.map((evidencia) => (
              <li key={evidencia.id} className="item-evidencia">
                {evidencia.ruta_archivo && typeof evidencia.ruta_archivo === 'string' ? (
                   <a
                  href={`${URL_BASE_BACKEND}${evidencia.ruta_archivo}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="enlace-evidencia"
                >
                  {evidencia.nombre_archivo}
                </a>
                ) : (
                  <span className="enlace-evidencia-invalido">
                    {evidencia.nombre_archivo} (Archivo no disponible)
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p>Este caso aún no tiene evidencias.</p>
        )}
      </div>
    </div>
  );
}

export default VistaDetalleCaso;