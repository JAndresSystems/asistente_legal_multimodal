// frontend/src/App.jsx

import React, { useState, useEffect } from 'react'; 
import './App.css';

import { useAuth } from './contextos/ContextoAutenticacion';
import VistaLogin from './componentes/VistaAutenticacion/VistaLogin';
import VistaRegistro from './componentes/VistaAutenticacion/VistaRegistro';

import VistaChat from './componentes/VistaChat/VistaChat';
import VistaProgresoAnalisis from './componentes/VistaProgresoAnalisis/VistaProgresoAnalisis';
import VistaReporteFinal from './componentes/VistaReporteFinal/VistaReporteFinal';

function App() {
  // CORRECCION: Obtenemos login y registro del contexto
  const { estaAutenticado, cargando, login, registro } = useAuth();

  
    const [vistaActual, setVistaActual] = useState(() => localStorage.getItem('app_vistaActual') || 'VISTA_LOGIN');
  const [casoId, setCasoId] = useState(() => JSON.parse(localStorage.getItem('app_casoId')) || null);
  const [agenteActivo, setAgenteActivo] = useState(() => localStorage.getItem('app_agenteActivo') || 'recepcionista');

// Hook para guardar el estado en localStorage cada vez que cambia
  useEffect(() => {
    localStorage.setItem('app_vistaActual', vistaActual);
    localStorage.setItem('app_casoId', JSON.stringify(casoId));
    localStorage.setItem('app_agenteActivo', agenteActivo);
  }, [vistaActual, casoId, agenteActivo]);



  // ... (manejarCasoCreado, manejarTriajeTerminado, etc. se quedan igual)
  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso);
    setCasoId(idDelNuevoCaso);
    setAgenteActivo('triaje_evidencias'); 
  };
  const manejarTriajeTerminado = (fueAdmisible) => {
    if (fueAdmisible) {
      setVistaActual('VISTA_PROGRESO_ANALISIS');
    } else {
      setAgenteActivo('recepcionista');
    }
  };
  const manejarAnalisisCompletado = () => {
    setVistaActual('VISTA_REPORTE_FINAL');
  };
  const manejarInicioDeTriaje = () => {
      setAgenteActivo('triaje_descripcion');
  };

 const renderizarContenido = () => {
    if (cargando) {
      return <div>Cargando...</div>;
    }

    if (!estaAutenticado) {
      // Si no esta autenticado, limpiamos cualquier estado de sesion anterior
      if (vistaActual !== 'VISTA_LOGIN' && vistaActual !== 'VISTA_REGISTRO') {
        setVistaActual('VISTA_LOGIN');
      }

      if (vistaActual === 'VISTA_REGISTRO') {
        return (
          <VistaRegistro 
            onRegistroSubmit={registro}
            onCambiarAVistaLogin={() => setVistaActual('VISTA_LOGIN')} 
          />
        );
      }
      return (
        <VistaLogin 
          onLoginSubmit={login}
          onCambiarAVistaRegistro={() => setVistaActual('VISTA_REGISTRO')} 
        />
      );
    }

    // Si esta autenticado y la vista es de login/registro, lo forzamos a ir al chat
    if (vistaActual === 'VISTA_LOGIN' || vistaActual === 'VISTA_REGISTRO') {
        setVistaActual('VISTA_CHAT');
    }

    switch (vistaActual) {
      case 'VISTA_CHAT':
         return (
          <VistaChat 
            agenteInicial={agenteActivo}
            casoIdActual={casoId}
            onIniciarTriaje={manejarInicioDeTriaje}
            onCasoCreado={manejarCasoCreado}
            onTriajeTerminado={manejarTriajeTerminado}
          />
        );
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis casoId={casoId} onAnalisisCompletado={manejarAnalisisCompletado} />;
      case 'VISTA_REPORTE_FINAL':
        return <VistaReporteFinal casoId={casoId} />;
      default:
        setVistaActual('VISTA_CHAT');
        return null;
    }
  };

  return (
    <div className="aplicacion-principal">
      <header className="app-header">
        <h1>Asistente Legal Multimodal</h1>
      </header>
      <main className="app-contenido">
        {renderizarContenido()}
      </main>
    </div>
  );
}

export default App;