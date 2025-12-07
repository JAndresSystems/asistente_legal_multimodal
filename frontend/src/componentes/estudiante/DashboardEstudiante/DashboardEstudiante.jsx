import React, { useState, useEffect, useCallback } from 'react';
import { apiObtenerMisAsignaciones, apiAceptarAsignacion, apiRechazarAsignacion } from '../../../servicios/api';
import { useAuth } from '../../../contextos/ContextoAutenticacion';
import './DashboardEstudiante.css';

function DashboardEstudiante({ onVerExpediente }) {
   const { usuario } = useAuth();
  const [listaDeCasos, setListaDeCasos] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);
  const [procesandoId, setProcesandoId] = useState(null); 
  
  const cargarAsignaciones = useCallback(async () => {
    try {
      setEstaCargando(true);
      const casosAsignados = await apiObtenerMisAsignaciones();
      setListaDeCasos(casosAsignados);
    } catch (err) {
      console.error("Error al cargar las asignaciones:", err);
      setError("No se pudieron cargar sus casos asignados.");
    } finally {
      setEstaCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarAsignaciones();
  }, [cargarAsignaciones]);
  
  const handleAceptar = async (idCaso) => {
    setProcesandoId(idCaso);
    try {
      await apiAceptarAsignacion(idCaso);
      cargarAsignaciones();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setProcesandoId(null);
    }
  };

  const handleRechazar = async (idCaso) => {
    setProcesandoId(idCaso);
    try {
      await apiRechazarAsignacion(idCaso);
      cargarAsignaciones();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setProcesandoId(null);
    }
  };

  // --- FUNCIÓN AUXILIAR PARA RENDERIZAR ESTRELLAS ---
  const renderizarEstrellas = (calificacion) => {
    if (!calificacion) return <span className="sin-calificacion">-</span>;
    // Crea un array de N elementos y los mapea a estrellas
    return (
        <span className="estrellas">
            {"★".repeat(calificacion)}
            {"☆".repeat(5 - calificacion)}
        </span>
    );
  };

  if (estaCargando && listaDeCasos.length === 0) {
    return <div className="dashboard-estudiante-contenedor"><p>Cargando sus asignaciones...</p></div>;
  }
  if (error) {
    return <div className="dashboard-estudiante-contenedor error"><p>{error}</p></div>;
  }

  return (
    <div className="dashboard-estudiante-contenedor">
      <div className="dashboard-saludo">
        <h2>Bienvenido, {usuario?.nombre_completo}</h2>
        <p>Gestión académica y operativa de casos.</p>
      </div>
      <div className="dashboard-cabecera">
        <h1>Panel de Casos</h1>
      </div>
      
      {listaDeCasos.length === 0 ? (
        <p>Actualmente no tiene casos asignados.</p>
      ) : (
        <table className="tabla-casos-estudiante">
          <thead>
            <tr>
              <th>ID</th>
              <th>Fecha</th>
              <th>Estado</th>
              {/* --- NUEVA COLUMNA --- */}
              <th>Evaluación</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {listaDeCasos.map((caso) => (
              <tr key={caso.id} className={caso.estado === 'cerrado' ? 'fila-cerrada' : ''}>
                <td>#{caso.id}</td>
                <td>{new Date(caso.fecha_creacion).toLocaleDateString('es-ES')}</td>
                <td>
                  <span className={`estado-caso estado-${caso.estado.replace('_', '-')}`}>
                    {caso.estado.replace('_', ' ')}
                  </span>
                </td>
                
                {/* --- CELDA DE EVALUACIÓN --- */}
                <td>
                    {caso.estado === 'cerrado' ? (
                        <div className="celda-evaluacion" title={caso.comentario_docente || "Sin comentario"}>
                            {renderizarEstrellas(caso.calificacion)}
                            {caso.calificacion && <span className="nota-numerica">({caso.calificacion}/5)</span>}
                        </div>
                    ) : (
                        <span className="pendiente-eval">En curso</span>
                    )}
                </td>

                <td>
                  <div className="acciones-contenedor">
                    {procesandoId === caso.id ? (
                      <span>Procesando...</span>
                    ) : (
                      <>
                        {caso.estado === 'pendiente_aceptacion' && (
                          <>
                            <button onClick={() => handleAceptar(caso.id)} className="boton-accion aceptar">Aceptar</button>
                            <button onClick={() => handleRechazar(caso.id)} className="boton-accion rechazar">Rechazar</button>
                          </>
                        )}
                        
                        {/* AHORA PERMITIMOS VER CASOS CERRADOS TAMBIÉN */}
                        {(caso.estado === 'asignado' || caso.estado === 'cerrado') && (
                          <button onClick={() => onVerExpediente(caso.id)} className="boton-accion ver">
                            {caso.estado === 'cerrado' ? 'Ver Histórico' : 'Gestionar'}
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default DashboardEstudiante;