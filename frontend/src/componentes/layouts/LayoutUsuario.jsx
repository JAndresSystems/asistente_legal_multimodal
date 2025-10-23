// C:\react\asistente_legal_multimodal\frontend\src\componentes\layouts\LayoutUsuario.jsx

import React, { useState } from 'react';

// Importamos las vistas que este layout controla
import DashboardUsuario from '../usuario/DashboardUsuario/DashboardUsuario';
import VistaDetalleCaso from '../usuario/VistaDetalleCaso/VistaDetalleCaso';
import VistaChat from '../usuario/VistaChat/VistaChat';
import VistaProgresoAnalisis from '../usuario/VistaProgresoAnalisis/VistaProgresoAnalisis';

function LayoutUsuario() {
  const [vistaActual, setVistaActual] = useState('VISTA_DASHBOARD_USUARIO');
  const [casoId, setCasoId] = useState(null);
  const [agenteActivo, setAgenteActivo] = useState('recepcionista');

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

  // ==============================================================================
  // INICIO DE LA CORRECCION: Reintroducimos el manejador para iniciar el triaje
  // ==============================================================================
  const manejarInicioDeTriaje = () => {
    // Esta función cambia el 'modo' del chat para que comience a pedir la descripción del caso
    setAgenteActivo('triaje_descripcion');
  };
  // ==============================================================================
  // FIN DE LA CORRECCION
  // ==============================================================================

  const manejarCasoCreado = (id) => {
    setCasoId(id);
    
    setAgenteActivo('triaje_evidencias');
  };
  
  const manejarAnalisisIniciado = (fueAdmisible) => {
    
    if (fueAdmisible) {
      // Si el caso es admitido, procedemos a la pantalla de progreso.
      setVistaActual('VISTA_PROGRESO_ANALISIS');
    } else {
      // Si el caso es rechazado, simplemente reseteamos el estado del agente
      // para que el chat vuelva al modo 'recepcionista', pero SIN cambiar de vista.
      setAgenteActivo('recepcionista');
    }
    
  };

  const manejarAnalisisCompletado = () => setVistaActual('VISTA_DETALLE_CASO_USUARIO');

  switch (vistaActual) {
    case 'VISTA_CHAT':
      return <VistaChat 
        agenteInicial={agenteActivo}
        casoIdActual={casoId}
        // ==============================================================================
        // INICIO DE LA CORRECCION: Reconectamos la prop 'onIniciarTriaje'
        // ==============================================================================
        onIniciarTriaje={manejarInicioDeTriaje}
        // ==============================================================================
        // FIN DE LA CORRECCION
        // ==============================================================================
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
}

export default LayoutUsuario;