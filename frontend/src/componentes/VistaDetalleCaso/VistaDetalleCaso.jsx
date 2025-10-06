// frontend/src/componentes/VistaDetalleCaso/VistaDetalleCaso.jsx
import React, { useState, useEffect } from 'react';
import { obtenerEstadoEvidencia } from '../../servicios/api'; 
import FormularioSubirEvidencia from '../FormularioSubirEvidencia/FormularioSubirEvidencia';
import ReporteAdmision from '../ReporteAdmision/ReporteAdmision';
import './VistaDetalleCaso.css';

function VistaDetalleCaso({ casoSeleccionado, onEvidenciaSubida, onAnalisisCompleto }) {
  const [reporteVisibleId, setReporteVisibleId] = useState(null);

  // Efecto para el polling (sondeo) del estado de la evidencia
  useEffect(() => {
    if (!casoSeleccionado) return;

    const evidenciaEnProceso = casoSeleccionado.evidencias.find(
      e => e.estado === 'encolado' || e.estado === 'procesando'
    );

    if (!evidenciaEnProceso) return;

    console.log(`POLLING: Iniciando monitoreo para evidencia ID: ${evidenciaEnProceso.id}`);
    const intervalo = setInterval(async () => {
      const data = await obtenerEstadoEvidencia(evidenciaEnProceso.id);
      if (data.estado === 'completado' || data.estado === 'error') {
        console.log(`POLLING: Análisis finalizado con estado '${data.estado}'. Recargando datos.`);
        clearInterval(intervalo);
        onAnalisisCompleto();
      }
    }, 5000);

    return () => clearInterval(intervalo);
  }, [casoSeleccionado, onAnalisisCompleto]);

  if (!casoSeleccionado) {
    return (
      <div className="vista-detalle-vacia">
        <h3>Panel de Detalles</h3>
        <p>Selecciona un caso de la lista para ver sus detalles, gestionar sus evidencias y ver los resultados del análisis de la IA.</p>
      </div>
    );
  }

  const manejarClickVerReporte = (evidencia) => {
    setReporteVisibleId(reporteVisibleId === evidencia.id ? null : evidencia.id);
  };
  
  const evidenciasOrdenadas = [...(casoSeleccionado.evidencias || [])].sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion));

  return (
    <div className="vista-detalle-caso">
      <div className="detalle-cabecera">
        <h3>Detalle del Caso</h3>
        <span className="caso-id">ID: {casoSeleccionado.id}</span>
      </div>
      <p className="descripcion-hechos">{casoSeleccionado.descripcion_hechos}</p>

      <hr className="separador-seccion" />

      <FormularioSubirEvidencia idCaso={casoSeleccionado.id} onEvidenciaSubida={onEvidenciaSubida} />

      <hr className="separador-seccion" />

      <div className="seccion-evidencias">
        <h4>Evidencias Adjuntas</h4>
        {evidenciasOrdenadas.length > 0 ? (
          <ul className="lista-evidencias">
            {evidenciasOrdenadas.map((evidencia) => (
              <li key={evidencia.id} className="item-evidencia-contenedor">
                <div className="item-evidencia">
                  <span className="nombre-archivo">{evidencia.ruta_archivo.split(/[\\/]/).pop()}</span>
                  <span className={`estado-evidencia ${evidencia.estado}`}>{evidencia.estado}</span>
                  <button
                    onClick={() => manejarClickVerReporte(evidencia)}
                    disabled={evidencia.estado !== 'completado'}
                    className="btn-ver-reporte"
                  >
                    {reporteVisibleId === evidencia.id ? 'Ocultar Reporte' : 'Ver Reporte'}
                  </button>
                </div>
                {reporteVisibleId === evidencia.id && evidencia.reporte_analisis && (
                  <div className="reporte-incrustado">
                    <ReporteAdmision reporteTexto={evidencia.reporte_analisis} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="sin-evidencias-mensaje">Este caso aún no tiene evidencias. Sube un archivo para comenzar el análisis.</p>
        )}
      </div>
    </div>
  );
}

export default VistaDetalleCaso;