// frontend/src/componentes/DashboardUsuario/DashboardUsuario.jsx

import React, { useState, useEffect } from 'react';
import { apiObtenerMisCasos } from '../../../servicios/api';
import './DashboardUsuario.css';

// 1. (MODIFICACIÓN) Aceptamos una nueva prop: onVerDetalles
function DashboardUsuario({ onIniciarNuevoCaso, onVerDetalles }) {
  const [listaDeCasos, setListaDeCasos] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cargarCasosDelUsuario = async () => {
      try {
        const casosObtenidos = await apiObtenerMisCasos();
        setListaDeCasos(casosObtenidos);
      } catch (error) {
        console.error("Error al cargar los casos del usuario:", error);
        setError("No se pudieron cargar sus casos. Por favor, intente de nuevo más tarde.");
      } finally {
        setEstaCargando(false);
      }
    };
    cargarCasosDelUsuario();
  }, []);

  if (estaCargando) {
    return <div className="dashboard-contenedor"><p>Cargando sus casos...</p></div>;
  }
  if (error) {
    return <div className="dashboard-contenedor error"><p>{error}</p></div>;
  }

  return (
    <div className="dashboard-contenedor">
      <div className="dashboard-cabecera">
        <h1>Mis Casos Registrados</h1>
        <button onClick={onIniciarNuevoCaso} className="boton-nuevo-caso">
          Registrar Nuevo Caso
        </button>
      </div>
      
      {listaDeCasos.length === 0 ? (
        <p>Aún no tiene casos registrados en el sistema.</p>
      ) : (
        <table className="tabla-casos">
          <thead>
            <tr>
              <th>ID del Caso</th>
              <th>Fecha de Creación</th>
              <th>Estado Actual</th>
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
                  {/* 2. (MODIFICACIÓN) El boton ahora llama a la funcion de la prop con el id del caso */}
                  <button onClick={() => onVerDetalles(caso.id)} className="boton-accion">
                    Ver Detalles
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

export default DashboardUsuario;