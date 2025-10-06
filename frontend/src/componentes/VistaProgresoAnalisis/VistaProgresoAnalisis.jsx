import React, { useState, useEffect, useRef } from 'react';
import { obtenerDetallesCaso } from '../../servicios/api';
import './VistaProgresoAnalisis.css';

// Componente de ayuda para el icono de estado
const IconoEstado = ({ estado }) => {
  if (estado === 'procesando') {
    return <div className="spinner"></div>;
  }
  return null;
};

function VistaProgresoAnalisis({ casoId, onAnalisisCompletado }) {
  /**
   * """
   * Docstring:
   * Muestra el estado en tiempo real de cada evidencia subida para un caso.
   * Realiza un sondeo periodico a la API para refrescar los estados.
   *
   * Args:
   *   casoId (number): El ID del caso cuyas evidencias se van a monitorear.
   *   onAnalisisCompletado (function): Callback para notificar a App.jsx
   *                                    que todos los analisis terminaron.
   * """
   */
  
  const [evidencias, setEvidencias] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [todoCompletado, setTodoCompletado] = useState(false);
  const idIntervaloRef = useRef(null);

  useEffect(() => {
    const recargarEvidencias = async () => {
      if (!casoId) return;

      try {
        // --- LA SIMULACION HA SIDO REEMPLAZADA POR LA LLAMADA REAL ---
        const datosCaso = await obtenerDetallesCaso(casoId);
        
        setEvidencias(datosCaso.evidencias || []);
        
        const estanTodosTerminados = datosCaso.evidencias && datosCaso.evidencias.length > 0 && datosCaso.evidencias.every(
          e => e.estado === 'completado' || e.estado === 'error'
        );

        if (estanTodosTerminados) {
          setTodoCompletado(true);
          clearInterval(idIntervaloRef.current);
          console.log("PROGRESO: Todos los analisis han finalizado. Sondeo detenido.");
        }
      } catch (error) {
        console.error("PROGRESO: Error al recargar las evidencias", error);
        clearInterval(idIntervaloRef.current);
      } finally {
        setCargando(false);
      }
    };

    recargarEvidencias();
    idIntervaloRef.current = setInterval(recargarEvidencias, 3000);

    return () => {
      clearInterval(idIntervaloRef.current);
    };
  }, [casoId]);

  if (cargando) {
    return <div className="vista-progreso-contenedor"><h3>Cargando estado de evidencias...</h3></div>;
  }

  return (
    <div className="vista-progreso-contenedor">
      <h3>Paso 4: Analizando Evidencias del Caso #{casoId}</h3>
      <ul className="lista-evidencias">
        {evidencias.length > 0 ? (
          evidencias.map(evidencia => (
            <li key={evidencia.id} className="item-evidencia">
              <span className="nombre-evidencia">{evidencia.ruta_archivo.split('\\').pop().split('/').pop()}</span>
              <span className={`estado-evidencia ${evidencia.estado}`}>
                <IconoEstado estado={evidencia.estado} />
                {evidencia.estado}
              </span>
            </li>
          ))
        ) : (
          <p>Aun no se han subido evidencias para este caso.</p>
        )}
      </ul>

      <div className="contenedor-acciones-progreso">
        <p>
          {todoCompletado 
            ? '¡El análisis ha finalizado!' 
            : 'Por favor, espera mientras nuestros agentes analizan tus documentos...'}
        </p>
        <button 
          className="boton-ver-reporte"
          onClick={onAnalisisCompletado}
          disabled={!todoCompletado}
        >
          Continuar al Reporte Final
        </button>
      </div>
    </div>
  );
}

export default VistaProgresoAnalisis;