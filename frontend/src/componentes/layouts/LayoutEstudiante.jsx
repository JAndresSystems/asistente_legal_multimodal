// frontend/src/componentes/layouts/LayoutEstudiante.jsx

import React, { useState } from 'react';

// Importamos ambas vistas que este layout controlara
import DashboardEstudiante from '../estudiante/DashboardEstudiante/DashboardEstudiante';
import VistaExpedienteEstudiante from '../estudiante/VistaExpedienteEstudiante/VistaExpedienteEstudiante';
import { useAuth } from '../../contextos/ContextoAutenticacion';

function LayoutEstudiante() {
  const [vistaActual, setVistaActual] = useState('dashboard'); // 'dashboard' o 'expediente'
  const [expedienteId, setExpedienteId] = useState(null);
    const { logout } = useAuth();

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
   return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 2rem", backgroundColor: "#571c1c", color: "white" }}>
        <h1>Portal del Estudiante</h1>
        <button onClick={logout}>Cerrar Sesión</button>
      </header>
      <main>
        {vistaActual === 'dashboard' && <DashboardEstudiante onVerExpediente={handleVerExpediente} />}
        {vistaActual === 'expediente' && <VistaExpedienteEstudiante expedienteId={expedienteId} onVolver={handleVolverAlDashboard} />}
      </main>
    </div>
  );
}

export default LayoutEstudiante;