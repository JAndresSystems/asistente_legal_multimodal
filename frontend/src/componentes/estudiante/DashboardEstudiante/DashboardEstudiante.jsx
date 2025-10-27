// frontend/src/componentes/estudiante/DashboardEstudiante/DashboardEstudiante.jsx

import React, { useState, useEffect, useCallback } from 'react';

import { apiObtenerMisAsignaciones, apiAceptarAsignacion, apiRechazarAsignacion } from '../../../servicios/api';

import './DashboardEstudiante.css';

function DashboardEstudiante({ onVerExpediente }) {
  const [listaDeCasos, setListaDeCasos] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);
  // ---Estado para manejar acciones en curso ---
  const [procesandoId, setProcesandoId] = useState(null); // Guarda el ID del caso que se está aceptando/rechazando
  

  // ---  carga de datos reutilizable ---
  const cargarAsignaciones = useCallback(async () => {
    try {
      setEstaCargando(true);
      const casosAsignados = await apiObtenerMisAsignaciones();
      setListaDeCasos(casosAsignados);
    } catch (err) {
      console.error("Error al cargar las asignaciones:", err);
      setError("No se pudieron cargar sus casos asignados. Verifique que su perfil de estudiante esté activo.");
    } finally {
      setEstaCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarAsignaciones();
  }, [cargarAsignaciones]);
  

  // --- Funciones para manejar las acciones ---
  const handleAceptar = async (idCaso) => {
    setProcesandoId(idCaso);
    try {
      await apiAceptarAsignacion(idCaso);
      // Recargamos la lista para que se actualice el estado del caso
      cargarAsignaciones();
    } catch (err) {
      console.error("Error al aceptar el caso:", err);
      setError(`Error al aceptar el caso ${idCaso}. Por favor, intente de nuevo.`);
    } finally {
      setProcesandoId(null);
    }
  };

  const handleRechazar = async (idCaso) => {
    setProcesandoId(idCaso);
    try {
      await apiRechazarAsignacion(idCaso);
      // Recargamos la lista para que el caso desaparezca o cambie de estado
      cargarAsignaciones();
    } catch (err) {
      console.error("Error al rechazar el caso:", err);
      setError(`Error al rechazar el caso ${idCaso}. Por favor, intente de nuevo.`);
    } finally {
      setProcesandoId(null);
    }
  };


  if (estaCargando && listaDeCasos.length === 0) {
    return <div className="dashboard-estudiante-contenedor"><p>Cargando sus asignaciones...</p></div>;
  }
  if (error) {
    return <div className="dashboard-estudiante-contenedor error"><p>{error}</p></div>;
  }

  return (
    <div className="dashboard-estudiante-contenedor">
      <div className="dashboard-cabecera">
        <h1>Panel de Casos</h1>
      </div>
      
      {listaDeCasos.length === 0 ? (
        <p>Actualmente no tiene casos asignados.</p>
      ) : (
        <table className="tabla-casos-estudiante">
          <thead>
            <tr>
              <th>ID Caso</th>
              <th>Fecha de Creación</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {listaDeCasos.map((caso) => (
              <tr key={caso.id}>
                <td>{caso.id}</td>
                <td>{new Date(caso.fecha_creacion).toLocaleDateString('es-ES')}</td>
                <td>
                  <span className={`estado-caso estado-${caso.estado.replace('_', '-')}`}>{caso.estado.replace('_', ' ')}</span>
                </td>
                <td>
                  {/* --- Lógica condicional de acciones --- */}
                  <div className="acciones-contenedor">
                    {procesandoId === caso.id ? (
                      <span>Procesando...</span>
                    ) : (
                      <>
                        {caso.estado === 'pendiente_aceptacion' && (
                          <>
                            <button onClick={() => handleAceptar(caso.id)} className="boton-accion aceptar">
                              Aceptar
                            </button>
                            <button onClick={() => handleRechazar(caso.id)} className="boton-accion rechazar">
                              Rechazar
                            </button>
                          </>
                        )}
                        
                        {caso.estado === 'asignado' && (
                          <button onClick={() => onVerExpediente(caso.id)} className="boton-accion ver">
                            Ver Expediente
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