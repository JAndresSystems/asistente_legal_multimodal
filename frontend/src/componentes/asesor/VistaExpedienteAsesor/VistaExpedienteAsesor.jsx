//C:\react\asistente_legal_multimodal\frontend\src\componentes\asesor\VistaExpedienteAsesor\VistaExpedienteAsesor.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { 
  apiObtenerDetalleExpedienteAsesor, 
  apiCrearNotaAsesor, 
  apiFinalizarCaso,
  apiObtenerEstudiantes,
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
  const [listaEstudiantes, setListaEstudiantes] = useState([]);
  const [estudianteSeleccionadoId, setEstudianteSeleccionadoId] = useState('');
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
      
      const lineaDeTiempo = [
        ...(data.evidencias || []).map(e => ({ ...e, tipo: 'documento', fecha: new Date(data.fecha_creacion) })),
        ...(data.notas || []).map(n => ({ ...n, tipo: 'nota', fecha: new Date(n.fecha_creacion) }))
      ].sort((a, b) => new Date(a.fecha) - new Date(b.fecha));

      setExpediente({ ...data, lineaDeTiempo });
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
      // 1. Capturamos la nota creada que devuelve el backend.
      const notaCreada = await apiCrearNotaAsesor(expedienteId, nuevaNota);
      setNuevaNota("");
      
      // 2. Actualizamos el estado local directamente, lo que es más rápido.
      setExpediente(prev => {
        // Añadimos el item formateado a la línea de tiempo
        const nuevaLineaDeTiempo = [
          ...prev.lineaDeTiempo,
          { ...notaCreada, tipo: 'nota', fecha: new Date(notaCreada.fecha_creacion) }
        ].sort((a, b) => new Date(a.fecha) - new Date(b.fecha)); // Re-ordenamos
        
        // Devolvemos el nuevo estado del expediente completo
        return { 
          ...prev, 
          lineaDeTiempo: nuevaLineaDeTiempo, 
          notas: [...prev.notas, notaCreada] 
        };
      });

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
    
    setFinalizandoCaso(true);
    setErrorFinalizar(null);
    try {
      // Llamamos a la API con los nuevos datos
      await apiFinalizarCaso(expedienteId, calificacion, comentarioCierre);
      setMostrarModalCalificacion(false);
      await cargarExpediente(); // Recargar para ver el estado cerrado
    } catch (err) {
      setErrorFinalizar(err.message || "Error al finalizar el caso.");
    } finally {
      setFinalizandoCaso(false);
    }
  };

  const handleIniciarReasignacion = async () => {
    setModoReasignacion(true);
    setErrorReasignacion(null);
    try {
      const estudiantes = await apiObtenerEstudiantes();
      const estudiantesFiltrados = estudiantes.filter(est => est.nombre_completo !== expediente.estudiante_asignado);
      setListaEstudiantes(estudiantesFiltrados);
    } catch (err) {
      setErrorReasignacion(err.message || "Error al cargar la lista de estudiantes.");
    }
  };

  const handleCancelarReasignacion = () => {
    setModoReasignacion(false);
    setEstudianteSeleccionadoId('');
    setErrorReasignacion(null);
  };

  const handleConfirmarReasignacion = async () => {
    if (!estudianteSeleccionadoId) {
      setErrorReasignacion("Por favor, seleccione un estudiante.");
      return;
    }
    setReasignandoCaso(true);
    setErrorReasignacion(null);
    try {
      const respuesta = await apiReasignarCaso(expedienteId, parseInt(estudianteSeleccionadoId));
      alert(respuesta.mensaje);
      onVolverADashboard();
    } catch (err) {
      setErrorReasignacion(err.message || "Ocurrió un error durante la reasignación.");
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
                        // Filtramos notas que pertenecen a este doc para mostrarlas en su hilo
                        notasRelacionadas={expediente.notas.filter(n => n.id_evidencia === item.id)}
                        onEnviarComentario={handleEnviarComentarioHilo}
                        baseURL="http://127.0.0.1:8000"
                        esAsesor={true} // Esto activa los botones de Aprobar/Rechazar dentro del componente
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
                                {new Date(item.fecha).toLocaleString()}
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
                <p>Seleccione el nuevo estudiante a cargo:</p>
                <select
                  value={estudianteSeleccionadoId}
                  onChange={(e) => setEstudianteSeleccionadoId(e.target.value)}
                  className={styles.selectEstudiante}
                >
                  <option value="">-- Seleccionar estudiante --</option>
                  {listaEstudiantes.map((est) => (
                    <option key={est.id} value={est.id}>
                      {est.nombre_completo} ({est.area_especialidad})
                    </option>
                  ))}
                </select>
                <div className={styles.botonesReasignacion}>
                  <button onClick={handleCancelarReasignacion} className={styles.botonCancelar}>Cancelar</button>
                  <button onClick={handleConfirmarReasignacion} disabled={reasignandoCaso} className={styles.botonConfirmar}>
                    {reasignandoCaso ? 'Reasignando...' : 'Confirmar'}
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
                    <label>Nota (1-5):</label>
                    <select 
                        value={calificacion} 
                        onChange={(e) => setCalificacion(e.target.value)}
                        className={styles.selectCalificacion}
                    >
                        <option value="5">5 - Excelente</option>
                        <option value="4">4 - Bueno</option>
                        <option value="3">3 - Aceptable</option>
                        <option value="2">2 - Insuficiente</option>
                        <option value="1">1 - Deficiente</option>
                    </select>
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