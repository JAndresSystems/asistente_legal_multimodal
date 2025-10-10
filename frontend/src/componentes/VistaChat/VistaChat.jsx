
//frontend\src\componentes\VistaChat\VistaChat.jsx

import React, { useState, useEffect, useRef } from 'react';
import { chatearConAgente } from '../../servicios/api';
import './VistaChat.css';

const Sugerencias = ({ onSugerenciaClick }) => (
  <div className="contenedor-sugerencias">
    <button onClick={() => onSugerenciaClick("¿Qué servicios ofrecen?")} className="boton-sugerencia">¿Qué servicios ofrecen?</button>
    <button onClick={() => onSugerenciaClick("¿Tiene algún costo?")} className="boton-sugerencia">¿Tiene algún costo?</button>
    <button onClick={() => onSugerenciaClick("¿Cuál es el horario?")} className="boton-sugerencia">¿Cuál es el horario?</button>
  </div>
);

function VistaChat({ onIniciarCaso }) {
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy el Asistente Legal virtual. Estoy aquí para resolver tus dudas sobre el Consultorio Jurídico.' }
  ]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(true);
  
  const finalDeMensajesRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    finalDeMensajesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  // ==============================================================================
  // LA LOGICA DEFINITIVA PARA CRECIMIENTO Y ENCOGIMIENTO DINAMICO
  // ==============================================================================
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      // 1. Resetea la altura para permitir que se encoja
      textarea.style.height = 'auto';
      // 2. Establece la nueva altura segun el contenido
      const nuevaAltura = Math.min(textarea.scrollHeight, 150); // 150px es el max-height del CSS
      textarea.style.height = `${nuevaAltura}px`;

      // 3. Activa el scroll si el contenido es mayor que la altura maxima
      textarea.style.overflowY = textarea.scrollHeight > 150 ? 'auto' : 'hidden';
    }
  }, [entradaUsuario]); // Se ejecuta cada vez que el usuario escribe

  const enviarMensaje = async (textoPregunta) => {
    if (!textoPregunta.trim()) return;
    if (mostrarSugerencias) setMostrarSugerencias(false);

    setMensajes(anteriores => [...anteriores, { autor: 'usuario', texto: textoPregunta }]);
    setEntradaUsuario('');
    setEstaEscribiendo(true);

    const textoRespuesta = await chatearConAgente(textoPregunta);
    
    setMensajes(anteriores => [...anteriores, { autor: 'agente', texto: textoRespuesta }]);
    setEstaEscribiendo(false);
  };

  const manejarEnvioFormulario = (e) => { e.preventDefault(); enviarMensaje(entradaUsuario); };
  const manejarClickSugerencia = (texto) => { enviarMensaje(texto); };

  return (
    <div className="contenedor-chat">
      <div className="historial-mensajes">
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            <p>{mensaje.texto}</p>
          </div>
        ))}
        {mostrarSugerencias && <Sugerencias onSugerenciaClick={manejarClickSugerencia} />}
        {estaEscribiendo && <div className="mensaje agente"><p>...</p></div>}
        <div ref={finalDeMensajesRef} />
      </div>

      <div className="area-acciones-chat">
        <form className="formulario-chat" onSubmit={manejarEnvioFormulario}>
          <textarea
            ref={textareaRef}
            value={entradaUsuario}
            onChange={(e) => setEntradaUsuario(e.target.value)}
            placeholder="Escribe tu pregunta aqui..."
            disabled={estaEscribiendo}
            rows={1}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); manejarEnvioFormulario(e); } }}
          />
          <button type="submit" disabled={estaEscribiendo || !entradaUsuario.trim()}>Enviar</button>
        </form>
        <div className="contenedor-iniciar-caso">
          <button onClick={onIniciarCaso} className="boton-principal-iniciar">Tengo un caso y quiero registrarlo</button>
        </div>
      </div>
    </div>
  );
}

export default VistaChat;