// frontend/src/App.jsx

import React, { useState } from 'react';
import './App.css';

import VistaChat from './componentes/VistaChat/VistaChat';
import FormularioSubirEvidencia from './componentes/FormularioSubirEvidencia/FormularioSubirEvidencia';
import VistaProgresoAnalisis from './componentes/VistaProgresoAnalisis/VistaProgresoAnalisis';
import VistaReporteFinal from './componentes/VistaReporteFinal/VistaReporteFinal';

function App() {
  const [vistaActual, setVistaActual] = useState('VISTA_CHAT');
  const [casoId, setCasoId] = useState(null);
  
  // ==============================================================================
  // INICIO DE LA MODIFICACION: Nuevo estado para controlar el agente activo en el chat
  // ==============================================================================
  const [agenteActivo, setAgenteActivo] = useState('recepcionista'); // 'recepcionista' o 'triaje'
  // ==============================================================================
  // FIN DE LA MODIFICACION
  // ==============================================================================

  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso);
    setCasoId(idDelNuevoCaso);
    // Ahora, en lugar de cambiar de vista, le decimos al chat que pida las evidencias
    setAgenteActivo('triaje_evidencias'); 
  };

  const manejarSubidaCompletada = () => {
    console.log("APP: Todas las evidencias subidas. Avanzando a vista de progreso.");
    setVistaActual('VISTA_PROGRESO_ANALISIS');
  };

  const manejarAnalisisCompletado = () => {
    console.log("APP: Todos los analisis completados. Avanzando al reporte final.");
    setVistaActual('VISTA_REPORTE_FINAL');
  };

  // ==============================================================================
  // INICIO DE LA MODIFICACION: Cambiamos la logica de iniciar caso
  // ==============================================================================
  const manejarInicioDeTriaje = () => {
      console.log("APP: El usuario quiere registrar un caso. Cambiando a agente de triaje.");
      setAgenteActivo('triaje_descripcion');
      // Importante: No cambiamos de 'vistaActual', nos mantenemos en el chat.
  };
  // ==============================================================================
  // FIN DE LA MODIFICACION
  // ==============================================================================


  const renderizarVistaActual = () => {
    switch (vistaActual) {
      case 'VISTA_CHAT':
        // ==================================================================
        // INICIO DE LA MODIFICACION: Pasamos el nuevo estado y manejadores a VistaChat
        // ==================================================================
        return (
          <VistaChat 
            agenteInicial={agenteActivo}
            casoIdActual={casoId}
            onIniciarTriaje={manejarInicioDeTriaje}
            onCasoCreado={manejarCasoCreado}
            onSubidaCompletada={manejarSubidaCompletada}
          />
        );
        // ==================================================================
        // FIN DE LA MODIFICACION
        // ==================================================================
      
      // La vista para crear caso y subir evidencia por separado ya no se usaran en este flujo.
      // Las mantendremos por ahora, pero la logica se movera a VistaChat.
      
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis casoId={casoId} onAnalisisCompletado={manejarAnalisisCompletado} />;
      
      case 'VISTA_REPORTE_FINAL':
        return <VistaReporteFinal casoId={casoId} />;
      
      default:
        return <VistaChat agenteInicial={'recepcionista'} onIniciarTriaje={manejarInicioDeTriaje} />;
    }
  };

  return (
    <div className="aplicacion-principal">
      <header className="app-header">
        <h1>Asistente Legal Multimodal</h1>
      </header>
      <main className="app-contenido">
        {renderizarVistaActual()}
      </main>
    </div>
  );
}

export default App;