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

  const [procesandoDocId, setProcesandoDocId] = useState(null);
  const [errorAccionDoc, setErrorAccionDoc] = useState('');
 const [descargandoPDF, setDescargandoPDF] = useState(false);



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
      await apiCrearNotaAsesor(expedienteId, nuevaNota);
      setNuevaNota("");
      await cargarExpediente();
    } catch (err) {
      setErrorNota(err.message || "Error al guardar la nota.");
    } finally {
      setEnviandoNota(false);
    }
  };

  const handleFinalizarCaso = async () => {
    if (!window.confirm("¿Está seguro de que desea marcar este caso como finalizado? Esta acción no se puede deshacer.")) return;
    setFinalizandoCaso(true);
    setErrorFinalizar(null);
    try {
      await apiFinalizarCaso(expedienteId);
      await cargarExpediente();
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
    setProcesandoDocId(idEvidencia);
    setErrorAccionDoc('');
    try {
      await apiAprobarDocumento(idEvidencia);
      await cargarExpediente();
    } catch (err) {
      setErrorAccionDoc(err.message || 'Error al aprobar el documento.');
    } finally {
      setProcesandoDocId(null);
    }
  };

 

  const handleSolicitarCambios = async (idEvidencia) => {
    setProcesandoDocId(idEvidencia);
    setErrorAccionDoc('');
    try {
      await apiSolicitarCambiosDocumento(idEvidencia);
      await cargarExpediente();
    } catch (err) {
      setErrorAccionDoc(err.message || 'Error al solicitar cambios.');
    } finally {
      setProcesandoDocId(null);
    }
  };

  // ==========================================================================
  // 4. RENDERIZADO DEL COMPONENTE
  // ==========================================================================

  if (estaCargando) return <div className={styles.contenedorCentrado}>Cargando detalles del expediente...</div>;
  if (error) return <div className={`${styles.contenedorCentrado} ${styles.error}`}>{error}</div>;
  if (!expediente) return <div className={styles.contenedorCentrado}>No se encontró la información del expediente.</div>;

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
            onClick={handleFinalizarCaso}
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
            {expediente.lineaDeTiempo.map((item, index) => (
              <div key={index} className={styles.itemTimeline}>
                <div className={`${styles.iconoTimeline} ${item.rol_autor === 'asesor' ? styles.iconoAsesor : ''}`}>
                  {item.tipo === 'documento' ? '📄' : '📝'}
                </div>
                <div className={styles.contenidoItem}>
                  {item.tipo === 'documento' ? (
                    <>
                      <p><strong>Documento:</strong> {item.nombre_archivo}</p>
                      <a href={`http://127.0.0.1:8000${item.ruta_archivo}`} target="_blank" rel="noopener noreferrer" className={styles.enlaceDescarga}>Descargar</a>
                      <div className={styles.documentoEstadoContenedor}>
                        <span className={`${styles.estadoDocumento} ${styles['estado-' + item.estado.replace('_', '-')]}`}>{item.estado.replace('_', ' ')}</span>
                        
                        {item.estado === 'en_revision' && (
                          <div className={styles.botonesRevision}>
                            <button onClick={() => handleAprobar(item.id)} className={styles.botonAprobar} disabled={procesandoDocId === item.id}>
                              {procesandoDocId === item.id ? '...' : 'Aprobar'}
                            </button>
                            <button onClick={() => handleSolicitarCambios(item.id)} className={styles.botonRechazar} disabled={procesandoDocId === item.id}>
                              {procesandoDocId === item.id ? '...' : 'Solicitar Cambios'}
                            </button>
                          </div>
                        )}
                      </div>
                    </>
                  ) : (
                    <>
                      <p><strong>{item.rol_autor === 'asesor' ? 'Nota de Supervisión (Asesor):' : 'Nota del Estudiante:'}</strong></p>
                      <p className={styles.contenidoNota}>{item.contenido}</p>
                      <span className={styles.fechaNota}>{new Date(item.fecha).toLocaleString()}</span>
                    </>
                  )}
                </div>
              </div>
            ))}
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
    </div>
  );
};

export default VistaExpedienteAsesor;