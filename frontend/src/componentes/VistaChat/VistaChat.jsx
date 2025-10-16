// frontend/src/componentes/VistaChat/VistaChat.jsx

import React, { useState, useEffect, useRef } from 'react';
import { chatearConAgente, crearNuevoCaso, subirEvidencia, analizarCaso } from '../../servicios/api';
import './VistaChat.css';


const Sugerencias = ({ onSugerenciaClick }) => (
  <div className="contenedor-sugerencias">
    <button onClick={() => onSugerenciaClick("¿Qué servicios ofrecen?")} className="boton-sugerencia">¿Qué servicios ofrecen?</button>
    <button onClick={() => onSugerenciaClick("¿Tiene algún costo?")} className="boton-sugerencia">¿Tiene algún costo?</button>
    <button onClick={() => onSugerenciaClick("¿Cuál es el horario?")} className="boton-sugerencia">¿Cuál es el horario?</button>
  </div>
);

const SubidorDeEvidencias = ({ 
  archivos, 
  onSeleccionArchivos, 
  onIniciarGrabacion, 
  onDetenerGrabacion, 
  grabando, 
  audioUrl 
}) => {
  return (
    <div className="area-subida-evidencias">
      <div className="lista-archivos-para-subir">
        {archivos.length > 0 ? (
          archivos.map((archivo, i) => <div key={i} className="archivo-item">{archivo.name}</div>)
        ) : ( <p>Adjunta archivos o graba un audio si es necesario.</p> )}
      </div>
      {audioUrl && ( <div className="reproductor-audio-chat"><audio src={audioUrl} controls /></div> )}
      <div className="botones-evidencia-contenedor">
        <input type="file" id="seleccion-archivo-chat" multiple onChange={onSeleccionArchivos} style={{ display: 'none' }} />
        <label htmlFor="seleccion-archivo-chat" className="boton-accion-evidencia">Adjuntar Archivo</label>
        {!grabando ? (
            <button onClick={onIniciarGrabacion} className="boton-accion-evidencia">Grabar Audio</button>
        ) : (
            <button onClick={onDetenerGrabacion} className="boton-accion-evidencia detener">Detener</button>
        )}
      </div>
    </div>
  );
};

function VistaChat({ agenteInicial, casoIdActual, onIniciarTriaje, onCasoCreado, onTriajeTerminado }) {
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy el Asistente Legal virtual. Estoy aquí para resolver tus dudas sobre el Consultorio Jurídico.' }
  ]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaProcesando, setEstaProcesando] = useState(false);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(true);
  const [modoAgente, setModoAgente] = useState(agenteInicial);
  const [archivosParaSubir, setArchivosParaSubir] = useState([]);
  const [grabando, setGrabando] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksDeAudioRef = useRef([]);
  const [triajeFinalizado, setTriajeFinalizado] = useState(false);

  const finalDeMensajesRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    finalDeMensajesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      const nuevaAltura = Math.min(textarea.scrollHeight, 150);
      textarea.style.height = `${nuevaAltura}px`;
      textarea.style.overflowY = textarea.scrollHeight > 150 ? 'auto' : 'hidden';
    }
  }, [entradaUsuario]);

  useEffect(() => {
    if (agenteInicial !== modoAgente) {
      setModoAgente(agenteInicial);
      
      if (agenteInicial === 'triaje_descripcion') {
        const nuevoMensaje = { autor: 'agente', texto: 'Entendido. Para iniciar el registro, por favor describe de la forma más detallada posible los hechos de tu caso en un solo mensaje.' };
        setMensajes(anteriores => [...anteriores, nuevoMensaje]);
      } else if (agenteInicial === 'triaje_evidencias') {
        const nuevoMensaje = { autor: 'agente', texto: 'Perfecto, tu caso ha sido creado. Ahora, por favor, adjunta todos los archivos de evidencia que tengas (documentos, imágenes) o graba un audio con tu narración.' };
        setMensajes(anteriores => [...anteriores, nuevoMensaje]);
      
      } else if (agenteInicial === 'recepcionista') {
        const nuevoMensaje = { autor: 'agente', texto: 'Si tiene alguna otra pregunta general sobre el consultorio, no dude en consultarme.' };
        setMensajes(anteriores => [...anteriores, nuevoMensaje]);
        setTriajeFinalizado(false);
        setMostrarSugerencias(true);
      }
    }
  }, [agenteInicial, modoAgente]);

   const manejarEnvioUnificado = async (textoOpcional = null) => {
    const textoAEnviar = (textoOpcional !== null ? textoOpcional : entradaUsuario).trim();
    if (!textoAEnviar && archivosParaSubir.length === 0) return;

    if (mostrarSugerencias) setMostrarSugerencias(false);

    setEstaProcesando(true);
    
    if (textoAEnviar) {
      setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: textoAEnviar }]);
    }
    if (archivosParaSubir.length > 0) {
      const nombres = archivosParaSubir.map(f => f.name).join(', ');
      setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: `(Adjuntando archivo(s): ${nombres})` }]);
    }
    
    setEntradaUsuario('');

    if (modoAgente === 'recepcionista') {
      const textoRespuesta = await chatearConAgente(textoAEnviar);
      setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: textoRespuesta }]);
    } else if (modoAgente === 'triaje_descripcion') {
      try {
        const casoCreado = await crearNuevoCaso({ descripcion_hechos: textoAEnviar, id_usuario: 1 });
        onCasoCreado(casoCreado.id);
      } catch (error) { console.log("Error al crear el caso:", error); }
    } else if (modoAgente === 'triaje_evidencias') {
      try {
        if (archivosParaSubir.length > 0) {
          await Promise.all(archivosParaSubir.map(archivo => subirEvidencia(casoIdActual, archivo)));
          setArchivosParaSubir([]);
          setAudioUrl(null);
        }
        
        const resultadoAnalisis = await analizarCaso(casoIdActual, textoAEnviar);
        
        // ==============================================================================
        // INICIO DE LA MODIFICACION FINAL Y DEFINITIVA
        // ==============================================================================
        
        // 1. La única fuente de verdad sobre la admisibilidad.
        const esAdmisible = resultadoAnalisis?.resultado_triaje?.admisible;

        // 2. Lógica para casos NO ADMISIBLES.
        if (esAdmisible === false) {
            const justificacion = resultadoAnalisis.resultado_triaje.justificacion || "No se proporcionó una justificación.";
            const mensajeRechazo = `Hemos evaluado la informacion de su caso y, lamentablemente, no cumple con los criterios de competencia definidos para nuestro consultorio juridico por la siguiente razon: '${justificacion}'. Le agradecemos su tiempo y por contactarnos.`;
            
            setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: mensajeRechazo }]);
            setTriajeFinalizado(true);
            onTriajeTerminado(false);

        // 3. Lógica para casos ADMISIBLES.
        } else {
            const pregunta = resultadoAnalisis.resultado_triaje.pregunta_para_usuario;
            // Si hay una pregunta, significa que se necesita más información.
            if (pregunta) {
                setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: pregunta }]);
            // Si no hay pregunta, el triaje fue exitoso y se puede continuar.
            } else {
                onTriajeTerminado(true);
            }
        }
        // ==============================================================================
        // FIN DE LA MODIFICACION FINAL Y DEFINITIVA
        // ==============================================================================

      } catch (error) { 
        console.error("Error en el proceso de evidencia:", error);
        setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: 'Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo.' }]);
      }
    }
    
    setEstaProcesando(false);
  };
  
  const manejarEnvioFormulario = (e) => { e.preventDefault(); manejarEnvioUnificado(); };
  const manejarClickSugerencia = (texto) => { manejarEnvioUnificado(texto); };

  const iniciarGrabacion = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorderRef.current = new MediaRecorder(stream);
        mediaRecorderRef.current.ondataavailable = (evento) => { chunksDeAudioRef.current.push(evento.data); };
        mediaRecorderRef.current.onstop = () => {
            const audioBlob = new Blob(chunksDeAudioRef.current, { type: 'audio/mpeg' });
            const url = URL.createObjectURL(audioBlob);
            setAudioUrl(url);
            const fecha = new Date();
            const nombreArchivo = `grabacion-${fecha.getFullYear()}-${fecha.getMonth()+1}-${fecha.getDate()}.mp3`;
            const archivoDeAudio = new File([audioBlob], nombreArchivo, { type: 'audio/mpeg' });
            setArchivosParaSubir(anteriores => [...anteriores, archivoDeAudio]);
            chunksDeAudioRef.current = [];
        };
        chunksDeAudioRef.current = [];
        mediaRecorderRef.current.start();
        setGrabando(true);
        setAudioUrl(null);
    } catch (error) {
        console.error("Error al acceder al microfono:", error);
        alert("No se pudo acceder al microfono.");
    }
  };

  const detenerGrabacion = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setGrabando(false);
    }
  };

  const obtenerPlaceholder = () => {
    if (modoAgente === 'recepcionista') return "Escribe tu pregunta aqui...";
    if (modoAgente === 'triaje_descripcion') return "Describe los hechos de tu caso aqui...";
    if (modoAgente === 'triaje_evidencias' && !triajeFinalizado) return "Responde al agente o adjunta mas archivos y presiona Enviar...";
    if (triajeFinalizado) return "El proceso ha finalizado.";
    return "";
  };

  return (
    <div className="contenedor-chat">
      <div className="historial-mensajes">
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            <p>{mensaje.texto}</p>
          </div>
        ))}
        {modoAgente === 'recepcionista' && mostrarSugerencias && <Sugerencias onSugerenciaClick={manejarClickSugerencia} />}
        {estaProcesando && <div className="mensaje agente"><p>...</p></div>}
        <div ref={finalDeMensajesRef} />
      </div>

      <div className="area-acciones-chat">
        {modoAgente === 'triaje_evidencias' && !triajeFinalizado && (
          <SubidorDeEvidencias 
            archivos={archivosParaSubir}
            onSeleccionArchivos={(e) => setArchivosParaSubir(prev => [...prev, ...Array.from(e.target.files)])}
            onIniciarGrabacion={iniciarGrabacion}
            onDetenerGrabacion={detenerGrabacion}
            grabando={grabando}
            audioUrl={audioUrl}
          />
        )}

        {(modoAgente !== 'triaje_evidencias' || !triajeFinalizado) && (
            <form className="formulario-chat" onSubmit={manejarEnvioFormulario}>
            <textarea
                ref={textareaRef}
                value={entradaUsuario}
                onChange={(e) => setEntradaUsuario(e.target.value)}
                placeholder={obtenerPlaceholder()}
                disabled={estaProcesando || triajeFinalizado}
                rows={1}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); manejarEnvioFormulario(e); } }}
            />
            <button type="submit" disabled={estaProcesando || triajeFinalizado}>Enviar</button>
            </form>
        )}
        
        {modoAgente === 'recepcionista' && (
          <div className="contenedor-iniciar-caso">
            <button onClick={onIniciarTriaje} className="boton-principal-iniciar">Tengo un caso y quiero registrarlo</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default VistaChat;