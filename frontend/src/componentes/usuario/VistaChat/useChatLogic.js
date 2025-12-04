import { useState, useEffect, useRef } from 'react';
import { chatearConAgente, subirEvidencia, analizarCaso } from '../../../servicios/api/ciudadano';

export const useChatLogic = ({ agenteInicial, casoIdActual, onCasoCreado, onTriajeTerminado }) => {
  
  // --- Funciones Auxiliares ---
  const obtenerMensajeInicial = (agente) => {
    if (agente === 'triaje_descripcion') {
      return { autor: 'agente', texto: 'He creado un borrador para su caso. Para continuar, por favor describa de la forma más detallada posible los hechos en un solo mensaje.' };
    }
    return { autor: 'agente', texto: '¡Hola! Soy el Asistente Legal virtual. Estoy aquí para resolver tus dudas sobre el Consultorio Jurídico.' };
  };

  // --- Estado del Hook ---
  const [mensajes, setMensajes] = useState([obtenerMensajeInicial(agenteInicial)]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaProcesando, setEstaProcesando] = useState(false);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(true);
  const [modoAgente, setModoAgente] = useState(agenteInicial);
  
  // Estado para archivos y audio
  const [archivosParaSubir, setArchivosParaSubir] = useState([]);
  const [grabando, setGrabando] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksDeAudioRef = useRef([]);

  // Estado de finalización
  const [triajeFinalizado, setTriajeFinalizado] = useState(false);
  
  // Refs para UI
  const finalDeMensajesRef = useRef(null);
  const textareaRef = useRef(null);

  // --- Efectos ---
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
       if (agenteInicial === 'recepcionista') {
        setTriajeFinalizado(false);
        setMostrarSugerencias(true);
      }
    }
  }, [agenteInicial, modoAgente]);

  // --- LÓGICA PRINCIPAL DE ENVÍO ---
  const manejarEnvioUnificado = async (textoOpcional = null) => {
    
    if (triajeFinalizado) return;

    const textoAEnviar = (textoOpcional !== null ? textoOpcional : entradaUsuario).trim();
    
    // Validaciones básicas
    if (!textoAEnviar && archivosParaSubir.length === 0) return;
    
    if (modoAgente === 'triaje_descripcion' && textoAEnviar.length < 20) {
        setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: textoAEnviar }, { autor: 'agente', texto: 'Por favor, describe tu caso con más detalle (mínimo 20 caracteres) para poder ayudarte mejor.' }]);
        setEntradaUsuario('');
        return;
    }

    // Preparar UI para envío
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

    try {
      // 1. MODO RECEPCIONISTA (Chat General)
      if (modoAgente === 'recepcionista') {
        const historialParaEnviar = mensajes.slice(0, -1);
        const respuestaDelApi = await chatearConAgente(textoAEnviar, historialParaEnviar);
        
        setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: respuestaDelApi.respuesta_texto }]);
        
        if (respuestaDelApi.iniciar_triaje) {
            setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: "Para continuar, por favor utilice el botón 'Registrar Nuevo Caso' en el panel." }]);
        }
      
      // 2. MODO TRIAJE: DESCRIPCIÓN INICIAL
      } else if (modoAgente === 'triaje_descripcion') {
        const resultadoDelPaso = await analizarCaso(casoIdActual, textoAEnviar);
        if (resultadoDelPaso.respuesta_para_usuario) { 
            setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: resultadoDelPaso.respuesta_para_usuario }]); 
        }
        // Notificamos al padre que el caso se ha creado/inicializado
        onCasoCreado(casoIdActual);
      
      // 3. MODO TRIAJE: EVIDENCIAS (El Bucle Principal)
      } else if (modoAgente === 'triaje_evidencias') {
        
        // A. Subir archivos primero si existen
        if (archivosParaSubir.length > 0) {
          await Promise.all(archivosParaSubir.map(archivo => subirEvidencia(casoIdActual, archivo)));
          setArchivosParaSubir([]);
          setAudioUrl(null);
        }
        
        // B. Enviar texto y detonar análisis
        const resultadoDelPaso = await analizarCaso(casoIdActual, textoAEnviar);
        const flujoTerminado = resultadoDelPaso.flujo_terminado || false;

        if (flujoTerminado) {
            const casoFueAdmitido = resultadoDelPaso.caso_admitido || false;
            
            if (casoFueAdmitido) {
                // CASO ÉXITO: Bloqueamos el chat y mostramos mensaje final
                const mensajeGuiaFinal = { 
                    autor: 'agente', 
                    texto: '¡Buenas noticias! Hemos reunido toda la información necesaria. Su caso ha sido admitido y asignado a nuestro equipo. El chat ha finalizado. Por favor, utilice el botón a continuación para ver el informe.' 
                };
                setMensajes(anteriores => [...anteriores, mensajeGuiaFinal]);
                setTriajeFinalizado(true); // Esto activará el cambio de UI en VistaChat
            } else {
                // CASO RECHAZO: Mostramos la razón y sugerimos volver
                if (resultadoDelPaso.respuesta_para_usuario) { 
                    setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: resultadoDelPaso.respuesta_para_usuario }]); 
                }
                setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: "Puede volver a su panel principal." }]);
            }
            
            // Notificamos a LayoutUsuario (pero LayoutUsuario NO cambiará la vista si es admisible)
            onTriajeTerminado(casoFueAdmitido);
            
        } else {
            // FLUJO CONTINÚA: Simplemente mostramos la respuesta del agente
            if (resultadoDelPaso.respuesta_para_usuario) {
                setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: resultadoDelPaso.respuesta_para_usuario }]);
            }
        }
      }
    } catch (error) { 
      console.error("Error en useChatLogic:", error);
      setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: 'Ocurrió un error de conexión. Por favor intente nuevamente.' }]);
    }
    
    setEstaProcesando(false);
  };

  // --- Manejadores de UI Auxiliares ---
  const manejarClickSugerencia = (texto) => { manejarEnvioUnificado(texto); };
  
  const manejarEliminarArchivo = (indiceAEliminar) => {
    const archivo = archivosParaSubir[indiceAEliminar];
    if (archivo.name.startsWith('grabacion-') && audioUrl) {
      setAudioUrl(null);
    }
    setArchivosParaSubir(anteriores => anteriores.filter((_, indice) => indice !== indiceAEliminar));
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
        console.error("Error micrófono:", error);
        alert("No se pudo acceder al micrófono.");
    }
  };

  const detenerGrabacion = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setGrabando(false);
    }
  };

  const obtenerPlaceholder = () => {
    if (modoAgente === 'recepcionista') return "Escribe tu pregunta aquí...";
    if (modoAgente === 'triaje_descripcion') return "Describe los hechos detalladamente...";
    if (modoAgente === 'triaje_evidencias' && !triajeFinalizado) return "Responde o adjunta archivos...";
    if (triajeFinalizado) return "Proceso finalizado.";
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