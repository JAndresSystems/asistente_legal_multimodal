// frontend/src/componentes/usuario/DashboardUsuario/WidgetChat.jsx

import React from 'react';
import VistaChat from '../VistaChat/VistaChat'; // Importamos el chat que ya funciona
import './WidgetChat.css';

// El contenedor flotante que envuelve a nuestro chat.
function WidgetChat({ onToggle, onIniciarNuevoCaso }) {
  return (
    <div className="widget-chat-container">
      <header className="widget-chat-header">
        <h3>Asistente Virtual</h3>
        <button className="close-button" onClick={onToggle} title="Cerrar chat">
          &times;
        </button>
      </header>
      <div className="widget-chat-content">
        <VistaChat
          agenteInicial="recepcionista"
          onIniciarTriaje={onIniciarNuevoCaso}
          mostrarBotonRegistrar={false} // Ocultamos botones no necesarios en este contexto
          mostrarBotonVolver={false}
        />
      </div>
    </div>
  );
}

export default WidgetChat;