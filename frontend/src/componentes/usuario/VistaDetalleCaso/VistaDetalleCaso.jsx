// frontend/src/componentes/usuario/VistaDetalleCaso/VistaDetalleCaso.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  obtenerDetallesCaso, 
  apiDescargarReportePDF, 
  apiCrearNotaUsuario,
  analizarCaso, // Importamos la función que inicia el análisis
  apiConsultarEstadoAnalisis // Importamos la nueva función
} from '../../../servicios/api';
import FormularioSubirEvidencia from '../FormularioSubirEvidencia/FormularioSubirEvidencia';
import VisorReporte from '../VisorReporte/VisorReporte';
import './VistaDetalleCaso.css';

function VistaDetalleCaso({ casoId, onVolverAlDashboard }) {
  const [caso, setCaso] = useState(null);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);
  const [descargando, setDescargando] = useState(false);
  const [nuevaNota, setNuevaNota] = useState('');
  const [enviandoNota, setEnviandoNota] = useState(false);
  const [errorNota, setErrorNota] = useState('');

  // --- INICIO DE LA MODIFICACIÓN ---
  const [isAnalizando, setIsAnalizando] = useState(false); // Nuevo estado para mostrar spinner
  const [analisisError, setAnalisisError] = useState(null);
  // const [tareaId, setTareaId] = useState(null); // REMOVIDO: No se usaba
  const analisisIntervalRef = useRef(null); // Referencia para el intervalo
  // --- FIN DE LA MODIFICACIÓN ---

  const cargarDatosDelCaso = useCallback(async () => {
    if (!casoId) {
      setError("No se ha proporcionado un ID de caso.");
      setEstaCargando(false);
      return;
    }
    try {
      setEstaCargando(true);
      const detallesDelCaso = await obtenerDetallesCaso(casoId);
      setCaso(detallesDelCaso);
      setError(null);
    } catch (err) {
      setError("No se pudieron cargar los detalles del caso. " + err.message);
    } finally {
      setEstaCargando(false);
    }
  }, [casoId]);

  useEffect(() => {
    cargarDatosDelCaso();
  }, [cargarDatosDelCaso]);

  // --- INICIO DE LA MODIFICACIÓN ---
  // Función para iniciar el análisis
  const handleIniciarAnalisis = async () => {
    setIsAnalizando(true);
    setAnalisisError(null);
    try {
      // Paso 1: Iniciar la tarea de análisis
      const resultadoInicio = await analizarCaso(casoId); // Llama a la nueva función
      console.log("API: Análisis iniciado. ID de tarea:", resultadoInicio.id_tarea);
      // setTareaId(resultadoInicio.id_tarea); // REMOVIDO: No se usaba

      // Paso 2: Iniciar polling para verificar el estado
      // Declaramos 'idTareaActual' en el scope de esta función para usarlo en el intervalo
      const idTareaActual = resultadoInicio.id_tarea;
      analisisIntervalRef.current = setInterval(async () => {
        try {
          const estado = await apiConsultarEstadoAnalisis(casoId, idTareaActual); // Usamos 'idTareaActual'
          console.log("API: Estado actual del análisis:", estado.estado);

          if (estado.estado === 'completado') {
            // El análisis terminó. Actualiza el estado del caso.
            setCaso(estado.caso); // Asume que el backend devuelve el caso actualizado
            setIsAnalizando(false);
            setAnalisisError(null); // Limpiar error si hubo uno previamente
            clearInterval(analisisIntervalRef.current);
          } else if (estado.estado === 'error') {
            // Hubo un error en la tarea.
            setAnalisisError(estado.mensaje || "Ocurrió un error desconocido en la tarea de análisis.");
            setIsAnalizando(false);
            clearInterval(analisisIntervalRef.current);
          }
          // Si el estado es 'en_progreso', el intervalo seguirá ejecutándose.
        } catch (error) {
          console.error("Error al consultar el estado del análisis:", error);
          setAnalisisError("Ocurrió un error al consultar el estado del análisis.");
          setIsAnalizando(false);
          clearInterval(analisisIntervalRef.current);
        }
      }, 5000); // Polling cada 5 segundos

    } catch (error) {
      console.error("Error al iniciar el análisis:", error);
      setAnalisisError(error.message || "Ocurrió un error al iniciar el análisis.");
      setIsAnalizando(false);
    }
  };

  // Limpiar el intervalo cuando el componente se desmonte o cuando se detenga
  useEffect(() => {
    return () => {
      if (analisisIntervalRef.current) {
        clearInterval(analisisIntervalRef.current);
      }
    };
  }, []);
  // --- FIN DE LA MODIFICACIÓN ---

  const handleCrearNota = async (e) => {
    e.preventDefault();
    if (!nuevaNota.trim()) {
      setErrorNota("El mensaje no puede estar vacío.");
      return;
    }
    setEnviandoNota(true);
    setErrorNota('');
    try {
      await apiCrearNotaUsuario(casoId, nuevaNota);
      setNuevaNota('');
      await cargarDatosDelCaso();
    } catch (err) {
      setErrorNota(err.message || 'Ocurrió un error al enviar el mensaje.');
    } finally {
      setEnviandoNota(false);
    }
  };

  const manejarDescargaReporte = async () => {
    setDescargando(true);
    const resultado = await apiDescargarReportePDF(casoId);
    if (!resultado.exito) {
      alert(resultado.mensaje || "Error al descargar el PDF.");
    }
    setDescargando(false);
  };

  const manejarSubidaCompletada = () => {
    console.log("Evidencia subida. Refrescando datos del caso...");
    cargarDatosDelCaso();
  };
  
  if (estaCargando) return <div className="detalle-contenedor"><p>Cargando información del caso...</p></div>;
  if (error) return <div className="detalle-contenedor"><p className="mensaje-error">{error}</p><button onClick={onVolverAlDashboard}>&larr; Volver</button></div>;
  if (!caso) return null;
  
  const URL_BASE_BACKEND = "http://127.0.0.1:8000";

  // --- INICIO DE LA MODIFICACIÓN ---
  // Lógica para unificar notas y evidencias en una sola línea de tiempo
  const eventosDocumento = (caso.evidencias || []).map(ev => ({ tipo: 'documento', ...ev }));
  const eventosNota = (caso.notas || []).map(nota => ({ tipo: 'nota', ...nota }));
  const lineaDeTiempo = [...eventosDocumento, ...eventosNota].sort((a, b) => {
    // Las notas tienen fecha de creación, los documentos no. Priorizamos las notas.
    const fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : new Date(0);
    const fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : new Date(0);
    return fechaB - fechaA; // Orden descendente
  });
  // --- FIN DE LA MODIFICACIÓN ---

  return (
    <div className="detalle-contenedor">
      <button onClick={onVolverAlDashboard} className="boton-volver">&larr; Volver a Mis Casos</button>
      <h1>Detalles del Caso #{caso.id}</h1>

      <div className="seccion-acciones">
        <button onClick={manejarDescargaReporte} className="boton-descargar-pdf" disabled={descargando}>
          {descargando ? 'Generando...' : 'Descargar Reporte en PDF'}
        </button>
        {/* --- INICIO DE LA MODIFICACIÓN --- */}
        <button
          onClick={handleIniciarAnalisis}
          disabled={isAnalizando || caso.estado !== 'en_revision'} // Deshabilitar si ya se está analizando o si el estado no es 'en_revision'
          className="boton-analizar"
        >
          {isAnalizando ? 'Analizando...' : 'Iniciar Análisis de IA'}
        </button>
        {/* --- FIN DE LA MODIFICACIÓN --- */}
      </div>

      {/* --- INICIO DE LA MODIFICACIÓN --- */}
      {isAnalizando && <p className="mensaje-proceso">Por favor, espere mientras se procesa su caso...</p>}
      {analisisError && <p className="mensaje-error">{analisisError}</p>}
      {/* --- FIN DE LA MODIFICACIÓN --- */}

      <div className="seccion-detalle">
        <h2>Resumen del Caso</h2>
        <div className="info-resumen">
          <div className="info-item"><strong>Estado Actual:</strong><span className={`estado-caso ${caso.estado}`}>{caso.estado.replace('_', ' ')}</span></div>
          <div className="info-item"><strong>Área Asignada:</strong><span>{caso.area_asignada || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Estudiante a Cargo:</strong><span>{caso.estudiante_asignado || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Asesor Supervisor:</strong><span>{caso.asesor_asignado || 'Pendiente'}</span></div>
        </div>
      </div>

      <div className="seccion-detalle">
        <h2>Descripción de los Hechos</h2>
        <p className="descripcion-hechos">{caso.descripcion_hechos}</p>
      </div>
      
      {/* --- INICIO DE LA MODIFICACIÓN --- */}
      <div className="seccion-detalle">
        <h2>Línea de Tiempo y Comunicaciones</h2>
        <div className="linea-de-tiempo-usuario">
          {lineaDeTiempo.length > 0 ? (
            lineaDeTiempo.map((item, index) => (
              <div key={`${item.tipo}-${item.id || index}`} className={`item-timeline-usuario item-autor-${item.rol_autor || 'documento'}`}>
                {item.tipo === 'nota' && (
                  <>
                    <p className="autor-timeline"><strong>{item.autor_nombre || item.rol_autor}:</strong></p>
                    <p className="contenido-timeline">{item.contenido}</p>
                    <p className="fecha-timeline">{new Date(item.fecha_creacion).toLocaleString('es-CO')}</p>
                  </>
                )}
                {item.tipo === 'documento' && (
                  <>
                    <p className="autor-timeline"><strong>Documento subido por {item.autor_nombre || 'No disponible'}:</strong></p>
                    <a href={`${URL_BASE_BACKEND}${item.ruta_archivo}`} target="_blank" rel="noopener noreferrer" className="enlace-evidencia">
                      {item.nombre_archivo}
                    </a>
                  </>
                )}
              </div>
            ))
          ) : <p>Aún no hay mensajes ni documentos en este caso.</p>}
        </div>
        
        <form onSubmit={handleCrearNota} className="formulario-crear-nota-usuario">
          <h4>Enviar un Mensaje al Equipo</h4>
          <textarea value={nuevaNota} onChange={(e) => setNuevaNota(e.target.value)} placeholder="Escriba su mensaje aquí..." disabled={enviandoNota} rows={4} />
          <button type="submit" disabled={enviandoNota}>{enviandoNota ? 'Enviando...' : 'Enviar Mensaje'}</button>
          {errorNota && <p className="mensaje-error">{errorNota}</p>}
        </form>
      </div>
      {/* --- FIN DE LA MODIFICACIÓN --- */}

      {caso.reporte_consolidado && (
        <div className="seccion-detalle">
          <h2>Informe Final de Agentes</h2>
          <VisorReporte jsonString={caso.reporte_consolidado} />
        </div>
      )}

      <hr className="separador-seccion" />
      <div className="seccion-detalle">
        <h2>Añadir Nueva Evidencia</h2>
        <FormularioSubirEvidencia casoId={caso.id} onSubidaCompletada={manejarSubidaCompletada} />
      </div>
    </div>
  );
}

export default VistaDetalleCaso;