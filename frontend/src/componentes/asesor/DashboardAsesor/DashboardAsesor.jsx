//C:\react\asistente_legal_multimodal\frontend\src\componentes\asesor\DashboardAsesor\DashboardAsesor.jsx
import React, { useState, useEffect, useCallback } from 'react';
// 1. Importamos la nueva funcion de la API
import { apiObtenerDashboardAsesor } from '../../../servicios/api';
import { useAuth } from '../../../contextos/ContextoAutenticacion';
import styles from './DashboardAsesor.module.css';

const DashboardAsesor = ({ onVerExpediente }) => {
   const { usuario } = useAuth();
  const [casosSupervisados, setCasosSupervisados] = useState([]);
  // 2. Añadimos un nuevo estado para las métricas
  const [metricas, setMetricas] = useState([]);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);

  // 3. Actualizamos la función de carga de datos
  const cargarDashboardData = useCallback(async () => {
    try {
      setEstaCargando(true);
      setError(null);
      // Llamamos a la nueva función que devuelve el objeto completo
      const data = await apiObtenerDashboardAsesor();
      setCasosSupervisados(data.casos_supervisados);
      setMetricas(data.metricas_carga_trabajo);
    } catch (err) {
      setError(err.message || "Ocurrió un error al cargar los datos del dashboard.");
      console.error(err);
    } finally {
      setEstaCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarDashboardData();
  }, [cargarDashboardData]);

  if (estaCargando) {
    return <div className={styles.contenedorCentrado}>Cargando datos del dashboard...</div>;
  }

  if (error) {
    return <div className={`${styles.contenedorCentrado} ${styles.error}`}>{error}</div>;
  }

  return (
    <div className={styles.dashboardContenedor}>
       <div className={styles.saludoContenedor}>
        <h2 className={styles.titulo}>Bienvenido de nuevo, {usuario?.nombre_completo}</h2>
        <p className={styles.subtitulo}>Este es su panel de supervisión de casos.</p>
      </div>
      <h2 className={styles.titulo}>Casos Asignados al Asesor</h2>
      
      {/* 4. Añadimos el nuevo panel de métricas */}
      <div className={styles.panelMetricas}>
        <h3>Estudiantes de Trabajo</h3>
        {metricas.length > 0 ? (
          <ul className={styles.listaMetricas}>
            {metricas.map((metrica, index) => (
              <li key={index} className={styles.itemMetrica}>
                <span className={styles.nombreEstudiante}>{metrica.nombre_estudiante}</span>
                <span className={styles.cargaTrabajo}>{metrica.casos_asignados} caso(s)</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No hay estudiantes con casos activos bajo su supervisión.</p>
        )}
      </div>

      <div className={styles.panelCasos}>
        <h3>Tus casos asignados</h3>
        {casosSupervisados.length === 0 ? (
          <p>No hay casos asignados a sus estudiantes en este momento.</p>
        ) : (
          <table className={styles.tablaCasos}>
            <thead>
              <tr>
                <th>ID Caso</th>
                <th>Estudiante a Cargo</th>
                <th>Estado del Caso</th>
                <th>Fecha de Creación</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {casosSupervisados.map((caso) => (
                <tr key={caso.id}>
                  <td>{caso.id}</td>
                  <td>{caso.nombre_estudiante}</td>
                  <td>{caso.estado}</td>
                  <td>{new Date(caso.fecha_creacion).toLocaleDateString()}</td>
                  <td>
                    <button 
                      className={styles.botonAccion}
                      onClick={() => onVerExpediente(caso.id)}
                    >
                      Ver Expediente
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