// frontend/src/componentes/estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante.jsx


// --- INICIO DE LA MODIFICACION ---
// MODIFICACION: Añadimos useCallback y la nueva funcion de API
import React, { useState, useEffect, useCallback } from 'react';
import { apiObtenerDetalleExpediente, apiConsultarAgenteJuridico, apiGenerarDocumento, apiSubirDocumentoEstudiante, apiCrearNotaEstudiante } from '../../../servicios/api';
// --- FIN DE LA MODIFICACION ---
import './VistaExpedienteEstudiante.css';

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

    // Funcion auxiliar para renderizar una seccion del reporte
    const renderizarSeccion = (titulo, data) => {
      if (!data) return null;
      return (
        <div className="reporte-seccion">
          <h4>{titulo}</h4>
          {Object.entries(data).map(([clave, valor]) => {
            if (typeof valor === 'object' && valor !== null) return null; // Omitir objetos anidados por ahora
            const claveLegible = clave.replace(/_/g, ' ');
            const valorLegible = typeof valor === 'boolean' ? (valor ? 'Sí' : 'No') : String(valor);
            return (
              <p key={clave}><strong>{claveLegible}:</strong> {valorLegible}</p>
            );
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

 // Esto asegura que la función no se recree en cada render, a menos que sus dependencias cambien.
  // No necesita saber el valor anterior de 'expediente' para funcionar.
  const cargarExpediente = useCallback(async () => {
    if (!expedienteId) return;
    try {
      // No necesitamos la condición 'if (!expediente)' aquí, 
      // la lógica de 'cargando' se maneja por separado.
      setCargando(true); 
      setError('');
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
    try {
      await apiSubirDocumentoEstudiante(expedienteId, archivoASubir);
      // Éxito! Limpiamos el input y recargamos los datos del expediente
      setArchivoASubir(null);
      e.target.reset(); // Limpia el formulario
      await cargarExpediente(); // Refresca la lista de evidencias
    } catch (err) {
      setErrorSubida(err.message || 'Ocurrió un error al subir el archivo.');
    } finally {
      setCargandoSubida(false);
    }
  };



  const handleCrearNota = async (e) => {
    e.preventDefault();
    if (!nuevaNota.trim()) {
      setErrorNota("La nota no puede estar vacía.");
      return;
    }
    setCargandoNota(true);
    setErrorNota('');
    try {
      await apiCrearNotaEstudiante(expedienteId, nuevaNota);
      setNuevaNota(''); // Limpiar el textarea
      await cargarExpediente(); // Refrescar la línea de tiempo
    } catch (err) {
      setErrorNota(err.message || 'Ocurrió un error al guardar la nota.');
    } finally {
      setCargandoNota(false);
    }
  };



  if (cargando) {
    return <div className="vista-expediente-cargando">Cargando expediente...</div>;
  }

  if (error) {
    return <div className="vista-expediente-error">Error: {error} <button onClick={onVolver}>Volver</button></div>;
  }

  if (!expediente) {
    return <div className="vista-expediente-cargando">No se encontró el expediente.</div>;
  }

  const baseURL = 'http://127.0.0.1:8000';



// --- INICIO DE LA MODIFICACION: Lógica para la Línea de Tiempo ---
  const eventosDocumento = (expediente.evidencias || []).map(ev => ({
    tipo: 'documento',
    ...ev
  }));
  const eventosNota = (expediente.notas || []).map(nota => ({
    tipo: 'nota',
    ...nota
  }));

  // Combinamos y ordenamos por fecha. Los documentos sin fecha van al final.
  const lineaDeTiempo = [...eventosDocumento, ...eventosNota].sort((a, b) => {
    const fechaA = a.fecha_creacion ? new Date(a.fecha_creacion) : new Date(0);
    const fechaB = b.fecha_creacion ? new Date(b.fecha_creacion) : new Date(0);
    return fechaB - fechaA; // Orden descendente (más nuevo primero)
  });



  return (
    <div className="vista-expediente-contenedor">
      <button onClick={onVolver} className="boton-volver">&larr; Volver al Dashboard</button>
      
      <h2>Detalle del Expediente #{expediente.id}</h2>
      
      <div className="expediente-metadata">
        <p><strong>Fecha de Creación:</strong> {new Date(expediente.fecha_creacion).toLocaleString('es-CO')}</p>
        <p><strong>Estado:</strong> <span className={`estado-caso estado-${expediente.estado.replace('_', '-')}`}>{expediente.estado.replace('_', ' ')}</span></p>
      </div>

      <div className="expediente-seccion">
        <h3>Descripción de los Hechos</h3>
        <p>{expediente.descripcion_hechos}</p>
      </div>

      {/* --- INICIO DE LA MODIFICACION: Nueva sección de Línea de Tiempo y Formularios --- */}
      <div className="expediente-seccion">
        <h3>Línea de Tiempo del Expediente</h3>
        <div className="linea-de-tiempo-contenedor">
          {lineaDeTiempo.length > 0 ? (
            lineaDeTiempo.map((item, index) => (
              <div key={`${item.tipo}-${item.id || index}`} className="linea-de-tiempo-item">
                {/* Renderizado para un DOCUMENTO */}
                {item.tipo === 'documento' && (
                  <>
                    <span className="icono">📄</span>
                    <div className="contenido">
                      <p><strong>Documento añadido:</strong> <a href={`${baseURL}${item.ruta_archivo}`} target="_blank" rel="noopener noreferrer">{item.nombre_archivo}</a></p>
                      {/* Aquí podríamos mostrar la fecha si la tuviéramos disponible en el objeto 'evidencia' */}
                      {/* <small>Subido por: [Nombre del autor]</small> */}
                    </div>
                  </>
                )}
                {/* Renderizado para una NOTA */}
                {item.tipo === 'nota' && (
                  <>
                    <span className="icono">📝</span>
                    <div className="contenido">
                      <p>{item.contenido}</p>
                      <small>Nota añadida el {new Date(item.fecha_creacion).toLocaleString('es-CO')}</small>
                      {/* <small> por [Nombre del autor]</small> */}
                    </div>
                  </>
                )}
              </div>
            ))
          ) : <p>No hay documentos ni notas en este expediente.</p>}
        </div>

        {/* Contenedor para los formularios de acción */}
        <div className="formularios-accion-contenedor">
          {/* Formulario para subir documentos */}
          <form onSubmit={handleSubirDocumento} className="formulario-accion">
            <h4>Añadir Documento</h4>
            <input 
              type="file" 
              onChange={(e) => setArchivoASubir(e.target.files[0])}
              disabled={cargandoSubida}
            />
            <button type="submit" disabled={cargandoSubida}>
              {cargandoSubida ? 'Subiendo...' : 'Subir Archivo'}
            </button>
            {errorSubida && <p className="error-texto">{errorSubida}</p>}
          </form>

          {/* Formulario para crear notas */}
          <form onSubmit={handleCrearNota} className="formulario-accion">
            <h4>Añadir Nota</h4>
            <textarea 
              value={nuevaNota} 
              onChange={(e) => setNuevaNota(e.target.value)} 
              placeholder="Escriba su nota de seguimiento aquí..." 
              disabled={cargandoNota} 
            />
            <button type="submit" disabled={cargandoNota}>
              {cargandoNota ? 'Guardando...' : 'Guardar Nota'}
            </button>
            {errorNota && <p className="error-texto">{errorNota}</p>}
          </form>
        </div>
      </div>
      {/* --- FIN DE LA MODIFICACION --- */}

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
              <p>{respuestaAgente.contenido}</p>
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