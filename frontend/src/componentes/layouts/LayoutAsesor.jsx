import React, { useState } from 'react';
import DashboardAsesor from '../asesor/DashboardAsesor/DashboardAsesor';
// 1. Descomentamos la importacion del componente que muestra el expediente.
import VistaExpedienteAsesor from '../asesor/VistaExpedienteAsesor/VistaExpedienteAsesor';
import { useAuth } from '../../contextos/ContextoAutenticacion';
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


  const { logout } = useAuth();
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

   return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 2rem", backgroundColor: "#1c3b57", color: "white" }}>
        <h1>Panel del Asesor Supervisor</h1>
        <button onClick={logout}>Cerrar Sesión</button>
      </header>
      <main>
        {vistaActual === 'dashboard' && <DashboardAsesor onVerExpediente={navegarAExpediente} />}
        {vistaActual === 'expediente' && <VistaExpedienteAsesor expedienteId={expedienteId} onVolverADashboard={navegarADashboard} />}
      </main>
    </div>
  );
};

export default LayoutAsesor;