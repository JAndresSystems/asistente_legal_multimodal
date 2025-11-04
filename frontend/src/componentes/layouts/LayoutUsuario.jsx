// C:\react\asistente_legal_multimodal\frontend\src\componentes\layouts\LayoutUsuario.jsx
import React, { useState } from 'react';

// Vistas que este layout controla
import DashboardUsuario from '../usuario/DashboardUsuario/DashboardUsuario';
import VistaDetalleCaso from '../usuario/VistaDetalleCaso/VistaDetalleCaso';
import VistaChat from '../usuario/VistaChat/VistaChat';
import VistaProgresoAnalisis from '../usuario/VistaProgresoAnalisis/VistaProgresoAnalisis';

// --- INICIO DE LA MODIFICACION: Añadir importación para el logout ---
import { useAuth } from '../../contextos/ContextoAutenticacion';
// --- FIN DE LA MODIFICACION ---

function LayoutUsuario() {
  const [vistaActual, setVistaActual] = useState('VISTA_DASHBOARD_USUARIO');
  const [casoId, setCasoId] = useState(null);
  const [agenteActivo, setAgenteActivo] = useState('recepcionista');
  
  // --- INICIO DE LA MODIFICACION: Añadir lógica para el logout ---
  const { logout } = useAuth();
  // --- FIN DE LA MODIFICACION ---

  // --- Manejadores de Navegación (Sin cambios en su lógica interna) ---
  const manejarIrAChat = () => {
    setAgenteActivo('recepcionista');
    setVistaActual('VISTA_CHAT');
  };
  const manejarVerDetalles = (id) => { 
    setCasoId(id); 
    setVistaActual('VISTA_DETALLE_CASO_USUARIO'); 
  };
  const manejarVolverAlDashboard = () => {
    setAgenteActivo('recepcionista');
    setVistaActual('VISTA_DASHBOARD_USUARIO');
  };
  const manejarInicioDeTriaje = () => {
    setAgenteActivo('triaje_descripcion');
  };
  const manejarCasoCreado = (id) => {
    setCasoId(id);
    setAgenteActivo('triaje_evidencias');
  };
  const manejarAnalisisIniciado = (fueAdmisible) => {
    if (fueAdmisible) {
      setVistaActual('VISTA_PROGRESO_ANALISIS');
    } else {
      setAgenteActivo('recepcionista');
    }
  };
  const manejarAnalisisCompletado = () => setVistaActual('VISTA_DETALLE_CASO_USUARIO');

  // --- Función para renderizar el contenido principal ---
  const renderizarContenido = () => {
    switch (vistaActual) {
      case 'VISTA_CHAT':
        return <VistaChat 
          agenteInicial={agenteActivo}
          casoIdActual={casoId}
          onIniciarTriaje={manejarInicioDeTriaje}
          onCasoCreado={manejarCasoCreado} 
          onTriajeTerminado={manejarAnalisisIniciado} 
          onVolverAlDashboard={manejarVolverAlDashboard} 
        />;
      
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis 
          casoId={casoId} 
          onAnalisisCompletado={manejarAnalisisCompletado} 
        />;
      
      case 'VISTA_DETALLE_CASO_USUARIO':
        return <VistaDetalleCaso 
          casoId={casoId} 
          onVolverAlDashboard={manejarVolverAlDashboard} 
          onEvidenciaSubida={() => manejarVerDetalles(casoId)} 
        />;

      case 'VISTA_DASHBOARD_USUARIO':
      default:
        return <DashboardUsuario 
          onIniciarNuevoCaso={manejarIrAChat} 
          onVerDetalles={manejarVerDetalles} 
        />;
    }
  };

  // --- estructura de Layout con cabecera ---
  return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 2rem", backgroundColor: "#005a4b", color: "white" }}>
        <h1>Portal del Ciudadano</h1>
        <button onClick={logout}>Cerrar Sesión</button>
      </header>
      <main>
        {renderizarContenido()}
      </main>
    </div>
  );
  
}

export default LayoutUsuario;