import React, { useState, useEffect, useRef } from 'react';
import { chatearConAgente } from '../../servicios/api';
import './VistaChat.css';

function VistaChat({ onIniciarCaso }) {
  // ... (Docstring y estados iniciales se mantienen) ...
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy tu Asistente Legal virtual. Estoy aqui para responder tus preguntas sobre el Consultorio Juridico. ¿En que puedo ayudarte?' }
  ]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const [mostrarBotonIniciarCaso, setMostrarBotonIniciarCaso] = useState(false);
  
  const finalDeMensajesRef = useRef(null);
  const textareaRef = useRef(null); // Ref para el textarea

  // Efecto para el scroll automatico
  useEffect(() => {
    finalDeMensajesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  // --- NUEVO EFECTO PARA EL TEXTAREA AUTO-EXPANDIBLE ---
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto'; // Resetea la altura
      textarea.style.height = `${textarea.scrollHeight}px`; // Ajusta a la altura del contenido
    }
  }, [entradaUsuario]);

  const manejarEnvio = async (evento) => {
    // Previene el comportamiento por defecto si viene de un 'form'
    if (evento) evento.preventDefault(); 
    
    const textoPregunta = entradaUsuario.trim();
    if (!textoPregunta) return;

    setMensajes(mensajesAnteriores => [...mensajesAnteriores, { autor: 'usuario', texto: textoPregunta }]);
    setEntradaUsuario('');
    setEstaEscribiendo(true);
    setMostrarBotonIniciarCaso(false); // Oculta el boton al enviar nueva pregunta

    const textoRespuesta = await chatearConAgente(textoPregunta);

    // --- LOGICA DEL BOTON MEJORADA ---
    // El agente de IA debe incluir la señal [INICIAR_CASO] cuando el flujo
    // deba continuar a la creacion del caso.
    let respuestaLimpia = textoRespuesta;
    if (textoRespuesta.includes("[INICIAR_CASO]")) {
        setMostrarBotonIniciarCaso(true);
        // Limpiamos la señal para no mostrarla al usuario.
        respuestaLimpia = textoRespuesta.replace("[INICIAR_CASO]", "").trim();
    }
    
    setMensajes(mensajesAnteriores => [...mensajesAnteriores, { autor: 'agente', texto: respuestaLimpia }]);
    setEstaEscribiendo(false);
  };

  // --- NUEVO MANEJADOR PARA ENVIO CON "ENTER" ---
  const manejarKeyDown = (evento) => {
    if (evento.key === 'Enter' && !evento.shiftKey) {
      evento.preventDefault();
      manejarEnvio();
    }
  };

  return (
    <div className="contenedor-chat">
      <div className="historial-mensajes">
        {/* ... (mapeo de mensajes igual que antes) ... */}
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            <p>{mensaje.texto}</p>
          </div>
        ))}
        {estaEscribiendo && (
          <div className="mensaje agente">
            <p className="indicador-escribiendo"><span>.</span><span>.</span><span>.</span></p>
          </div>
        )}
        <div ref={finalDeMensajesRef} />
      </div>

      {mostrarBotonIniciarCaso && (
        <div className="contenedor-acciones-chat">
          <button onClick={onIniciarCaso} className="boton-iniciar-caso">
            Iniciar Creacion de Caso
          </button>
        </div>
      )}

      <form className="formulario-chat" onSubmit={manejarEnvio}>
        <textarea
          ref={textareaRef}
          value={entradaUsuario}
          onChange={(e) => setEntradaUsuario(e.target.value)}
          onKeyDown={manejarKeyDown}
          placeholder="Escribe tu pregunta aqui..."
          disabled={estaEscribiendo}
          rows={1} // Empezamos con una sola fila
        />
        <button type="submit" disabled={estaEscribiendo || !entradaUsuario.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}

export default VistaChat;