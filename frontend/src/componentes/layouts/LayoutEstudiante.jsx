// frontend/src/componentes/layouts/LayoutEstudiante.jsx

import React, { useState } from 'react';

// Importamos ambas vistas que este layout controlara
import DashboardEstudiante from '../estudiante/DashboardEstudiante/DashboardEstudiante';
import VistaExpedienteEstudiante from '../estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante';

function LayoutEstudiante() {
  const [vistaActual, setVistaActual] = useState('dashboard'); // 'dashboard' o 'expediente'
  const [expedienteId, setExpedienteId] = useState(null);

  // Esta funcion se pasara al Dashboard para que pueda iniciar la navegacion
  const handleVerExpediente = (id) => {
    console.log("LayoutEstudiante: Navegando al expediente del caso:", id);
    setExpedienteId(id);
    setVistaActual('expediente');
  };

  // Esta funcion se pasara a la VistaExpediente para que pueda regresar
  const handleVolverAlDashboard = () => {
    setExpedienteId(null);
    setVistaActual('dashboard');
  };
  
  // Renderizado condicional basado en el estado
  if (vistaActual === 'dashboard') {
    return <DashboardEstudiante onVerExpediente={handleVerExpediente} />;
  }
  
  if (vistaActual === 'expediente') {
    // AHORA RENDERIZAMOS EL COMPONENTE REAL
    return <VistaExpedienteEstudiante expedienteId={expedienteId} onVolver={handleVolverAlDashboard} />;
  }

  // Fallback por si el estado es invalido
  return <div>Estado de vista no reconocido.</div>;
}

export default LayoutEstudiante;