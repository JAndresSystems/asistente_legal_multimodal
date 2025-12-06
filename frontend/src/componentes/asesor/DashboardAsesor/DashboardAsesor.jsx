import React, { useState, useEffect, useCallback } from 'react';
import { apiObtenerDashboardAsesor } from '../../../servicios/api';
import { useAuth } from '../../../contextos/ContextoAutenticacion';
import styles from './DashboardAsesor.module.css';

const DashboardAsesor = ({ onVerExpediente }) => {
  const { usuario } = useAuth();
  const [casosSupervisados, setCasosSupervisados] = useState([]);
  const [metricas, setMetricas] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  // --- ESTADO PARA FILTROS ---
  const [filtroActual, setFiltroActual] = useState('todos'); // 'todos', 'alertas', 'pendientes'

  const cargarDashboardData = useCallback(async () => {
    try {
      setEstaCargando(true);
      setError(null);
      const data = await apiObtenerDashboardAsesor();
      setCasosSupervisados(data.casos_supervisados);
      setMetricas(data.metricas_carga_trabajo);
    } catch (err) {
      setError(err.message || "Error cargando dashboard.");
    } finally {
      setEstaCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarDashboardData();
  }, [cargarDashboardData]);

  // --- LÓGICA DE FILTRADO ---
  const obtenerCasosFiltrados = () => {
    if (filtroActual === 'alertas') {
      return casosSupervisados.filter(c => c.tiene_alerta);
    }
    if (filtroActual === 'pendientes') {
      return casosSupervisados.filter(c => c.estado === 'pendiente_aceptacion' || c.estado === 'en_revision');
    }
    return casosSupervisados;
  };

  const casosVisibles = obtenerCasosFiltrados();

  if (estaCargando) return <div className={styles.contenedorCentrado}>Cargando panel de control...</div>;
  if (error) return <div className={`${styles.contenedorCentrado} ${styles.error}`}>{error}</div>;

  return (
    <div className={styles.dashboardContenedor}>
       <div className={styles.saludoContenedor}>
        <h2 className={styles.titulo}>Bienvenido, Dr. {usuario?.nombre?.split(' ')[0]}</h2>
        <p className={styles.subtitulo}>Panel de Supervisión y Control.</p>
      </div>

      {/* --- PANEL DE MÉTRICAS --- */}
      <div className={styles.panelMetricas}>
        <h3>Carga de Trabajo del Equipo</h3>
        {metricas.length > 0 ? (
          <ul className={styles.listaMetricas}>
            {metricas.map((metrica, i) => (
              <li key={i} className={styles.itemMetrica}>
                <span className={styles.nombreEstudiante}>{metrica.nombre_estudiante}</span>
                <div className={styles.barraProgresoFondo}>
                    <div 
                        className={styles.barraProgresoRelleno} 
                        style={{width: `${Math.min(metrica.casos_asignados * 10, 100)}%`}}
                    ></div>
                </div>
                <span className={styles.cargaTrabajo}>{metrica.casos_asignados} activos</span>
              </li>
            ))}
          </ul>
        ) : <p>Sin métricas disponibles.</p>}
      </div>

      <div className={styles.panelCasos}>
        <div className={styles.cabeceraTabla}>
            <h3>Expedientes Supervisados</h3>
            
            {/* --- BOTONES DE FILTRO --- */}
            <div className={styles.filtros}>
                <button 
                    className={`${styles.btnFiltro} ${filtroActual === 'todos' ? styles.activo : ''}`}
                    onClick={() => setFiltroActual('todos')}
                >
                    Todos ({casosSupervisados.length})
                </button>
                <button 
                    className={`${styles.btnFiltro} ${filtroActual === 'pendientes' ? styles.activo : ''}`}
                    onClick={() => setFiltroActual('pendientes')}
                >
                    Pendientes ({casosSupervisados.filter(c => c.estado === 'pendiente_aceptacion').length})
                </button>
                <button 
                    className={`${styles.btnFiltro} ${filtroActual === 'alertas' ? styles.activo : ''} ${styles.alerta}`}
                    onClick={() => setFiltroActual('alertas')}
                >
                    🚨 Con Alertas ({casosSupervisados.filter(c => c.tiene_alerta).length})
                </button>
            </div>
        </div>

        {casosVisibles.length === 0 ? (
          <div className={styles.vacio}>No hay casos que coincidan con este filtro.</div>
        ) : (
          <table className={styles.tablaCasos}>
            <thead>
              <tr>
                <th>Estado</th>
                <th>ID</th>
                <th>Estudiante</th>
                <th>Etapa</th>
                <th>Fecha</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {casosVisibles.map((caso) => (
                <tr key={caso.id} className={caso.tiene_alerta ? styles.filaAlerta : ''}>
                  <td className={styles.celdaIcono}>
                    {caso.tiene_alerta && <span title="¡Atención Requerida!" className={styles.iconoAlerta}>🚨</span>}
                  </td>
                  <td>#{caso.id}</td>
                  <td>{caso.nombre_estudiante}</td>
                  <td>
                    <span className={`${styles.etiquetaEstado} ${styles[caso.estado]}`}>
                        {caso.estado.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{new Date(caso.fecha_creacion).toLocaleDateString()}</td>
                  <td>
                    <button 
                      className={styles.botonAccion}
                      onClick={() => onVerExpediente(caso.id)}
                    >
                      Revisar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default DashboardAsesor;