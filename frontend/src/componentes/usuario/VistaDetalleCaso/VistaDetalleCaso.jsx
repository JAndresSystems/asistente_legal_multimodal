import React, { useState, useEffect, useCallback, useRef } from 'react';
import { obtenerDetallesCaso, apiDescargarReportePDF, apiCrearNotaUsuario, enviarMensajeOrientacion } from '../../../servicios/api';
import FormularioSubirEvidencia from '../FormularioSubirEvidencia/FormularioSubirEvidencia';
import VisorReporte from '../VisorReporte/VisorReporte';
import './VistaDetalleCaso.css';

function VistaDetalleCaso({ casoId, onVolverAlDashboard }) {
  const [caso, setCaso] = useState(null);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);
  const [descargando, setDescargando] = useState(false);
  
  // Notas
  const [nuevaNota, setNuevaNota] = useState('');
  const [enviandoNota, setEnviandoNota] = useState(false);
  const [errorNota, setErrorNota] = useState('');

  // Chat Flotante
  const [chatAbierto, setChatAbierto] = useState(false);
  const [preguntaOrientacion, setPreguntaOrientacion] = useState('');
  const [cargandoOrientacion, setCargandoOrientacion] = useState(false);
  const [historialVisual, setHistorialVisual] = useState([]); 
  const finalChatRef = useRef(null);

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
      
      if (detallesDelCaso.historial_conversacion) {
          setHistorialVisual(detallesDelCaso.historial_conversacion);
      }
      
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

  useEffect(() => {
    if (chatAbierto && finalChatRef.current) {
        finalChatRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [historialVisual, chatAbierto, cargandoOrientacion]);

  const handleCrearNota = async (e) => {
    e.preventDefault();
    if (!nuevaNota.trim()) return;
    setEnviandoNota(true);
    try {
      await apiCrearNotaUsuario(casoId, nuevaNota);
      setNuevaNota('');
      await cargarDatosDelCaso();
    } catch (err) {
      setErrorNota(err.message);
    } finally {
      setEnviandoNota(false);
    }
  };

  const handleChatOrientacion = async (e) => {
    e.preventDefault();
    if (!preguntaOrientacion.trim()) return;

    const textoPregunta = preguntaOrientacion;
    setPreguntaOrientacion(''); 
    setCargandoOrientacion(true);

    const nuevosMensajes = [
        ...historialVisual, 
        { autor: 'usuario', texto: textoPregunta, tipo: 'chat_orientacion' }
    ];
    setHistorialVisual(nuevosMensajes);

    try {
      const respuesta = await enviarMensajeOrientacion(casoId, textoPregunta);
      setHistorialVisual(prev => [
          ...prev, 
          { autor: 'agente_orientacion', texto: respuesta.respuesta_texto, tipo: 'chat_orientacion' }
      ]);
    } catch (err) {
      console.log("Error al enviar mensaje de orientación:", err);
      setHistorialVisual(prev => [
          ...prev, 
          { autor: 'sistema', texto: 'Error de conexión.', tipo: 'error' }
      ]);
    } finally {
      setCargandoOrientacion(false);
    }
  };

  const manejarDescargaReporte = async () => {
    setDescargando(true);
    const resultado = await apiDescargarReportePDF(casoId);
    if (!resultado.exito) alert(resultado.mensaje || "Error al descargar el PDF.");
    setDescargando(false);
  };

  const manejarSubidaCompletada = () => {
    cargarDatosDelCaso();
  };

  const obtenerEstiloEstado = (estado) => {
    if (!estado) return {};
    const estadoNormalizado = estado.toLowerCase().replace('_', ' ');
    switch (estadoNormalizado) {
      case 'en revision': return { backgroundColor: '#17a2b8', color: 'white' };
      case 'pendiente aceptacion': return { backgroundColor: '#ffc107', color: 'black' };
      case 'asignado': return { backgroundColor: '#28a745', color: 'white' };
      case 'rechazado': return { backgroundColor: '#dc3545', color: 'white' };
      default: return { backgroundColor: '#e2e6ea', color: '#333' };
    }
  };
  
  if (estaCargando) return <div className="detalle-contenedor"><p>Cargando...</p></div>;
  if (error) return <div className="detalle-contenedor"><p className="mensaje-error">{error}</p><button onClick={onVolverAlDashboard}>Volver</button></div>;
  if (!caso) return null;
  
  //const URL_BASE_BACKEND = "http://127.0.0.1:8000";<-local
  // Usamos la variable de entorno que definimos en render.yaml
const URL_BASE_BACKEND = import.meta.env.VITE_URL_BASE_BACKEND;

  // --- INICIO DE LA CORRECCIÓN DE LA LÍNEA DE TIEMPO (USUARIO) ---
  
  // 1. Documentos
  const eventosDocumento = (caso.evidencias || []).map(ev => ({ 
      tipo: 'documento', 
      fechaSort: new Date(ev.fecha_subida || ev.fecha_creacion || 0),
      ...ev 
  }));

  // 2. Notas (CON FILTRO)
 const eventosNota = (caso.notas || [])
    .filter(nota => nota.id_evidencia === null) // <--- Oculta notas que pertenecen a un documento
    .map(nota => ({ 
        tipo: 'nota', 
        fechaSort: new Date(nota.fecha_creacion || 0),
        ...nota 
    }));

  // 3. Unificar y Ordenar
 const lineaDeTiempo = [...eventosDocumento, ...eventosNota].sort((a, b) => {
    return a.fechaSort - b.fechaSort; 
  });
  // --- FIN DE LA CORRECCIÓN ---

  return (
    <div className="detalle-contenedor">
      <button onClick={onVolverAlDashboard} className="boton-volver">&larr; Volver a Mis Casos</button>
      <h1>Detalles del Caso #{caso.id}</h1>

      <div className="seccion-acciones">
        <button onClick={manejarDescargaReporte} className="boton-descargar-pdf" disabled={descargando}>
          {descargando ? 'Generando...' : 'Descargar Reporte en PDF'}
        </button>
      </div>

      <div className="seccion-detalle">
        <h2>Resumen del Caso</h2>
        <div className="info-resumen">
          <div className="info-item">
            <strong>Estado Actual:</strong>
            <span className={`estado-caso`} style={obtenerEstiloEstado(caso.estado)}>
                {caso.estado.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </span>
          </div>
          <div className="info-item"><strong>Área Asignada:</strong><span>{caso.area_asignada || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Estudiante:</strong><span>{caso.estudiante_asignado || 'Pendiente'}</span></div>
          <div className="info-item"><strong>Supervisor:</strong><span>{caso.asesor_asignado || 'Pendiente'}</span></div>
        </div>
      </div>

      <div className="seccion-detalle">
        <h2>Descripción de los Hechos</h2>
        <p className="descripcion-hechos">{caso.descripcion_hechos}</p>
      </div>
      
      <div className="seccion-detalle">
        <h2>Línea de Tiempo y Comunicaciones</h2>
        <div className="linea-de-tiempo-usuario">
          {lineaDeTiempo.length > 0 ? (
            lineaDeTiempo.map((item, index) => (
              <div key={`${item.tipo}-${item.id || index}`} className={`item-timeline-usuario item-autor-${item.rol_autor || 'documento'}`}>
                
                {/* --- RENDERIZADO DE NOTA SUELTA --- */}
                {item.tipo === 'nota' && (
                  <>
                    <p className="autor-timeline"><strong>{item.autor_nombre || item.rol_autor}:</strong></p>
                    <p className="contenido-timeline">{item.contenido}</p>
                    <p className="fecha-timeline">{item.fechaSort.toLocaleString('es-CO')}</p>
                  </>
                )}

                {/* --- RENDERIZADO DE DOCUMENTO (CON HILO) --- */}
                {item.tipo === 'documento' && (
                  <div className="tarjeta-documento-usuario">
                    <p className="autor-timeline"><strong>Documento Subido:</strong> {item.autor_nombre}</p>
                    <div className="info-doc-wrapper">
                        <span style={{fontSize:'1.5rem', marginRight:'10px'}}>📄</span>
                        <div>
                             {/* Lógica inteligente: Si ya trae http, úsala tal cual. Si no, agrégale la base. */}
                            <a 
                                href={item.ruta_archivo.startsWith('http') ? item.ruta_archivo : `${URL_BASE_BACKEND}${item.ruta_archivo}`} 
                                target="_blank" 
                                rel="noopener noreferrer" 
                                className="enlace-evidencia"
                            >
                                {item.nombre_archivo}
                            </a>
                            <p className="fecha-timeline">{item.fechaSort.toLocaleString('es-CO')}</p>
                        </div>
                    </div>

                    {/* HILO DE COMENTARIOS ASOCIADOS A ESTE DOCUMENTO */}
                    {caso.notas.filter(n => n.id_evidencia === item.id).length > 0 && (
                        <div className="hilo-comentarios-doc">
                            <hr style={{margin:'5px 0', border:'0', borderTop:'1px solid #eee'}}/>
                            {caso.notas.filter(n => n.id_evidencia === item.id).map(subNota => (
                                <div key={subNota.id} className="sub-comentario">
                                    <strong>{subNota.autor_nombre}: </strong> 
                                    <span>{subNota.contenido}</span>
                                </div>
                            ))}
                        </div>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : <p>Aún no hay actividad.</p>}
        </div>
        
        <form onSubmit={handleCrearNota} className="formulario-crear-nota-usuario">
          <h4>Enviar Mensaje al Equipo</h4>
          <textarea 
            value={nuevaNota} 
            onChange={(e) => setNuevaNota(e.target.value)} 
            placeholder="Escriba su mensaje..." 
            disabled={enviandoNota} 
            rows={3} 
          />
          <button type="submit" disabled={enviandoNota}>
            {enviandoNota ? 'Enviando...' : 'Enviar Mensaje'}
          </button>
          
          {errorNota && <p className="mensaje-error" style={{color: 'red', marginTop: '5px'}}>{errorNota}</p>}
          
        </form>
      </div>

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

      {/* WIDGET FLOTANTE */}
      <div className="widget-orientacion-contenedor">
        {!chatAbierto && (
            <button className="boton-flotante-abrir" onClick={() => setChatAbierto(true)}>
                💬 Asistente Virtual
            </button>
        )}

        {chatAbierto && (
            <div className="ventana-chat-flotante">
                <div className="chat-header">
                    <h3>Asistente del Caso #{caso.id}</h3>
                    <button className="btn-cerrar-chat" onClick={() => setChatAbierto(false)}>×</button>
                </div>
                
                <div className="chat-body">
                    {historialVisual
                        .filter(msg => msg.tipo === 'chat_orientacion' || msg.autor === 'agente_orientacion')
                        .map((msg, i) => (
                            <div key={i} className={`burbuja ${msg.autor === 'usuario' ? 'propio' : 'agente'}`}>
                                {msg.texto}
                            </div>
                        ))
                    }
                    {historialVisual.filter(m => m.tipo === 'chat_orientacion').length === 0 && (
                        <p style={{textAlign: 'center', color: '#888', marginTop: '20px'}}>
                            Hola, soy tu asistente de orientación. ¿En qué puedo ayudarte sobre tu caso?
                        </p>
                    )}
                    {cargandoOrientacion && (
                        <div className="typing-indicator">Escribiendo...</div>
                    )}
                    <div ref={finalChatRef} />
                </div>

                <form className="chat-footer" onSubmit={handleChatOrientacion}>
                    <input 
                        type="text" 
                        value={preguntaOrientacion}
                        onChange={(e) => setPreguntaOrientacion(e.target.value)}
                        placeholder="Escribe tu duda..."
                        disabled={cargandoOrientacion}
                    />
                    <button type="submit" disabled={cargandoOrientacion}>➤</button>
                </form>
            </div>
        )}
      </div>

    </div>
  );
}

export default VistaDetalleCaso;