// frontend/src/componentes/estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante.jsx


// --- INICIO DE LA MODIFICACION ---
//->,apiEnviarNotificacion
// MODIFICACION: Añadimos useCallback y la nueva funcion de API
import React, { useState, useEffect, useCallback } from 'react';
import { apiObtenerDetalleExpediente, apiConsultarAgenteJuridico, apiGenerarDocumento, apiSubirDocumentoEstudiante, apiCrearNotaEstudiante, apiEnviarParaRevision,
  apiDescargarReporteExpedientePDF 
  } from '../../../servicios/api';
// --- FIN DE LA MODIFICACION ---
import ReactMarkdown from 'react-markdown'; 
import './VistaExpedienteEstudiante.css';
import DocumentoConHilo from '../../compartidos/DocumentoConHilo';

// Componente auxiliar para mostrar el reporte JSON de forma legible y segura
// const VisorReporteIA = ({ reporteJson }) => {
//   try {
//     const reporteObjeto = JSON.parse(reporteJson);
//     return (
//       <div className="visor-reporte-ia">
//         <h4>Reporte de Análisis IA</h4>
//         <pre>{JSON.stringify(reporteObjeto, null, 2)}</pre>
//       </div>
//     );
//   } catch (error) {
//     console.error("Error al parsear el reporte JSON:", error);
//     return (
//       <div className="visor-reporte-ia">
//         <h4>Reporte de Análisis IA</h4>
//         <p>El reporte no tiene un formato JSON válido o aún no ha sido generado.</p>
//         <pre>{reporteJson}</pre>
//       </div>
//     );
//   }
// };


const VisorReporteEstructurado = ({ reporteJson }) => {
  try {
    const reporte = JSON.parse(reporteJson);

    const renderizarSeccion = (titulo, data) => {
      if (!data) return null;
      // Caso especial para el Análisis Jurídico, que es un objeto con 'contenido'
      if (titulo === "Análisis Jurídico Inicial" && typeof data === 'object' && data.contenido) {
        return (
          <div className="reporte-seccion">
            <h4>{titulo}</h4>
            <div className="markdown-content">
              <ReactMarkdown>{data.contenido}</ReactMarkdown>
            </div>
          </div>
        );
      }
      return (
        <div className="reporte-seccion">
          <h4>{titulo}</h4>
          {Object.entries(data).map(([clave, valor]) => {
            if (typeof valor === 'object' && valor !== null) return null;
            const claveLegible = clave.replace(/_/g, ' ');
            const valorLegible = typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : String(valor);
            return (<p key={clave}><strong>{claveLegible}:</strong> {valorLegible}</p>);
          })}
        </div>
      );
    };

    return (
      <div className="visor-reporte-estructurado">
        <h3>Reporte de Análisis IA</h3>
        {renderizarSeccion("Fase de Triaje", reporte.TRIEJE)}
        {renderizarSeccion("Determinación de Competencia", reporte.COMPETENCIA)}
        {renderizarSeccion("Asignación de Caso", reporte.ASIGNACION)}
        {renderizarSeccion("Análisis Jurídico Inicial", reporte.ANALISIS_JURIDICO)}
      </div>
    );
  } catch (error) {
    console.error("Error al parsear el reporte JSON:", error);
    return (
      <div className="visor-reporte-ia">
        <h4>Reporte de Análisis IA (Formato no reconocido)</h4>
        <pre>{reporteJson}</pre>
      </div>
    );
  }
};


// --- Lista de plantillas disponibles ---
const PLANTILLAS_DISPONIBLES = [
  { nombre: "Derecho de Petición", archivo: "derecho_de_peticion.docx" },
  { nombre: "Acción de Tutela", archivo: "accion_de_tutela.docx" },
];



const VistaExpedienteEstudiante = ({ expedienteId, onVolver }) => {
  const [expediente, setExpediente] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  // Estados para el Agente Juridico ---
  const [preguntaAgente, setPreguntaAgente] = useState('');
  const [respuestaAgente, setRespuestaAgente] = useState(null);
  const [cargandoAgente, setCargandoAgente] = useState(false);
  const [errorAgente, setErrorAgente] = useState('');
  
  const [plantillaSeleccionada, setPlantillaSeleccionada] = useState(PLANTILLAS_DISPONIBLES[0].archivo);
  const [cargandoDocumento, setCargandoDocumento] = useState(false);
  const [errorDocumento, setErrorDocumento] = useState('');
  const [documentoGenerado, setDocumentoGenerado] = useState(null); // { url_descarga, nombre_archivo }

// MODIFICACION: Estados para la subida de archivos del estudiante
  const [archivoASubir, setArchivoASubir] = useState(null);
  const [cargandoSubida, setCargandoSubida] = useState(false);
  const [errorSubida, setErrorSubida] = useState('');



  const [nuevaNota, setNuevaNota] = useState('');
  const [cargandoNota, setCargandoNota] = useState(false);
  const [errorNota, setErrorNota] = useState('');

  const [enviandoRevisionId, setEnviandoRevisionId] = useState(null); // ID del doc en proceso
  const [errorAccion, setErrorAccion] = useState('');

  const [descargandoPDF, setDescargandoPDF] = useState(false);
const [destinatarioNota, setDestinatarioNota] = useState('asesor'); // 'asesor' (privado) o 'usuario' (público)
  const [destinatarioDoc, setDestinatarioDoc] = useState('asesor'); 
// const [asuntoNotificacion, setAsuntoNotificacion] = useState('');
  // const [mensajeNotificacion, setMensajeNotificacion] = useState('');
  // const [enviandoNotificacion, setEnviandoNotificacion] = useState(false);
  // const [errorNotificacion, setErrorNotificacion] = useState('');






const handleDescargarReporte = async () => {
    setDescargandoPDF(true);
    const resultado = await apiDescargarReporteExpedientePDF(expedienteId);
    if (!resultado.exito) {
      alert(resultado.mensaje || "No se pudo descargar el reporte PDF.");
    }
    setDescargandoPDF(false);
  };



 // Esto asegura que la función no se recree en cada render, a menos que sus dependencias cambien.
  // No necesita saber el valor anterior de 'expediente' para funcionar.
  const cargarExpediente = useCallback(async () => {
    if (!expedienteId) return;
    try {
      // No necesitamos la condición 'if (!expediente)' aquí, 
      // la lógica de 'cargando' se maneja por separado.
      setCargando(true); 
      setError('');
      setErrorAccion('');
      const datosExpediente = await apiObtenerDetalleExpediente(expedienteId);
      setExpediente(datosExpediente);
    } catch (err) {
      setError(err.message || 'Ocurrió un error al cargar el expediente.');
    } finally {
      setCargando(false);
    }
  }, [expedienteId]); // La única dependencia correcta es expedienteId

  // PASO B: Este useEffect ahora se comporta como se espera.
  // Solo se ejecutará si la función 'cargarExpediente' cambia,
  // lo cual ahora solo sucederá si 'expedienteId' cambia.
  useEffect(() => {
    cargarExpediente();
  }, [cargarExpediente]);

  // --- INICIO DE LA MODIFICACION: Funcion para manejar la consulta al agente ---
  const handleConsultarAgente = async (e) => {
    e.preventDefault(); // Evita que la pagina se recargue al enviar el formulario
    if (!preguntaAgente.trim()) return; // No enviar preguntas vacias

    setCargandoAgente(true);
    setErrorAgente('');
    setRespuestaAgente(null);

    try {
      const respuesta = await apiConsultarAgenteJuridico(expedienteId, preguntaAgente);
      setRespuestaAgente(respuesta);
    } catch (err) {
      setErrorAgente(err.message || 'Ocurrió un error al consultar al agente.');
    } finally {
      setCargandoAgente(false);
    }
  };
  // --- FIN DE LA MODIFICACION ---


const handleGenerarDocumento = async (e) => {
    e.preventDefault();
    setCargandoDocumento(true);
    setErrorDocumento('');
    setDocumentoGenerado(null);
    try {
      const resultado = await apiGenerarDocumento(expedienteId, plantillaSeleccionada);
      setDocumentoGenerado(resultado);
    } catch (err) {
      setErrorDocumento(err.message || 'Ocurrió un error al generar el documento.');
    } finally {
      setCargandoDocumento(false);
    }
  };


   const handleSubirDocumento = async (e) => {
    e.preventDefault();
    if (!archivoASubir) {
      setErrorSubida("Por favor, seleccione un archivo para subir.");
      return;
    }
    setCargandoSubida(true);
    setErrorSubida('');
    
    // Determinamos si es pública basándonos en el selector
    const esPublica = destinatarioDoc === 'usuario';

    try {
      // Pasamos el 3er argumento 'esPublica' a la API
      await apiSubirDocumentoEstudiante(expedienteId, archivoASubir, esPublica);
      
      setArchivoASubir(null);
      e.target.reset(); 
      await cargarExpediente(); 
    } catch (err) {
      setErrorSubida(err.message || 'Ocurrió un error al subir el archivo.');
    } finally {
      setCargandoSubida(false);
    }
  };



const handleCrearNota = async (e) => {
    e.preventDefault();
    if (!nuevaNota.trim()) return;
    
    setCargandoNota(true);
    // Determinamos si es pública basándonos en el destinatario
    const esPublica = destinatarioNota === 'usuario';
    
    try {
      // Nota: apiCrearNotaEstudiante debe actualizarse para recibir el 3er parametro (esPublica)
      // O pasar un objeto. Vamos a actualizar la llamada API primero.
      await apiCrearNotaEstudiante(expedienteId, nuevaNota, esPublica); 
      
      setNuevaNota(''); 
      await cargarExpediente();
    } catch (err) {
      setErrorNota(err.message);
    } finally {
      setCargandoNota(false);
    }
};


  const handleEnviarParaRevision = async (idEvidencia) => {
    setEnviandoRevisionId(idEvidencia);
    setErrorAccion('');
    try {
      await apiEnviarParaRevision(idEvidencia);
      await cargarExpediente(); // Recargar para ver el nuevo estado
    } catch (err) {
      setErrorAccion(err.message || 'Error al enviar el documento.');
    } finally {
      setEnviandoRevisionId(null);
    }
  };


  // const handleEnviarNotificacion = async (e) => {
  //   e.preventDefault();
  //   if (!asuntoNotificacion.trim() || !mensajeNotificacion.trim()) {
  //     setErrorNotificacion("El asunto y el mensaje no pueden estar vacíos.");
  //     return;
  //   }
  //   setEnviandoNotificacion(true);
  //   setErrorNotificacion('');
  //   try {
  //     const respuesta = await apiEnviarNotificacion(expedienteId, asuntoNotificacion, mensajeNotificacion);
  //     alert(respuesta.mensaje || "Notificación enviada con éxito."); // Feedback para el estudiante
  //     setAsuntoNotificacion(''); // Limpiar el formulario
  //     setMensajeNotificacion('');
  //     await cargarExpediente(); // Recargar para ver la nueva nota de "sistema" en la línea de tiempo
  //   } catch (err) {
  //     setErrorNotificacion(err.message || 'Ocurrió un error al enviar la notificación.');
  //   } finally {
  //     setEnviandoNotificacion(false);
  //   }
  // };


  if (cargando) {
    return <div className="vista-expediente-cargando">Cargando expediente...</div>;
  }

  if (error) {
    return <div className="vista-expediente-error">Error: {error} <button onClick={onVolver}>Volver</button></div>;
  }

  if (!expediente) {
    return <div className="vista-expediente-cargando">No se encontró el expediente.</div>;
  }

   // OPCIÓN 1: MODO RENDER (Nube) -> ¡ACTIVA!
  const baseURL = "https://asistente-legal-backend-897g.onrender.com";

  // OPCIÓN 2: MODO LOCAL (PC) -> ¡COMENTADA!
  // const baseURL = "http://127.0.0.1:8000";



// --- INICIO DE LA MODIFICACION: Lógica para la Línea de Tiempo ---
 const eventosDocumento = (expediente.evidencias || []).map(ev => {
    // Intentamos obtener una fecha válida. Si no existe, usamos la fecha actual como fallback para que no rompa.
    const fechaString = ev.fecha_subida || ev.fecha_creacion;
    const fechaObj = fechaString ? new Date(fechaString) : new Date(); 
    
    return {
      tipo: 'documento',
      fechaSort: fechaObj, // Usamos esta fecha para ordenar
      ...ev
    };
  });
   const eventosNota = (expediente.notas || [])
    // FILTRO CRÍTICO: Si 'id_evidencia' tiene un valor (no es null), NO lo mostramos aquí.
    // (Porque ya se mostrará dentro de la tarjeta del documento correspondiente)
    .filter(nota => nota.id_evidencia === null) 
    .map(nota => {
      const fechaString = nota.fecha_creacion;
      const fechaObj = fechaString ? new Date(fechaString) : new Date();

      return {
        tipo: 'nota',
        fechaSort: fechaObj,
        ...nota
      };
    });

  // Combinamos y ordenamos por fecha. Los documentos sin fecha van al final.
   const lineaDeTiempo = [...eventosDocumento, ...eventosNota].sort((a, b) => {
    return a.fechaSort - b.fechaSort;
  });



  return (
    <div className="vista-expediente-contenedor">
      <button onClick={onVolver} className="boton-volver">&larr; Volver al Dashboard</button>
      
      <h2>Detalle del Expediente #{expediente.id}</h2>
      <div className="expediente-seccion-acciones">
        <button
          onClick={handleDescargarReporte}
          className="boton-accion-principal"
          disabled={descargandoPDF}
        >
          {descargandoPDF ? 'Generando PDF...' : 'Descargar Reporte Completo'}
        </button>
      </div>
      
      <div className="expediente-metadata">
        <p><strong>Fecha de Creación:</strong> {new Date(expediente.fecha_creacion).toLocaleString('es-CO')}</p>
        <p><strong>Estado:</strong> <span className={`estado-caso estado-${expediente.estado.replace('_', '-')}`}>{expediente.estado.replace('_', ' ')}</span></p>
      {expediente.asesor_asignado && (
          <p><strong>Asesor Supervisor del Caso:</strong> {expediente.asesor_asignado}</p>
        )}
      </div>

      <div className="expediente-seccion">
        <h3>Descripción de los Hechos</h3>
        <p>{expediente.descripcion_hechos}</p>
      </div>

      <div className="expediente-seccion">
        <h3>Línea de Tiempo del Expediente</h3>
        {errorAccion && <p className="error-texto error-accion">{errorAccion}</p>}
        <div className="linea-de-tiempo-contenedor">
          {lineaDeTiempo.length > 0 ? (
            lineaDeTiempo.map((item, index) => {
              
              // --- LÓGICA DE DETECCIÓN ---
              const esAlerta = item.rol_autor === 'sistema' && (item.contenido.includes('ALERTA') || item.contenido.includes('🚨'));
              const esNotaInterna = item.tipo === 'nota' && (item.rol_autor === 'asesor' || item.rol_autor === 'estudiante');
              
              let claseItem = "linea-de-tiempo-item";
              if (esAlerta) claseItem += " alerta-sistema";
              else if (esNotaInterna) claseItem += " nota-interna";


        const handleEnviarComentarioHilo = async (idEvidencia, texto) => {
    try {
      // Llamamos a la API enviando el ID del documento
      // false = es nota interna (no pública para el ciudadano) dentro del hilo de revisión
      await apiCrearNotaEstudiante(expedienteId, texto, false, idEvidencia);
      await cargarExpediente(); // Recargar para ver el nuevo comentario
    } catch (err) {
      alert("Error al enviar comentario: " + err.message);
    }
  };      



              return (
                <div key={`${item.tipo}-${item.id || index}`} className={claseItem}>
                  
                  {item.tipo === 'documento' && (
                    <div className="documento-wrapper">
                        {/* 1. Renderizamos el documento con su hilo de comentarios */}
                        <DocumentoConHilo 
                            documento={item}
                            notasRelacionadas={expediente.notas.filter(n => n.id_evidencia === item.id)}
                            onEnviarComentario={handleEnviarComentarioHilo}
                            baseURL={baseURL}
                            esAsesor={false} // Eres estudiante
                        />
                        
                        {/* 2. Mantenemos el botón de "Enviar a Revisión" justo debajo */}
                        {item.estado === 'subido' && (
                            <div style={{ marginTop: '-10px', marginBottom: '15px', marginLeft: '10px' }}>
                                <button 
                                    onClick={() => handleEnviarParaRevision(item.id)}
                                    className="boton-accion-doc"
                                    disabled={enviandoRevisionId === item.id}
                                    style={{ fontSize: '0.85rem', padding: '5px 10px' }}
                                >
                                    {enviandoRevisionId === item.id ? 'Enviando...' : '📤 Enviar a Revisión'}
                                </button>
                            </div>
                        )}
                    </div>
                  )}

                  {item.tipo === 'nota' && (
                    <>
                      {/* --- ICONO DINÁMICO --- */}
                      <span className={`icono ${esAlerta ? 'alerta' : ''}`}>
                        {esAlerta ? '🚨' : (item.es_publica ? '📢' : '🔒')} 
                        {/* 🔒 = Privado, 📢 = Público */}
                      </span>
                      
                      <div className="contenido">
                         {esAlerta && <span className="titulo-alerta">⚠️ ATENCIÓN REQUERIDA</span>}
                         
                         <p>
                            <strong>
                              {esAlerta ? 'Sistema:' : `Nota de ${item.autor_nombre || item.rol_autor}`}
                              
                              {/* ETIQUETA VISUAL */}
                              {!esAlerta && (
                                <span style={{
                                    fontSize: '0.75rem', 
                                    marginLeft: '8px', 
                                    padding: '2px 6px', 
                                    borderRadius: '4px',
                                    backgroundColor: item.es_publica ? '#d4edda' : '#e2e3e5',
                                    color: item.es_publica ? '#155724' : '#383d41',
                                    border: '1px solid',
                                    borderColor: item.es_publica ? '#c3e6cb' : '#d6d8db'
                                }}>
                                    {item.es_publica ? 'PÚBLICO (Visible al Usuario)' : 'INTERNO (Privado)'}
                                </span>
                              )}
                            </strong>
                         </p>
                        
                        <p>{item.contenido}</p>
                        
                       <small>
                        {/* Cambia item.fecha_creacion por item.fechaSort para asegurar que se vea */}
                        {item.fechaSort.toLocaleString('es-CO')} 
                    </small>
                      </div>
                    </>
                  )}
                </div>
              );
            })
          ) : <p>No hay documentos ni notas en este expediente.</p>}
        </div>

        <div className="formularios-accion-contenedor">
          <form onSubmit={handleSubirDocumento} className="formulario-accion">
            <h4>Añadir Documento</h4>
            
            {/* --- NUEVO SELECTOR DE PRIVACIDAD PARA DOCUMENTOS --- */}
            <div className="selector-destinatario">
                <label>Para:</label>
                <div className="toggle-group">
                    <button 
                        type="button"
                        className={`toggle-btn ${destinatarioDoc === 'asesor' ? 'active privado' : ''}`}
                        onClick={() => setDestinatarioDoc('asesor')}
                    >
                        🔒 Asesor (Interno)
                    </button>
                    <button 
                        type="button"
                        className={`toggle-btn ${destinatarioDoc === 'usuario' ? 'active publico' : ''}`}
                        onClick={() => setDestinatarioDoc('usuario')}
                    >
                        📢 Usuario (Público)
                    </button>
                </div>
            </div>
            {/* ---------------------------------------------------- */}

            <input 
              type="file" 
              onChange={(e) => setArchivoASubir(e.target.files[0])}
              disabled={cargandoSubida}
            />
            {/* Cambiamos el texto del botón para reflejar la acción */}
            <button type="submit" disabled={cargandoSubida} className={`btn-enviar ${destinatarioDoc}`}>
              {cargandoSubida ? 'Subiendo...' : `Subir para ${destinatarioDoc === 'usuario' ? 'Ciudadano' : 'Asesor'}`}
            </button>
            {errorSubida && <p className="error-texto">{errorSubida}</p>}
          </form>

          <form onSubmit={handleCrearNota} className="formulario-accion nota-box">
        <h4>Redactar Mensaje</h4>
        
        {/* --- SELECTOR DE DESTINATARIO --- */}
        <div className="selector-destinatario">
            <label>Para:</label>
            <div className="toggle-group">
                <button 
                    type="button"
                    className={`toggle-btn ${destinatarioNota === 'asesor' ? 'active privado' : ''}`}
                    onClick={() => setDestinatarioNota('asesor')}
                >
                    🔒 Asesor (Interno)
                </button>
                <button 
                    type="button"
                    className={`toggle-btn ${destinatarioNota === 'usuario' ? 'active publico' : ''}`}
                    onClick={() => setDestinatarioNota('usuario')}
                >
                    📢 Usuario (Público)
                </button>
            </div>
        </div>
        {/* ------------------------------- */}

        <textarea 
          value={nuevaNota} 
          onChange={(e) => setNuevaNota(e.target.value)} 
          placeholder={destinatarioNota === 'asesor' ? "Nota interna para el supervisor..." : "Mensaje visible para el ciudadano..."}
          disabled={cargandoNota} 
          rows={4}
        />
        <button type="submit" disabled={cargandoNota} className={`btn-enviar ${destinatarioNota}`}>
          {cargandoNota ? 'Enviando...' : `Enviar a ${destinatarioNota === 'usuario' ? 'Ciudadano' : 'Asesor'}`}
        </button>
        {errorNota && <p className="error-texto">{errorNota}</p>}
      </form>

          {/* <form onSubmit={handleEnviarNotificacion} className="formulario-accion">
            <h4>Enviar Notificación al Usuario por Email</h4>
            <input
              type="text"
              value={asuntoNotificacion}
              onChange={(e) => setAsuntoNotificacion(e.target.value)}
              placeholder="Asunto del correo"
              disabled={enviandoNotificacion}
            />
            <textarea
              value={mensajeNotificacion}
              onChange={(e) => setMensajeNotificacion(e.target.value)}
              placeholder="Escriba el mensaje para el usuario aquí. Puede usar este medio para solicitar documentos adicionales."
              disabled={enviandoNotificacion}
              rows={4}
            />
            <button type="submit" disabled={enviandoNotificacion}>
              {enviandoNotificacion ? 'Enviando...' : 'Enviar Email'}
            </button>
            {errorNotificacion && <p className="error-texto">{errorNotificacion}</p>}
          </form> */}

        </div>
      </div>

      {expediente.reporte_consolidado && (
        <div className="expediente-seccion">
          <VisorReporteEstructurado reporteJson={expediente.reporte_consolidado} />
        </div>
      )}

      <div className="expediente-seccion">
        <h3>Asistente Jurídico (IA)</h3>
        <p>Realice una consulta sobre este caso al agente especializado.</p>
        <form onSubmit={handleConsultarAgente} className="agente-formulario">
          <textarea
            value={preguntaAgente}
            onChange={(e) => setPreguntaAgente(e.target.value)}
            placeholder="Escriba su pregunta aquí..."
            className="agente-textarea"
            disabled={cargandoAgente}
          />
          <button type="submit" className="agente-boton-enviar" disabled={cargandoAgente}>
            {cargandoAgente ? 'Consultando...' : 'Consultar'}
          </button>
        </form>
        <div className="agente-area-respuesta">
          {cargandoAgente && <p>Procesando...</p>}
          {errorAgente && <p className="agente-error">Error: {errorAgente}</p>}
          {respuestaAgente && (
            <div className="agente-respuesta-formateada">
              <h4>Respuesta:</h4>
              <ReactMarkdown>{respuestaAgente.contenido}</ReactMarkdown>
              <h5>Fuentes:</h5>
              <ul>{respuestaAgente.fuentes.map((f, i) => (<li key={i}>{f}</li>))}</ul>
            </div>
          )}
        </div>
      </div>

      <div className="expediente-seccion">
        <h3>Generador de Documentos (IA)</h3>
        <p>Seleccione una plantilla para generar un borrador automático con los datos del caso.</p>
        <form onSubmit={handleGenerarDocumento} className="documento-formulario">
          <select 
            value={plantillaSeleccionada} 
            onChange={(e) => setPlantillaSeleccionada(e.target.value)}
            className="documento-selector"
            disabled={cargandoDocumento}
          >
            {PLANTILLAS_DISPONIBLES.map((plantilla) => (
              <option key={plantilla.archivo} value={plantilla.archivo}>
                {plantilla.nombre}
              </option>
            ))}
          </select>
          <button type="submit" className="documento-boton-generar" disabled={cargandoDocumento}>
            {cargandoDocumento ? 'Generando...' : 'Generar Documento'}
          </button>
        </form>
        <div className="documento-area-resultado">
          {cargandoDocumento && <p>Generando borrador, por favor espere...</p>}
          {errorDocumento && <p className="documento-error">Error: {errorDocumento}</p>}
          {documentoGenerado && (
            <div className="documento-enlace-descarga">
              <p>¡Documento generado con éxito!</p>
              <a 
                href={`${baseURL}${documentoGenerado.url_descarga}`} 
                download={documentoGenerado.nombre_archivo}
              >
                Descargar: {documentoGenerado.nombre_archivo}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VistaExpedienteEstudiante;