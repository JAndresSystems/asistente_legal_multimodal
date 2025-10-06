import React, { useState, useEffect, useRef } from 'react';
import { chatearConAgente } from '../../servicios/api';
import './VistaChat.css';

function VistaChat({ onIniciarCaso }) {
  /**
   * """
   * Docstring:
   * Este componente renderiza y gestiona la interfaz del chat inicial.
   * Permite al usuario interactuar con el Agente de Atencion y, si es
   * apropiado, iniciar el proceso de creacion de un caso formal.
   *
   * Args:
   *   onIniciarCaso (function): Una funcion callback pasada desde App.jsx
   *                             que se ejecuta para cambiar a la siguiente
   *                             vista del wizard.
   *
   * Returns:
   *   (JSX.Element): La interfaz de usuario completa para el chat.
   * """
   */

  // ----------------------------------------------------------------------------
  // Estado del Componente
  // ----------------------------------------------------------------------------
  const [mensajes, setMensajes] = useState([
    { autor: 'agente', texto: '¡Hola! Soy tu Asistente Legal virtual. Estoy aqui para responder tus preguntas sobre el Consultorio Juridico. ¿En que puedo ayudarte?' }
  ]);
  const [entradaUsuario, setEntradaUsuario] = useState('');
  const [estaEscribiendo, setEstaEscribiendo] = useState(false);
  const [mostrarBotonIniciarCaso, setMostrarBotonIniciarCaso] = useState(false);
  const finalDeMensajesRef = useRef(null);

  // ----------------------------------------------------------------------------
  // Efectos Secundarios
  // ----------------------------------------------------------------------------
  useEffect(() => {
    finalDeMensajesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  // ----------------------------------------------------------------------------
  // Manejadores de Eventos
  // ----------------------------------------------------------------------------
  const manejarEnvio = async (evento) => {
    evento.preventDefault();
    const textoPregunta = entradaUsuario.trim();

    if (!textoPregunta) return;

    setMensajes(mensajesAnteriores => [
      ...mensajesAnteriores,
      { autor: 'usuario', texto: textoPregunta }
    ]);
    setEntradaUsuario('');
    setEstaEscribiendo(true);

    // --- LLAMADA REAL A LA API ---
    // La simulacion ha sido reemplazada por la llamada a la funcion del
    // modulo de servicios/api.js.
    const textoRespuesta = await chatearConAgente(textoPregunta);
    // --- FIN DE LA LLAMADA A LA API ---

    setMensajes(mensajesAnteriores => [
      ...mensajesAnteriores,
      { autor: 'agente', texto: textoRespuesta }
    ]);
    
    // Logica de ejemplo para mostrar el boton de iniciar caso.
    // El agente de IA puede ser instruido para incluir una palabra clave
    // como "[INICIAR_CASO]" en su respuesta para activar este boton.
    if (textoRespuesta.includes("[INICIAR_CASO]")) {
        setMostrarBotonIniciarCaso(true);
    }

    setEstaEscribiendo(false);
  };

  // ----------------------------------------------------------------------------
  // Renderizado del Componente
  // ----------------------------------------------------------------------------
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
        <div ref={finalDeMensajesRef} />
      </div>

      {mostrarBotonIniciarCaso && (
        <div className="contenedor-acciones-chat">
          <button onClick={onIniciarCaso} className="boton-iniciar-caso">
            Entendido, quiero iniciar un caso
          </button>
        </div>
      )}

      <form className="formulario-chat" onSubmit={manejarEnvio}>
        <input
          type="text"
          value={entradaUsuario}
          onChange={(e) => setEntradaUsuario(e.target.value)}
          placeholder="Escribe tu pregunta aqui..."
          disabled={estaEscribiendo}
          autoComplete="off"
        />
        <button type="submit" disabled={estaEscribiendo || !entradaUsuario.trim()}>
          Enviar
        </button>
      </form>
    </div>
  );
}

export default VistaChat;