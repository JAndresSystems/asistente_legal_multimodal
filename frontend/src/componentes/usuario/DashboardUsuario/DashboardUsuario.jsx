// frontend/src/componentes/usuario/DashboardUsuario/DashboardUsuario.jsx

import React, { useState, useEffect } from 'react';
import { apiObtenerMisCasos } from '../../../servicios/api';
import { useAuth } from '../../../contextos/ContextoAutenticacion';
import './DashboardUsuario.css';

// (NUEVO) Importamos los componentes del widget
import WidgetChat from './WidgetChat';
import WidgetToggler from './WidgetToggler';

// Aceptamos las props que ya teníamos: onIniciarNuevoCaso y onVerDetalles
function DashboardUsuario({ onIniciarNuevoCaso, onVerDetalles }) {
  const { usuario } = useAuth();
  const [listaDeCasos, setListaDeCasos] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  // (NUEVO) Estado para controlar la visibilidad del widget de chat
  const [isWidgetOpen, setIsWidgetOpen] = useState(false);

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
    return <div className="dashboard-contenedor"><p>Cargando su información...</p></div>;
  }
  if (error) {
    return <div className="dashboard-contenedor error"><p>{error}</p></div>;
  }

  // (NUEVO) Función para abrir/cerrar el widget
  const toggleWidget = () => setIsWidgetOpen(!isWidgetOpen);

  return (
    // (MODIFICACIÓN) Volvemos a un contenedor simple de una sola columna.
    <div className="dashboard-contenedor">

      <div className="dashboard-saludo">
        <h2>Bienvenido de nuevo, {usuario?.nombre}</h2>
        <p>Aquí puede ver el estado de sus casos o registrar uno nuevo.</p>
      </div>
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
          {/* ... El contenido de la tabla no cambia ... */}
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
                  <button onClick={() => onVerDetalles(caso.id)} className="boton-accion">
                    Ver Detalles
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* --- (NUEVA LÓGICA DE RENDERIZADO DEL WIDGET) --- */}
      {isWidgetOpen ? (
        <WidgetChat onToggle={toggleWidget} onIniciarNuevoCaso={onIniciarNuevoCaso} />
      ) : (
        <WidgetToggler onToggle={toggleWidget} />
      )}
    </div>
  );
}

export default DashboardUsuario;