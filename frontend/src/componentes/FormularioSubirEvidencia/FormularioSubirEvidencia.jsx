// frontend/src/componentes/FormularioSubirEvidencia/FormularioSubirEvidencia.jsx

import React, { useState, useRef } from 'react';
import { subirEvidencia } from '../../servicios/api';
import './FormularioSubirEvidencia.css';

function FormularioSubirEvidencia({ casoId, onSubidaCompletada }) {
  const inputArchivoRef = useRef(null);
  const [archivosSeleccionados, setArchivosSeleccionados] = useState([]);
  const [estaSubiendo, setEstaSubiendo] = useState(false);
  const [progreso, setProgreso] = useState({ actual: 0, total: 0 });
  const [mensaje, setMensaje] = useState('');

  // Estados y Referencias para la grabacion de audio
  const [grabando, setGrabando] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksDeAudioRef = useRef([]);

  const manejarClickZona = () => inputArchivoRef.current.click();

  const manejarSeleccionArchivos = (evento) => {
    setArchivosSeleccionados(prev => [...prev, ...Array.from(evento.target.files)]);
  };

  const manejarEliminarArchivo = (indiceAEliminar) => {
    setArchivosSeleccionados(prev => prev.filter((_, indice) => indice !== indiceAEliminar));
  };

  const manejarSubida = async () => {
    setEstaSubiendo(true);
    setMensaje('Iniciando subida...');
    setProgreso({ actual: 0, total: archivosSeleccionados.length });

    for (let i = 0; i < archivosSeleccionados.length; i++) {
      const archivo = archivosSeleccionados[i];
      setProgreso(prev => ({ ...prev, actual: i + 1 }));
      setMensaje(`Subiendo archivo ${i + 1} de ${archivosSeleccionados.length}: ${archivo.name}`);
      
      try {
        await subirEvidencia(casoId, archivo);
      } catch (error) {
        setMensaje(`Error al subir ${archivo.name}. Por favor, intentalo de nuevo.`);
        console.error("Error en subida de archivo:", error);
        setEstaSubiendo(false);
        return;
      }
    }
    setMensaje('¡Todas las evidencias se han subido correctamente!');
    onSubidaCompletada();
  };

  // Logica para la grabacion de audio
  const iniciarGrabacion = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        
        mediaRecorderRef.current.ondataavailable = (evento) => {
            chunksDeAudioRef.current.push(evento.data);
        };
        
        mediaRecorderRef.current.onstop = () => {
            // ==================================================================
            // INICIO DE LA CORRECCION (BACKEND ERROR)
            // Cambiamos el tipo a 'audio/mpeg' para mejorar compatibilidad con Gemini.
            // ==================================================================
            const audioBlob = new Blob(chunksDeAudioRef.current, { type: 'audio/mpeg' });
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
            
            const fecha = new Date();
            // Cambiamos la extension a .mp3 para que coincida con el tipo MIME.
            const nombreArchivo = `grabacion-${fecha.getFullYear()}-${fecha.getMonth()+1}-${fecha.getDate()}.mp3`;
            const archivoDeAudio = new File([audioBlob], nombreArchivo, { type: 'audio/mpeg' });
            // ==================================================================
            // FIN DE LA CORRECCION
            // ==================================================================
            
            setArchivosSeleccionados(anteriores => [...anteriores, archivoDeAudio]);
            chunksDeAudioRef.current = [];
        };
        
        chunksDeAudioRef.current = [];
        mediaRecorderRef.current.start();
        setGrabando(true);
        setAudioUrl(null);

    } catch (error) {
        console.error("Error al acceder al microfono:", error);
        alert("No se pudo acceder al microfono. Por favor, verifica los permisos en tu navegador.");
    }
  };

  const detenerGrabacion = () => {
    mediaRecorderRef.current.stop();
    setGrabando(false);
  };

  // ==============================================================================
  // INICIO DE LA CORRECCION (FRONTEND LAYOUT)
  // Restauramos la estructura y nombres de clases CSS originales.
  // ==============================================================================
  return (
    <div className="formulario-subir-evidencia-contenedor">
      <h3>Paso 3: Adjuntar Evidencias para el Caso #{casoId}</h3>

      <input
        type="file"
        multiple
        ref={inputArchivoRef}
        onChange={manejarSeleccionArchivos}
        className="input-oculto"
      />

      <div className="zona-seleccion-archivo" onClick={manejarClickZona}>
        <p>Arrastra tus archivos aquí o haz clic para seleccionarlos</p>
        <small>(PDF, JPG, PNG, MP3, WAV, etc.)</small>
      </div>

      {/* --- NUEVA SECCION DE GRABACION --- */}
      <div className="area-de-grabacion">
        <p className="texto-grabacion">O si prefieres, puedes grabar tu narracion de los hechos:</p>
        {!grabando ? (
            <button onClick={iniciarGrabacion} className="boton-grabar">
                Iniciar Grabacion
            </button>
        ) : (
            <button onClick={detenerGrabacion} className="boton-detener">
                Detener Grabacion
            </button>
        )}
        {audioUrl && (
            <div className="reproductor-audio">
                <p>Grabacion completada. Escuchala y luego presiona "Subir Archivo(s)".</p>
                <audio src={audioUrl} controls />
            </div>
        )}
      </div>

      {archivosSeleccionados.length > 0 && (
        <>
          <h4>Archivos listos para subir:</h4>
          <ul className="lista-archivos-seleccionados">
            {archivosSeleccionados.map((archivo, indice) => (
              <li key={indice} className="item-archivo">
                <span className="nombre-archivo">{archivo.name}</span>
                <button 
                  onClick={() => manejarEliminarArchivo(indice)}
                  className="boton-eliminar-archivo"
                  disabled={estaSubiendo}
                >
                  &times;
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="contenedor-acciones-subida">
        <button 
          onClick={manejarSubida}
          className="boton-subir"
          disabled={estaSubiendo || archivosSeleccionados.length === 0}
        >
          {estaSubiendo ? 'Subiendo...' : `Subir ${archivosSeleccionados.length} Archivo(s)`}
        </button>

        {estaSubiendo && (
          <div className="progreso-subida">
            <div 
              className="barra-progreso" 
              style={{ width: `${(progreso.actual / progreso.total) * 100}%` }}
            ></div>
          </div>
        )}

        {mensaje && <p className="mensaje-feedback">{mensaje}</p>}
      </div>
    </div>
  );
  // ==============================================================================
  // FIN DE LA CORRECCION
  // ==============================================================================
}

export default FormularioSubirEvidencia;