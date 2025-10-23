// C:\react\asistente_legal_multimodal\frontend\src\componentes\layouts\LayoutEstudiante.jsx

import React from 'react';

// Importamos la única vista que este layout controla por ahora
import DashboardEstudiante from '../estudiante/DashboardEstudiante/DashboardEstudiante';

function LayoutEstudiante() {
  // ==============================================================================
  // INICIO DE LA CORRECCION: Eliminamos los useState no utilizados
  // ==============================================================================
  // La lógica de estado (useState para 'vista' y 'casoId') se reintroducirá
  // cuando construyamos la vista de detalle del expediente. Por ahora, no es necesaria.

  // Mantenemos la función como preparación para el siguiente paso
  const manejarVerExpediente = (id) => {
    console.log("FUTURO: Navegar al expediente del caso:", id);
    // En un paso futuro, aquí añadiremos la lógica para cambiar de vista.
  };
  
  // Como solo hay una vista posible en este layout por ahora, la retornamos directamente.
  return <DashboardEstudiante onVerExpediente={manejarVerExpediente} />;
  // ==============================================================================
  // FIN DE LA CORRECCION
  // ==============================================================================
}

export default LayoutEstudiante;