// frontend/src/componentes/VistaChat/useChatLogic.js

/**
 * Docstring:
 * Este es un Hook personalizado que encapsula toda la logica de negocio
 * y manejo de estado para el componente VistaChat.
 *
 * Args:
 *   props (object): Las props iniciales pasadas desde App.jsx, como
 *                   agenteInicial, casoIdActual, y las funciones callback.
 *
 * Returns:
 *   (object): Un objeto que contiene todas las variables de estado y
 *             funciones que el componente de UI (VistaChat.jsx) necesita
 *             para renderizarse y funcionar.
 */
import { useState, useEffect, useRef } from 'react';
import { chatearConAgente, crearNuevoCaso, subirEvidencia, analizarCaso } from '../../../servicios/api/ciudadano';


export const useChatLogic = ({ agenteInicial, casoIdActual, onCasoCreado, onTriajeTerminado, onIniciarTriaje }) => {

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
      const respuestaAgente = await chatearConAgente(textoAEnviar);
      setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: respuestaAgente.texto }]);
      if (respuestaAgente.iniciarTriaje) {
          onIniciarTriaje();
      }
    } else if (modoAgente === 'triaje_descripcion') {
      try {
        const casoCreado = await crearNuevoCaso({ descripcion_hechos: textoAEnviar, id_usuario: 1 });
        onCasoCreado(casoCreado.id);
      } catch (error) { 
        console.error("Error al crear el caso:", error);
        setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: 'Hubo un error al crear tu caso. Por favor, intenta de nuevo.' }]);
      }
    } else if (modoAgente === 'triaje_evidencias') {
      try {
        if (archivosParaSubir.length > 0) {
          await Promise.all(archivosParaSubir.map(archivo => subirEvidencia(casoIdActual, archivo)));
          setArchivosParaSubir([]);
          setAudioUrl(null);
        }
        
        const resultadoAnalisis = await analizarCaso(casoIdActual, textoAEnviar);
        const esAdmisible = resultadoAnalisis?.resultado_triaje?.admisible;
        
        if (esAdmisible === false) {
            
            const justificacionBackend = resultadoAnalisis?.resultado_triaje?.justificacion || "No se proporcionó una justificación.";
           
            
            const mensajeRechazo = { autor: 'agente', texto: justificacionBackend };
            const mensajeGuia = { autor: 'agente', texto: 'Si tiene alguna otra pregunta general sobre el consultorio, no dude en consultarme.' };

            setMensajes(anteriores => [...anteriores, mensajeRechazo, mensajeGuia]);
            setTriajeFinalizado(true);
            onTriajeTerminado(false);
        } else {
            const preguntaDelAgente = resultadoAnalisis.resultado_triaje.pregunta_para_usuario;
            
            if (preguntaDelAgente) {
                setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: preguntaDelAgente }]);
            } else {
                onTriajeTerminado(true);
            }
        }
      } catch (error) { 
        console.error("Error en el proceso de evidencia:", error);
        setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: 'Ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo.' }]);
      }
    }
    setEstaProcesando(false);
  };
  
  const manejarClickSugerencia = (texto) => { manejarEnvioUnificado(texto); };



   /**
   * Elimina un archivo de la lista de archivos para subir.
   * @param {number} indiceAEliminar - El índice del archivo a eliminar en el array 'archivosParaSubir'.
   */
  const manejarEliminarArchivo = (indiceAEliminar) => {
    // Si el archivo a eliminar es un audio grabado, también limpiamos la URL del audio.
    const archivo = archivosParaSubir[indiceAEliminar];
    if (archivo.name.startsWith('grabacion-') && audioUrl) {
      setAudioUrl(null);
    }
    
    setArchivosParaSubir(anteriores => 
      anteriores.filter((_, indice) => indice !== indiceAEliminar)
    );
  };


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
    if (triajeFinalizado) return "El proceso ha finalizado. Puede hacer otra pregunta general.";
    return "";
  };

  return {
    mensajes,
    entradaUsuario,
    setEntradaUsuario,
    estaProcesando,
    mostrarSugerencias,
    modoAgente,
    archivosParaSubir,
    setArchivosParaSubir,
    grabando,
    audioUrl,
    triajeFinalizado,
    finalDeMensajesRef,
    textareaRef,
    manejarEnvioUnificado,
    manejarClickSugerencia,
    manejarEliminarArchivo,
    iniciarGrabacion,
    detenerGrabacion,
    obtenerPlaceholder
  };
};