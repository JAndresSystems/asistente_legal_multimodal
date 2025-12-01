// frontend/src/componentes/VistaChat/useChatLogic.js

import { useState, useEffect, useRef } from 'react';
import { chatearConAgente, subirEvidencia, analizarCaso } from '../../../servicios/api/ciudadano';

// (MODIFICACIÓN CLAVE) La función 'limpiarYParsearJSON' ya no es necesaria y se elimina.

export const useChatLogic = ({ agenteInicial, casoIdActual, onCasoCreado, onTriajeTerminado }) => {
  // ... (el resto del hook hasta manejarEnvioUnificado no cambia)
  const obtenerMensajeInicial = (agente) => {
    if (agente === 'triaje_descripcion') {
      return { autor: 'agente', texto: 'He creado un borrador para su caso. Para continuar, por favor describa de la forma más detallada posible los hechos en un solo mensaje.' };
    }
    return { autor: 'agente', texto: '¡Hola! Soy el Asistente Legal virtual. Estoy aquí para resolver tus dudas sobre el Consultorio Jurídico.' };
  };
  const [mensajes, setMensajes] = useState([obtenerMensajeInicial(agenteInicial)]);
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
  const [mostrarBotonInforme, setMostrarBotonInforme] = useState(false);
  const finalDeMensajesRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => { finalDeMensajesRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [mensajes]);
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
      // if (agenteInicial === 'triaje_evidencias') {
      //   const nuevoMensaje = { autor: 'agente', texto: 'He recibido la descripción de su caso. Ahora, por favor, adjunte todos los archivos de evidencia que tenga (documentos, imágenes) o grabe un audio con su narración.' };
      //   setMensajes(anteriores => [...anteriores, nuevoMensaje]);
      // } elseif...
       if (agenteInicial === 'recepcionista') {
        setTriajeFinalizado(false);
        setMostrarSugerencias(true);
      }
    }
  }, [agenteInicial, modoAgente]);

  const manejarEnvioUnificado = async (textoOpcional = null) => {
    const textoAEnviar = (textoOpcional !== null ? textoOpcional : entradaUsuario).trim();
    if (!textoAEnviar && archivosParaSubir.length === 0) return;
    if (modoAgente === 'triaje_descripcion' && textoAEnviar.length < 20) {
        setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: textoAEnviar }, { autor: 'agente', texto: 'Por favor, describe tu caso con más detalle para poder ayudarte mejor. Una buena descripción es fundamental.' }]);
        setEntradaUsuario('');
        return;
    }
    if (mostrarSugerencias) setMostrarSugerencias(false);
    setEstaProcesando(true);
    if (textoAEnviar) { setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: textoAEnviar }]); }
    if (archivosParaSubir.length > 0) { const nombres = archivosParaSubir.map(f => f.name).join(', '); setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: `(Adjuntando archivo(s): ${nombres})` }]);}
    setEntradaUsuario('');

    try {
      if (modoAgente === 'recepcionista') {
        const historialParaEnviar = mensajes.slice(0, -1);
        const respuestaDelApi = await chatearConAgente(textoAEnviar, historialParaEnviar);
        
        // --- INICIO DE LA CORRECCIÓN CLAVE ---
        // El backend ahora devuelve un objeto plano. Ya no necesitamos acceder a ".respuesta_agente".
        // La propia 'respuestaDelApi' es el objeto que contiene el texto y la bandera de triaje.
        const textoRespuesta = respuestaDelApi.respuesta_texto;
        setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: textoRespuesta }]);
        
        if (respuestaDelApi.iniciar_triaje) {
            const mensajeGuia = { autor: 'agente', texto: "Para continuar, por favor utilice el botón 'Registrar Nuevo Caso' en el panel." };
            setMensajes(anteriores => [...anteriores, mensajeGuia]);
        }
        // --- FIN DE LA CORRECCIÓN CLAVE ---
      
      } else if (modoAgente === 'triaje_descripcion') {
        const resultadoDelPaso = await analizarCaso(casoIdActual, textoAEnviar);
        if (resultadoDelPaso.respuesta_para_usuario) { setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: resultadoDelPaso.respuesta_para_usuario }]); }
        onCasoCreado(casoIdActual);
      
      } else if (modoAgente === 'triaje_evidencias') {
        if (archivosParaSubir.length > 0) {
          await Promise.all(archivosParaSubir.map(archivo => subirEvidencia(casoIdActual, archivo)));
          setArchivosParaSubir([]);
          setAudioUrl(null);
        }
        const resultadoDelPaso = await analizarCaso(casoIdActual, textoAEnviar);
        if (resultadoDelPaso.respuesta_para_usuario) { setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: resultadoDelPaso.respuesta_para_usuario }]); }
        const flujoTerminado = resultadoDelPaso.flujo_terminado || false;
        if (flujoTerminado) {
            setTriajeFinalizado(true);
            const casoFueAdmitido = resultadoDelPaso.caso_admitido || false;
            onTriajeTerminado(casoFueAdmitido);
            if (casoFueAdmitido) {
                setMostrarBotonInforme(true);
            } else {
                // Si fue rechazado, añadimos un mensaje guía general.
                const mensajeGuia = { autor: 'agente', texto: "Puede volver a su panel o iniciar un nuevo registro si lo desea." };
                setMensajes(anteriores => [...anteriores, mensajeGuia]);
            }
            // --- FIN DE LA CORRECCIÓN CLAVE 2 ---
        }
      }
    } catch (error) { 
      console.error("Error en el proceso de chat unificado:", error);
      const mensajeError = { autor: 'agente', texto: 'Lo siento, ocurrió un error inesperado al procesar tu solicitud. Por favor, intenta de nuevo.' };
      setMensajes(anteriores => [...anteriores, mensajeError]);
    }
    
    setEstaProcesando(false);
  };
  
  // El resto del archivo (manejarClickSugerencia, manejarEliminarArchivo, grabación, etc.)
  // no necesita cambios y permanece exactamente igual.
  
  const manejarClickSugerencia = (texto) => { manejarEnvioUnificado(texto); };
  const manejarEliminarArchivo = (indiceAEliminar) => {
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
    mostrarBotonInforme,
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