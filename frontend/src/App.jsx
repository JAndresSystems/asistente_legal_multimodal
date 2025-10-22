// frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import './App.css';
import { useAuth } from './contextos/ContextoAutenticacion';

// Importaciones Originales
import VistaLogin from './componentes/VistaAutenticacion/VistaLogin';
import VistaRegistro from './componentes/VistaAutenticacion/VistaRegistro';


import VistaChat from './componentes/usuario/VistaChat/VistaChat';
import VistaProgresoAnalisis from './componentes/usuario/VistaProgresoAnalisis/VistaProgresoAnalisis';
import DashboardUsuario from './componentes/usuario/DashboardUsuario/DashboardUsuario';
import VistaDetalleCaso from './componentes/usuario/VistaDetalleCaso/VistaDetalleCaso';

function App() {
  const { estaAutenticado, cargando, login, registro, logout } = useAuth();
  
  const [vistaActual, setVistaActual] = useState(() => localStorage.getItem('app_vistaActual') || 'VISTA_LOGIN');
  const [casoId, setCasoId] = useState(() => JSON.parse(localStorage.getItem('app_casoId')) || null);
  const [agenteActivo, setAgenteActivo] = useState(() => localStorage.getItem('app_agenteActivo') || 'recepcionista');

  useEffect(() => {
    localStorage.setItem('app_vistaActual', vistaActual);
    localStorage.setItem('app_casoId', JSON.stringify(casoId));
    localStorage.setItem('app_agenteActivo', agenteActivo);
  }, [vistaActual, casoId, agenteActivo]);

  // --- MANEJADORES ORIGINALES ---
  const manejarCasoCreado = (idDelNuevoCaso) => { setCasoId(idDelNuevoCaso); setAgenteActivo('triaje_evidencias'); };
  const manejarTriajeTerminado = (fueAdmisible) => { if (fueAdmisible) { setVistaActual('VISTA_PROGRESO_ANALISIS'); } else { setAgenteActivo('recepcionista'); } };
  const manejarInicioDeTriaje = () => { setAgenteActivo('triaje_descripcion'); };
  
  // --- NUESTROS MANEJADORES ---
  const manejarAnalisisCompletado = () => { setVistaActual('VISTA_DETALLE_CASO'); };
  const manejarIrAChat = () => { setVistaActual('VISTA_CHAT'); setAgenteActivo('recepcionista'); setCasoId(null); };
  const manejarVerDetalles = (idDelCaso) => { setCasoId(idDelCaso); setVistaActual('VISTA_DETALLE_CASO'); };
  const manejarVolverAlDashboard = () => { setCasoId(null); setVistaActual('VISTA_DASHBOARD_USUARIO'); };

  const renderizarContenido = () => {
    if (cargando) { return <div>Cargando...</div>; }

    if (!estaAutenticado) {
      if (vistaActual !== 'VISTA_LOGIN' && vistaActual !== 'VISTA_REGISTRO') setVistaActual('VISTA_LOGIN');
      if (vistaActual === 'VISTA_REGISTRO') return <VistaRegistro onRegistroSubmit={registro} onCambiarAVistaLogin={() => setVistaActual('VISTA_LOGIN')} />;
      return <VistaLogin onLoginSubmit={login} onCambiarAVistaRegistro={() => setVistaActual('VISTA_REGISTRO')} />;
    }

    if (vistaActual === 'VISTA_LOGIN' || vistaActual === 'VISTA_REGISTRO') {
      setVistaActual('VISTA_DASHBOARD_USUARIO');
      return null;
    }

    switch (vistaActual) {
      case 'VISTA_DASHBOARD_USUARIO':
        return <DashboardUsuario onIniciarNuevoCaso={manejarIrAChat} onVerDetalles={manejarVerDetalles} />;
      case 'VISTA_CHAT':
        return <VistaChat agenteInicial={agenteActivo} casoIdActual={casoId} onIniciarTriaje={manejarInicioDeTriaje} onCasoCreado={manejarCasoCreado} onTriajeTerminado={manejarTriajeTerminado} onVolverAlDashboard={manejarVolverAlDashboard} />;
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis casoId={casoId} onAnalisisCompletado={manejarAnalisisCompletado} />;
      case 'VISTA_DETALLE_CASO':
        return <VistaDetalleCaso casoId={casoId} onVolverAlDashboard={manejarVolverAlDashboard} onEvidenciaSubida={() => manejarVerDetalles(casoId)} onAnalisisCompleto={() => manejarVerDetalles(casoId)} />;
      default:
        setVistaActual('VISTA_DASHBOARD_USUARIO');
        return null;
    }
  };

  return (
    <div className="aplicacion-principal">
      <header className="app-header">
        <h1>Asistente Legal Multimodal</h1>
        {estaAutenticado && (<button onClick={logout} className="boton-logout">Cerrar Sesión</button>)}
      </header>
      <main className="app-contenido">{renderizarContenido()}</main>
    </div>
  );
}
export default App;