import React, { useState, useEffect } from 'react';
import './VistaDetalleCaso.css';
import FormularioSubirEvidencia from '../FormularioSubirEvidencia/FormularioSubirEvidencia';
import { subirEvidencia, obtenerEstadoEvidencia } from '../../servicios/api';

// 1. IMPORTAMOS NUESTRO NUEVO COMPONENTE
import ReporteAdmision from '../ReporteAdmision/ReporteAdmision';

const VistaDetalleCaso = ({ casoSeleccionado, onEvidenciaSubida, onAnalisisCompleto }) => {
  const [idEvidenciaEnSondeo, setIdEvidenciaEnSondeo] = useState(null);
  const [estaProcesando, setEstaProcesando] = useState(false);

  // --- El resto de tus funciones (manejarSubidaDeArchivo, useEffect) se mantienen exactamente igual ---
  const manejarSubidaDeArchivo = async (archivo) => {
    if (!casoSeleccionado) return;
    setEstaProcesando(true);
    try {
      const casoActualizado = await subirEvidencia(casoSeleccionado.id_caso, archivo);
      const nuevaEvidencia = casoActualizado.evidencias[casoActualizado.evidencias.length - 1];
      onEvidenciaSubida(casoActualizado);
      setIdEvidenciaEnSondeo(nuevaEvidencia.id_evidencia);
    } catch (error) {
      console.error("Error en el proceso de subida:", error);
      setEstaProcesando(false);
    }
  };

  useEffect(() => {
    if (!idEvidenciaEnSondeo) return;
    const intervalo = setInterval(async () => {
      const respuesta = await obtenerEstadoEvidencia(idEvidenciaEnSondeo);
      const estadoActual = respuesta.estado_procesamiento;
      if (estadoActual === 'completado' || estadoActual.includes('error')) {
        clearInterval(intervalo);
        console.log("ANÁLISIS COMPLETO: Avisando al componente App para que refresque los datos.");
        onAnalisisCompleto();
        setIdEvidenciaEnSondeo(null);
        setEstaProcesando(false);
      }
    }, 5000);
    return () => clearInterval(intervalo);
  }, [idEvidenciaEnSondeo, onAnalisisCompleto]);


  if (!casoSeleccionado) {
    return <div className="vista-detalle-contenedor placeholder"><p>Selecciona un caso...</p></div>;
  }

  return (
    <div className="vista-detalle-contenedor">
      <h2>Detalle del Caso: {casoSeleccionado.titulo}</h2>
      <p><strong>Resumen:</strong> {casoSeleccionado.resumen || 'No proporcionado'}</p>
      <p><strong>ID:</strong> {casoSeleccionado.id_caso}</p>
      
      <hr />

      <FormularioSubirEvidencia 
        onArchivoSeleccionado={manejarSubidaDeArchivo}
        estaProcesando={estaProcesando}
      />

      <h3>Evidencias ({casoSeleccionado.evidencias.length})</h3>
      {casoSeleccionado.evidencias.map(evidencia => (
        <div key={evidencia.id_evidencia} className="evidencia-card">
          <h4>Archivo: {evidencia.nombre_archivo}</h4>
          <p><strong>Estado:</strong> {evidencia.estado_procesamiento}</p>
          
          {estaProcesando && idEvidenciaEnSondeo === evidencia.id_evidencia && (
            <p className="procesando-indicador"><strong>(Procesando en segundo plano...)</strong></p>
          )}

          {/* --- 2. AQUÍ ESTÁ LA NUEVA LÓGICA DE VISUALIZACIÓN --- */}
          {evidencia.texto_extraido && (
            <div className="detalle-seccion">
              {/*
                Verificamos si el texto_extraido es uno de nuestros reportes.
                Si lo es, usamos el componente especializado ReporteAdmision.
                Si no lo es, mostramos el texto plano como antes (<pre>).
              */}
              {evidencia.texto_extraido.includes("--- REPORTE DE ADMISIÓN AUTOMÁTICA ---") ? (
                <ReporteAdmision reporteTexto={evidencia.texto_extraido} />
              ) : (
                <>
                  <h5>Resultado del Análisis</h5>
                  <pre>{evidencia.texto_extraido}</pre>
                </>
              )}
            </div>
          )}

          {/* El resto de los campos (entidades, borrador, etc.) no son generados
              por nuestra nueva cadena de agentes, así que podemos ocultarlos
              o eliminarlos por ahora para mantener la interfaz limpia.
              En este caso, los voy a comentar para que los tengas de referencia. */}
          
          {/*
          {evidencia.entidades_extraidas?.length > 0 && ( ... )}
          {evidencia.informacion_recuperada?.length > 0 && ( ... )}
          {evidencia.borrador_estrategia && ( ... )}
          {evidencia.verificacion_calidad && ( ... )}
          */}
        </div>
      ))}
    </div>
  );
};

export default VistaDetalleCaso;