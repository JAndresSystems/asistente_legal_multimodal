//C:\react\asistente_legal_multimodal\frontend\src\componentes\asesor\VistaExpedienteAsesor\VistaExpedienteAsesor.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { 
  apiObtenerDetalleExpedienteAsesor, 
  apiCrearNotaAsesor, 
  apiFinalizarCaso,
  //apiObtenerEstudiantes,
  apiReasignarCaso,
  apiAprobarDocumento,         // 1. Importamos las nuevas APIs
  apiSolicitarCambiosDocumento ,
   apiDescargarReporteExpedientePDF
} from '../../../servicios/api';
import styles from './VistaExpedienteAsesor.module.css';
import AsistenteJuridico from './AsistenteJuridico/AsistenteJuridico';
// 1. Importamos el nuevo componente del Generador de Documentos
import GeneradorDocumentos from './GeneradorDocumentos/GeneradorDocumentos';
import DocumentoConHilo from '../../compartidos/DocumentoConHilo';


// OPCIÓN 1: MODO RENDER (Producción) -> ¡ACTIVA ESTA!
const URL_BASE_BACKEND = "https://asistente-legal-backend-897g.onrender.com";

// OPCIÓN 2: MODO LOCAL (Tu PC) -> Comentada
// const URL_BASE_BACKEND = "http://127.0.0.1:8000";

const VistaExpedienteAsesor = ({ expedienteId, onVolverADashboard }) => {
  // ==========================================================================
  // 1. DECLARACIÓN DE ESTADOS
  // ==========================================================================
  
  const [expediente, setExpediente] = useState(null);
  const [estaCargando, setEstaCargando] = useState(true);
  const [error, setError] = useState(null);
  const [nuevaNota, setNuevaNota] = useState("");
  const [enviandoNota, setEnviandoNota] = useState(false);
  const [errorNota, setErrorNota] = useState(null);
  const [finalizandoCaso, setFinalizandoCaso] = useState(false);
  const [errorFinalizar, setErrorFinalizar] = useState(null);
  const [modoReasignacion, setModoReasignacion] = useState(false);
 // const [listaEstudiantes, setListaEstudiantes] = useState([]);
  //const [estudianteSeleccionadoId, setEstudianteSeleccionadoId] = useState('');
  const [reasignandoCaso, setReasignandoCaso] = useState(false);
  const [errorReasignacion, setErrorReasignacion] = useState(null);


  const [errorAccionDoc, setErrorAccionDoc] = useState('');
 const [descargandoPDF, setDescargandoPDF] = useState(false);


 // --- ESTADOS PARA MODAL DE CALIFICACIÓN ---
  const [mostrarModalCalificacion, setMostrarModalCalificacion] = useState(false);
  const [calificacion, setCalificacion] = useState(5);
  const [comentarioCierre, setComentarioCierre] = useState("");



 const handleDescargarReporte = async () => {
    setDescargandoPDF(true);
    const resultado = await apiDescargarReporteExpedientePDF(expedienteId);
    if (!resultado.exito) {
      alert(resultado.mensaje || "No se pudo descargar el reporte PDF.");
    }
    setDescargandoPDF(false);
  };



  // ==========================================================================
  // 2. EFECTOS Y MANEJADORES DE DATOS
  // ==========================================================================

  const cargarExpediente = useCallback(async () => {
    try {
      setEstaCargando(true);
      setError(null);
      const data = await apiObtenerDetalleExpedienteAsesor(expedienteId);
      
      // --- INICIO CORRECCIÓN ---
      
      // 1. Documentos
      const lineaDeTiempoDocs = (data.evidencias || []).map(e => ({ 
          ...e, 
          tipo: 'documento', 
          // Aseguramos fecha válida
          fechaSort: new Date(e.fecha_subida || data.fecha_creacion || 0) 
      }));

      // 2. Notas (CON FILTRO: id_evidencia === null)
      const lineaDeTiempoNotas = (data.notas || [])
          .filter(n => n.id_evidencia === null) // <--- ESTO ELIMINA LOS DUPLICADOS
          .map(n => ({ 
              ...n, 
              tipo: 'nota', 
              fechaSort: new Date(n.fecha_creacion || 0) 
          }));

      // 3. Unificar y Ordenar
      const lineaDeTiempoOrdenada = [...lineaDeTiempoDocs, ...lineaDeTiempoNotas].sort((a, b) => {
          return a.fechaSort - b.fechaSort; // Ascendente (Viejo -> Nuevo)
      });

      // --- FIN CORRECCIÓN ---

      setExpediente({ ...data, lineaDeTiempo: lineaDeTiempoOrdenada });
    } catch (err) {
      setError(err.message || "Ocurrió un error al cargar el expediente.");
      console.error(err);
    } finally {
      setEstaCargando(false);
    }
  }, [expedienteId]);

  useEffect(() => {
    cargarExpediente();
  }, [cargarExpediente]);

  // ==========================================================================
  // 3. MANEJADORES DE ACCIONES DEL USUARIO
  // ==========================================================================

  const handleCrearNota = async (e) => {
    e.preventDefault();
    if (!nuevaNota.trim()) return;
    
    setEnviandoNota(true);
    setErrorNota(null);
    
    try {
      // 1. Llamamos a la API para guardar la nota
      await apiCrearNotaAsesor(expedienteId, nuevaNota);
      
      // 2. Limpiamos el campo de texto
      setNuevaNota("");
      
      // 3. ¡CORRECCIÓN CRÍTICA!
      // En lugar de manipular el estado manualmente (lo que causaba el error),
      // recargamos el expediente. Esto asegura que la nueva nota pase por
      // la lógica de ordenamiento y formato de fecha de 'cargarExpediente'.
      await cargarExpediente(); 

    } catch (err) {
      setErrorNota(err.message || "Error al guardar la nota.");
    } finally {
      setEnviandoNota(false);
    }
  };
  const handleClicFinalizar = () => {
    // En lugar de cerrar directo, abrimos el modal
    setMostrarModalCalificacion(true);
  };

  const confirmarCierre = async () => {
    if (!comentarioCierre.trim()) {
      alert("Por favor ingrese un comentario de retroalimentación para el estudiante.");
      return;
    }

    const notaFloat = parseFloat(calificacion);
    if (isNaN(notaFloat) || notaFloat < 0 || notaFloat > 5) {
        alert("La calificación debe ser un número entre 0.0 y 5.0");
        return;
    }
    
    setFinalizandoCaso(true);
    setErrorFinalizar(null);
    try {
      // Llamamos a la API asegurando que la nota sea DECIMAL
      await apiFinalizarCaso(expedienteId, notaFloat, comentarioCierre); // <--- USO DE parseFloat
      
      setMostrarModalCalificacion(false);
      await cargarExpediente(); 
    } catch (err) {
      setErrorFinalizar(err.message || "Error al finalizar el caso.");
    } finally {
      setFinalizandoCaso(false);
    }
  };

const handleIniciarReasignacion = () => {
    // Ya no necesitamos cargar la lista de estudiantes
    setModoReasignacion(true);
    setErrorReasignacion(null);
    // Reiniciamos los campos de calificación por si acaso
    setCalificacion(5);
    setComentarioCierre("");
  };

 const handleCancelarReasignacion = () => {
    setModoReasignacion(false);
    setErrorReasignacion(null);
  };

 const handleConfirmarReasignacion = async () => {
    if (!comentarioCierre.trim()) {
      setErrorReasignacion("Debe ingresar un motivo para la reasignación.");
      return;
    }
    
    // Validación extra: Que la nota esté en rango
    const notaFloat = parseFloat(calificacion);
    if (isNaN(notaFloat) || notaFloat < 0 || notaFloat > 5) {
        setErrorReasignacion("La calificación debe ser un número entre 0.0 y 5.0");
        return;
    }

    setReasignandoCaso(true);
    setErrorReasignacion(null);
    
    try {
      // Preparamos el payload con la calificación DECIMAL
      const datosReasignacion = {
          calificacion_saliente: notaFloat, // <--- USO DE parseFloat
          comentario_saliente: comentarioCierre
      };
      
      const respuesta = await apiReasignarCaso(expedienteId, datosReasignacion);
      
      alert(respuesta.mensaje);
      onVolverADashboard(); 
    } catch (err) {
      setErrorReasignacion(err.message || "Error al reasignar.");
    } finally {
      setReasignandoCaso(false);
    }
  };




const handleAprobar = async (idEvidencia) => {
    // Quitamos setProcesandoDocId...
    setErrorAccionDoc('');
    try {
      await apiAprobarDocumento(idEvidencia);
      await cargarExpediente();
    } catch (err) {
      setErrorAccionDoc(err.message || 'Error al aprobar el documento.');
    } 
    // Quitamos el finally con setProcesandoDocId(null)...
  };

 

  const handleSolicitarCambios = async (idEvidencia) => {
    // Quitamos setProcesandoDocId...
    setErrorAccionDoc('');
    try {
      await apiSolicitarCambiosDocumento(idEvidencia);
      await cargarExpediente();
    } catch (err) {
      setErrorAccionDoc(err.message || 'Error al solicitar cambios.');
    }
  };

  // ==========================================================================
  // 4. RENDERIZADO DEL COMPONENTE
  // ==========================================================================

  if (estaCargando) return <div className={styles.contenedorCentrado}>Cargando detalles del expediente...</div>;
  if (error) return <div className={`${styles.contenedorCentrado} ${styles.error}`}>{error}</div>;
  if (!expediente) return <div className={styles.contenedorCentrado}>No se encontró la información del expediente.</div>;


// --- MANEJADOR PARA COMENTARIOS EN HILO (ASESOR) ---
  const handleEnviarComentarioHilo = async (idEvidencia, texto) => {
    try {
      // El asesor envía la nota atada al documento.
      // false = nota interna (generalmente el feedback de documentos es para el estudiante)
      await apiCrearNotaAsesor(expedienteId, texto, false, idEvidencia);
      await cargarExpediente(); 
    } catch (err) {
      alert("Error al enviar comentario: " + err.message);
    }
  };



  return (
    <div className={styles.vistaContenedor}>
      <button onClick={onVolverADashboard} className={styles.botonVolver}>&larr; Volver al Dashboard</button>
      
      <div className={styles.cabecera}>
        <div>
          <h2 className={styles.titulo}>Expediente del Caso #{expediente.id}</h2>
          <span className={styles.estadoCaso}>{expediente.estado}</span>
        </div>
        <div className={styles.cabeceraBotones}>
          <button 
            className={styles.botonDescargar}
            onClick={handleDescargarReporte}
            disabled={descargandoPDF}
          >
            {descargandoPDF ? "Generando..." : "Descargar Reporte"}
          </button>
          <button 
            className={styles.botonFinalizar}
            onClick={handleClicFinalizar}
            disabled={finalizandoCaso || expediente.estado === 'cerrado'}
          >
            {finalizandoCaso ? "Finalizando..." : "Finalizar Caso"}
          </button>
          {errorFinalizar && <p className={styles.errorAccion}>{errorFinalizar}</p>}
        </div>
      </div>

      <div className={styles.contenidoGrid}>
        <div className={styles.columnaPrincipal}>
          <h3>Línea de Tiempo del Expediente</h3>
          {errorAccionDoc && <p className={`${styles.error} ${styles.errorAccionDoc}`}>{errorAccionDoc}</p>}
          <div className={styles.lineaDeTiempo}>
            {expediente.lineaDeTiempo.map((item, index) => {
              
              // --- LÓGICA DE VISUALIZACIÓN MEJORADA ---
              const esAlerta = item.rol_autor === 'sistema' && (item.contenido.includes('ALERTA') || item.contenido.includes('🚨'));
              
              // Verificamos si es una nota creada por el equipo (Estudiante o Asesor)
              const esNotaEquipo = item.tipo === 'nota' && (item.rol_autor === 'asesor' || item.rol_autor === 'estudiante');
              
              // Diferenciamos Pública vs Privada
              const esPublica = item.es_publica === true;

              let claseItem = styles.itemTimeline;
              if (esAlerta) {
                  claseItem += ` ${styles.alertaSistema}`;
              } else if (esNotaEquipo) {
                  // Si es pública le ponemos una clase, si es privada otra
                  claseItem += esPublica ? ` ${styles.notaPublica}` : ` ${styles.notaInterna}`;
              }

              return (
                <div key={index} className={claseItem}>
                  
                  {/* --- ICONO DINÁMICO --- */}
                  <div className={`${styles.iconoTimeline} ${esAlerta ? styles.iconoAlerta : (esNotaEquipo ? (esPublica ? styles.iconoPublico : styles.iconoInterno) : '')}`}>
                    {esAlerta ? '🚨' : (item.tipo === 'documento' ? '📄' : (esPublica ? '📢' : '🔒'))}
                  </div>

                  <div className={styles.contenidoItem}>
                    {item.tipo === 'documento' ? (
                    
                    /* --- 1. VISTA DE DOCUMENTO CON HILO DE COMENTARIOS --- */
                    <DocumentoConHilo 
                        key={item.id}
                        documento={item}
                        notasRelacionadas={expediente.notas.filter(n => n.id_evidencia === item.id)}
                        onEnviarComentario={handleEnviarComentarioHilo}
                        
                        // CORRECCIÓN: Usamos la variable del interruptor, NO "http://127.0.0.1:8000"
                        baseURL={URL_BASE_BACKEND} 
                        
                        esAsesor={true} 
                        onAprobar={handleAprobar}
                        onSolicitarCambios={handleSolicitarCambios}
                    />
                    
                  ) : (
                    
                    /* --- 2. VISTA DE NOTAS SUELTAS O ALERTAS --- */
                    <>
                        <div className={`${styles.iconoTimeline} ${esAlerta ? styles.iconoAlerta : (esNotaEquipo ? (esPublica ? styles.iconoPublico : styles.iconoInterno) : '')}`}>
                            {/* Iconos: 🚨=Alerta, 📢=Público, 🔒=Privado */}
                            {esAlerta ? '🚨' : (esPublica ? '📢' : '🔒')}
                        </div>

                        <div className={styles.contenidoItem}>
                             
                             {esAlerta && <span className={styles.tituloAlerta}>⚠️ ALERTA DE USUARIO</span>}
                             
                             <p>
                                <strong>
                                    {esAlerta 
                                        ? 'Sistema de Monitoreo' 
                                        : `Nota de ${item.autor_nombre || item.rol_autor}`}
                                    
                                    {/* Etiqueta visual explícita */}
                                    {esNotaEquipo && (
                                        <span style={{
                                            fontSize: '0.75rem', 
                                            marginLeft: '10px', 
                                            padding: '2px 6px', 
                                            borderRadius: '4px',
                                            backgroundColor: esPublica ? '#d4edda' : '#cce5ff',
                                            color: esPublica ? '#155724' : '#004085',
                                            border: '1px solid',
                                            borderColor: esPublica ? '#c3e6cb' : '#b8daff'
                                        }}>
                                            {esPublica ? 'VISIBLE AL USUARIO' : 'INTERNO / PRIVADO'}
                                        </span>
                                    )}
                                </strong>
                             </p>
                             
                             <p className={styles.contenidoNota}>{item.contenido}</p>
                             
                            <span className={styles.fechaNota}>
                               {item.fechaSort ? item.fechaSort.toLocaleString() : 'Reciente'} {/* <--- ESTO ES LO NUEVO (fechaSort) */}
                             </span>
                        </div>
                    </>
                  )}
                  </div>
                </div>
              );
            })}
          </div>
          
          <AsistenteJuridico idCaso={expedienteId} />
          <GeneradorDocumentos idCaso={expedienteId} />

        </div>
        
        <div className={styles.columnaLateral}>
          <div className={styles.resumen}>
            <h3>Resumen del Caso</h3>
            <p><strong>Estudiante a Cargo:</strong> {expediente.estudiante_asignado || 'No asignado'}</p>
            <p><strong>Asesor Supervisor:</strong> {expediente.asesor_asignado || 'No asignado'}</p>
            <hr/>
            <h4>Hechos Reportados</h4>
            <p>{expediente.descripcion_hechos}</p>
          </div>
          
          <div className={styles.panelAcciones}>
            <h3>Acciones de Gestión</h3>
            {!modoReasignacion ? (
              <button
                onClick={handleIniciarReasignacion}
                className={styles.botonAccion}
                disabled={expediente.estado === 'cerrado'}
              >
                Reasignar Caso
              </button>
            ) : (
              <div className={styles.contenedorReasignacion}>
                <h4 style={{marginTop:0, color:'#d35400'}}>Reasignación de Caso</h4>
                <p style={{fontSize:'0.9rem'}}>Califique al estudiante actual antes de transferir el caso. El sistema buscará automáticamente un reemplazo.</p>
                
                {/* 1. Selector de Nota */}
                <div style={{marginBottom:'10px'}}>
                    <label style={{display:'block', fontWeight:'bold', fontSize:'0.85rem'}}>Calificación (Saliente):</label>
                    <input
                      type="number"
                      min="0"
                      max="5"
                      step="0.1"
                      value={calificacion} 
                      onChange={(e) => setCalificacion(e.target.value)}
                      placeholder="Ej: 3.5"
                      style={{width:'100%', padding:'5px', border:'1px solid #ccc', borderRadius:'4px'}}
                    />
                </div>

                {/* 2. Comentario Obligatorio */}
                <div style={{marginBottom:'10px'}}>
                    <label style={{display:'block', fontWeight:'bold', fontSize:'0.85rem'}}>Motivo / Feedback:</label>
                    <textarea
                        value={comentarioCierre} // Reusamos estado comentarioCierre
                        onChange={(e) => setComentarioCierre(e.target.value)}
                        placeholder="¿Por qué se reasigna? Feedback para el estudiante..."
                        rows="3"
                        style={{width:'100%', padding:'5px', borderRadius:'4px', border:'1px solid #ccc'}}
                    />
                </div>

                <div className={styles.botonesReasignacion}>
                  <button onClick={handleCancelarReasignacion} className={styles.botonCancelar}>Cancelar</button>
                  <button onClick={handleConfirmarReasignacion} disabled={reasignandoCaso} className={styles.botonConfirmar}>
                    {reasignandoCaso ? 'Procesando...' : 'Confirmar y Reasignar'}
                  </button>
                </div>
              </div>
            )}
            {errorReasignacion && <p className={styles.errorAccion}>{errorReasignacion}</p>}
          </div>

          <div className={styles.formularioNotas}>
            <h3>Añadir Nota de Supervisión</h3>
            <form onSubmit={handleCrearNota}>
              <textarea
                className={styles.textareaNota}
                value={nuevaNota}
                onChange={(e) => setNuevaNota(e.target.value)}
                placeholder="Escriba aquí sus observaciones o instrucciones para el estudiante..."
                rows="6"
                disabled={enviandoNota}
              />
              <button type="submit" className={styles.botonGuardarNota} disabled={enviandoNota}>
                {enviandoNota ? "Guardando..." : "Guardar Nota"}
              </button>
              {errorNota && <p className={styles.errorFormulario}>{errorNota}</p>}
            </form>
          </div>
        </div>
      </div>


            {/* --- MODAL DE CALIFICACIÓN (NUEVO) --- */}
      {mostrarModalCalificacion && (
        <div className={styles.overlayModal}>
            <div className={styles.modalCalificacion}>
                <h3 className={styles.tituloModal}>Evaluación Final</h3>
                <p>Califique el desempeño del estudiante para cerrar el caso.</p>
                
                <div className={styles.campoModal}>
                    <label>Nota (0.0 - 5.0):</label>
                    {/* CAMBIO: Input numérico en vez de Select */}
                    <input 
                        type="number" 
                        min="0" 
                        max="5" 
                        step="0.1" // Permite decimales
                        value={calificacion} 
                        onChange={(e) => setCalificacion(e.target.value)}
                        className={styles.inputCalificacion} // Asegúrate de tener estilo o usa style={{...}}
                        style={{width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc'}}
                        placeholder="Ej: 4.5"
                    />
                </div>

                <div className={styles.campoModal}>
                    <label>Retroalimentación:</label>
                    <textarea
                        value={comentarioCierre}
                        onChange={(e) => setComentarioCierre(e.target.value)}
                        placeholder="Escriba sus comentarios para el estudiante..."
                        rows="4"
                        className={styles.textareaModal}
                    />
                </div>

                <div className={styles.botonesModal}>
                    <button 
                        onClick={() => setMostrarModalCalificacion(false)} 
                        className={styles.botonCancelar}
                    >
                        Cancelar
                    </button>
                    <button 
                        onClick={confirmarCierre} 
                        className={styles.botonConfirmar}
                        disabled={finalizandoCaso}
                    >
                        {finalizandoCaso ? "Guardando..." : "Confirmar Cierre"}
                    </button>
                </div>
            </div>
        </div>
      )}


    </div>
  );
};

export default VistaExpedienteAsesor;