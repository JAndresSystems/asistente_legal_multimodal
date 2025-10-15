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

// ==============================================================================
// INICIO DE LA MODIFICACION: SubidorDeEvidencias ahora es un componente "tonto"
// ==============================================================================
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
      {/* EL BOTON DE ENVIO HA SIDO ELIMINADO DE AQUI */}
    </div>
  );
};
// ==============================================================================
// FIN DE LA MODIFICACION
// ==============================================================================


function VistaChat({ agenteInicial, casoIdActual, onIniciarTriaje, onCasoCreado, onSubidaCompletada }) {
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy el Asistente Legal virtual. Estoy aquí para resolver tus dudas sobre el Consultorio Jurídico.' }
  ]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaProcesando, setEstaProcesando] = useState(false);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(true);
  const [modoAgente, setModoAgente] = useState(agenteInicial);
  
  // ==================================================================
  // INICIO DE LA MODIFICACION: El estado de los archivos se mueve aqui
  // ==================================================================
  const [archivosParaSubir, setArchivosParaSubir] = useState([]);
  const [grabando, setGrabando] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksDeAudioRef = useRef([]);
  // ==================================================================
  // FIN DE LA MODIFICACION
  // ==================================================================

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
      }
      if (agenteInicial === 'triaje_evidencias') {
        const nuevoMensaje = { autor: 'agente', texto: 'Perfecto, tu caso ha sido creado. Ahora, por favor, adjunta todos los archivos de evidencia que tengas (documentos, imágenes) o graba un audio con tu narración.' };
        setMensajes(anteriores => [...anteriores, nuevoMensaje]);
      }
    }
  }, [agenteInicial, modoAgente]);

  const manejarRespuestaDeAgenteTriaje = (nuevoMensaje) => {
    setMensajes(anteriores => [...anteriores, nuevoMensaje]);
  };

  // ==============================================================================
  // INICIO DE LA MODIFICACION: Logica de envio ahora es unificada
  // ==============================================================================
   const manejarEnvioUnificado = async (textoOpcional = null) => {
    // Si la funcion es llamada desde un click de sugerencia, usa ese texto.
    // Si no, usa el texto del estado 'entradaUsuario'.
    const textoAEnviar = (textoOpcional !== null ? textoOpcional : entradaUsuario).trim();

    if (!textoAEnviar && archivosParaSubir.length === 0) return;

    if (mostrarSugerencias) {
      setMostrarSugerencias(false); // Corregimos la advertencia de variable no usada
    }

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
        const preguntaDelAgente = resultadoAnalisis?.resultado_triaje?.pregunta_para_usuario;
        if (preguntaDelAgente) {
          manejarRespuestaDeAgenteTriaje({ autor: 'agente', texto: preguntaDelAgente });
        } else {
          onSubidaCompletada();
        }
      } catch (error) { console.error("Error en el proceso de evidencia:", error);}
    }
    
    setEstaProcesando(false);
  };
  
  const manejarEnvioFormulario = (e) => { e.preventDefault(); manejarEnvioUnificado(); };
  const manejarClickSugerencia = (texto) => { manejarEnvioUnificado(texto); };

  // Logica de grabacion ahora vive aqui, en el componente padre
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
  // ==============================================================================
  // FIN DE LA MODIFICACION
  // ==============================================================================

  const obtenerPlaceholder = () => {
    if (modoAgente === 'recepcionista') return "Escribe tu pregunta aqui...";
    if (modoAgente === 'triaje_descripcion') return "Describe los hechos de tu caso aqui...";
    if (modoAgente === 'triaje_evidencias') return "Responde al agente o adjunta mas archivos y presiona Enviar...";
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
        {modoAgente === 'triaje_evidencias' && (
          <SubidorDeEvidencias 
            archivos={archivosParaSubir}
            onSeleccionArchivos={(e) => setArchivosParaSubir(prev => [...prev, ...Array.from(e.target.files)])}
            onIniciarGrabacion={iniciarGrabacion}
            onDetenerGrabacion={detenerGrabacion}
            grabando={grabando}
            audioUrl={audioUrl}
          />
        )}

        <form className="formulario-chat" onSubmit={manejarEnvioFormulario}>
          <textarea
            ref={textareaRef}
            value={entradaUsuario}
            onChange={(e) => setEntradaUsuario(e.target.value)}
            placeholder={obtenerPlaceholder()}
            disabled={estaProcesando}
            rows={1}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); manejarEnvioFormulario(e); } }}
          />
          <button type="submit" disabled={estaProcesando}>Enviar</button>
        </form>

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