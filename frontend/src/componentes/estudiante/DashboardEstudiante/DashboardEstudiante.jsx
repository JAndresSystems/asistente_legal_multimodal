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
// --- FUNCIÓN AUXILIAR PARA RENDERIZAR ESTRELLAS ---
  const renderizarEstrellas = (calificacion) => {
    // Verificamos si es null o undefined explícitamente
    if (calificacion === null || calificacion === undefined) return <span className="sin-calificacion">-</span>;
    
    // Redondeamos para dibujar las estrellas (ej: 3.8 -> 4 estrellas visuales)
    const notaRedondeada = Math.round(calificacion);
    
    return (
        <span className="estrellas">
            {"★".repeat(notaRedondeada)}
            {"☆".repeat(5 - notaRedondeada)}
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
            {listaDeCasos.map((caso) => {
              
              // Detectamos si el caso ya no está activo para este estudiante
              const esInactivo = ['cerrado', 'reasignado', 'rechazado'].includes(caso.estado);

              return (
                <tr key={caso.id} className={esInactivo ? 'fila-cerrada' : ''}>
                  <td>#{caso.id}</td>
                  <td>{new Date(caso.fecha_creacion).toLocaleDateString('es-ES')}</td>
                  
                  {/* ESTADO */}
                  <td>
                    <span className={`estado-caso estado-${caso.estado.replace('_', '-')}`}>
                      {caso.estado === 'reasignado' ? 'Reasignado (Cerrado)' : caso.estado.replace('_', ' ')}
                    </span>
                  </td>
                  
                  {/* EVALUACIÓN (Nota Decimal) */}
                  <td>
                      {caso.calificacion !== null ? (
                          <div className="celda-evaluacion" title={caso.comentario_docente || "Sin comentario"}>
                              {renderizarEstrellas(caso.calificacion)}
                              <span className="nota-numerica" style={{marginLeft:'5px', fontWeight:'bold'}}>
                                  ({caso.calificacion}/5.0)
                              </span>
                          </div>
                      ) : (
                          <span className="pendiente-eval" style={{color:'#999'}}>En curso</span>
                      )}
                  </td>

                  {/* ACCIONES */}
                  <td>
                    <div className="acciones-contenedor">
                      {procesandoId === caso.id ? (
                        <span>Procesando...</span>
                      ) : (
                        <>
                          {/* ACEPTAR / RECHAZAR (Solo si es nuevo) */}
                          {caso.estado === 'pendiente_aceptacion' && (
                            <>
                              <button onClick={() => handleAceptar(caso.id)} className="boton-accion aceptar">Aceptar</button>
                              <button onClick={() => handleRechazar(caso.id)} className="boton-accion rechazar">Rechazar</button>
                            </>
                          )}
                          
                          {/* GESTIONAR (Solo si está activo) */}
                          {caso.estado === 'asignado' && (
                            <button onClick={() => onVerExpediente(caso.id)} className="boton-accion ver">
                              Gestionar
                            </button>
                          )}

                          {/* VER HISTORIAL (Si está cerrado/reasignado) */}
                          {esInactivo && (
                             <button 
                               onClick={() => onVerExpediente(caso.id)} 
                               className="boton-accion ver"
                               style={{backgroundColor:'#6c757d', borderColor:'#6c757d'}}
                             >
                               Ver Historial
                             </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default DashboardEstudiante;