
//frontend/src/componentes/usuario/DashboardUsuario/WidgetToggler.jsx

import React from 'react';
import './WidgetChat.css'; // Reutilizamos los estilos

// Un componente simple y reutilizable para el botón que abre el chat.
function WidgetToggler({ onToggle }) {
  return (
    <button className="widget-toggler" onClick={onToggle} title="Abrir chat de ayuda">
      {/* Puedes usar un ícono SVG aquí en lugar de texto */}
      ?
    </button>
  );
}

export default WidgetToggler;