// frontend/src/componentes/estudiante/DashboardEstudiante/DashboardEstudiante.jsx

import React, { useState, useEffect } from 'react';
import { apiObtenerMisAsignaciones } from '../../../servicios/api';
import './DashboardEstudiante.css';

function DashboardEstudiante({ onVerExpediente }) { // Aceptamos una prop para el futuro
  const [listaDeCasos, setListaDeCasos] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cargarAsignaciones = async () => {
      try {
        const casosAsignados = await apiObtenerMisAsignaciones();
        setListaDeCasos(casosAsignados);
      } catch (err) {
        console.error("Error al cargar las asignaciones:", err);
        setError("No se pudieron cargar sus casos asignados. Verifique que su perfil de estudiante esté activo.");
      } finally {
        setEstaCargando(false);
      }
    };
    cargarAsignaciones();
  }, []);

  if (estaCargando) {
    return <div className="dashboard-estudiante-contenedor"><p>Cargando sus asignaciones...</p></div>;
  }
  if (error) {
    return <div className="dashboard-estudiante-contenedor error"><p>{error}</p></div>;
  }

  return (
    <div className="dashboard-estudiante-contenedor">
      <div className="dashboard-cabecera">
        <h1>Panel de Casos Asignados</h1>
        {/* Espacio para futuros botones, como filtros o busquedas */}
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
                  <span className={`estado-caso ${caso.estado}`}>{caso.estado.replace('_', ' ')}</span>
                </td>
                <td>
                  <button onClick={() => onVerExpediente(caso.id)} className="boton-accion">
                    Ver Expediente
                  </button>
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