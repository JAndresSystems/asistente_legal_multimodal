import React, { useState } from 'react';
import DashboardAsesor from '../asesor/DashboardAsesor/DashboardAsesor';
// 1. Descomentamos la importacion del componente que muestra el expediente.
import VistaExpedienteAsesor from '../asesor/VistaExpedienteAsesor/VistaExpedienteAsesor';

/**
 * Docstring:
 * Este componente actua como el controlador de vistas principal para el rol de Asesor.
 * Decide si mostrar el dashboard con la lista de casos supervisados o la vista
 * detallada de un expediente especifico.
 */
const LayoutAsesor = () => {
  // Estado para controlar la vista actual: 'dashboard' o 'expediente'
  const [vistaActual, setVistaActual] = useState('dashboard');
  
  // Estado para saber que expediente especifico se debe mostrar
  const [expedienteId, setExpedienteId] = useState(null);

  // Funcion para navegar a la vista de un expediente especifico
  const navegarAExpediente = (idCaso) => {
    setExpedienteId(idCaso);
    setVistaActual('expediente');
  };

  // Funcion para volver al dashboard principal
  const navegarADashboard = () => {
    setExpedienteId(null);
    setVistaActual('dashboard');
  };

  // Renderizado condicional basado en el estado de la vista
  if (vistaActual === 'dashboard') {
    // Pasamos la funcion de navegacion como prop al dashboard
    return <DashboardAsesor onVerExpediente={navegarAExpediente} />;
  }

  if (vistaActual === 'expediente') {
    // 2. Reemplazamos el bloque del placeholder por la llamada real al componente.
    //    Le pasamos el ID del expediente y la funcion para volver.
    return <VistaExpedienteAsesor expedienteId={expedienteId} onVolverADashboard={navegarADashboard} />;
  }

  // Fallback por si el estado es invalido
  return <div>Vista no reconocida.</div>;
};

export default LayoutAsesor;