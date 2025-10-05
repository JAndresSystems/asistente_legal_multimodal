// frontend/src/componentes/VistaChat/VistaChat.jsx

import React, { useState } from 'react';
import { chatearConAgente } from '../../servicios/api';
import './VistaChat.css';

function VistaChat() {
  // Estado para guardar el historial de la conversacion
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy el asistente virtual del Consultorio Jurídico. ¿En qué puedo ayudarte hoy?' }
  ]);
  
  // Estado para el texto que el usuario esta escribiendo
  const [entradaUsuario, setEntradaUsuario] = useState('');
  
  // Estado para mostrar un indicador de "escribiendo..."
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);

  const manejarEnvio = async (evento) => {
    evento.preventDefault();
    const textoPregunta = entradaUsuario.trim();

    if (!textoPregunta) return;

    // 1. Añadir el mensaje del usuario a la lista para mostrarlo inmediatamente
    setMensajes(mensajesAnteriores => [
      ...mensajesAnteriores,
      { autor: 'usuario', texto: textoPregunta }
    ]);

    setEntradaUsuario(''); // Limpiar el campo de texto
    setEstaEscribiendo(true); // Mostrar el indicador "escribiendo..."

    // 2. Llamar a la funcion de la API que creamos
    const textoRespuesta = await chatearConAgente(textoPregunta);

    // 3. Añadir la respuesta del agente a la lista
    setMensajes(mensajesAnteriores => [
      ...mensajesAnteriores,
      { autor: 'agente', texto: textoRespuesta }
    ]);

    setEstaEscribiendo(false); // Ocultar el indicador
  };

  return (
    <div className="contenedor-chat">
      <div className="historial-mensajes">
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            <p>{mensaje.texto}</p>
          </div>
        ))}
        {estaEscribiendo && (
          <div className="mensaje agente">
            <p className="indicador-escribiendo">
              <span>.</span><span>.</span><span>.</span>
            </p>
          </div>
        )}
      </div>
      <form className="formulario-chat" onSubmit={manejarEnvio}>
        <input
          type="text"
          value={entradaUsuario}
          onChange={(e) => setEntradaUsuario(e.target.value)}
          placeholder="Escribe tu pregunta aqui..."
          disabled={estaEscribiendo}
        />
        <button type="submit" disabled={estaEscribiendo || !entradaUsuario.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}

export default VistaChat;