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
  
  const [agenteActivo, setAgenteActivo] = useState('recepcionista'); // 'recepcionista' o 'triaje'
 

  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso);
    setCasoId(idDelNuevoCaso);
  
    setAgenteActivo('triaje_evidencias'); 
  };

  const manejarTriajeTerminado = (fueAdmisible) => {
    console.log("APP: El triaje ha terminado. ¿Fue admisible?", fueAdmisible);
    
    if (fueAdmisible) {
      console.log("APP: El caso fue admitido. Avanzando a la vista de progreso.");
      setVistaActual('VISTA_PROGRESO_ANALISIS');
    } else {
    
      console.log("APP: El caso fue rechazado. Regresando al agente recepcionista.");
      setAgenteActivo('recepcionista');
      
    }
  };


  // const manejarSubidaCompletada = () => {
  //   console.log("APP: Todas las evidencias subidas. Avanzando a vista de progreso.");
  //   setVistaActual('VISTA_PROGRESO_ANALISIS');
  // };

  const manejarAnalisisCompletado = () => {
    console.log("APP: Todos los analisis completados. Avanzando al reporte final.");
    setVistaActual('VISTA_REPORTE_FINAL');
  };

  
  const manejarInicioDeTriaje = () => {
      console.log("APP: El usuario quiere registrar un caso. Cambiando a agente de triaje.");
      setAgenteActivo('triaje_descripcion');
      // Importante: No cambiamos de 'vistaActual', nos mantenemos en el chat.
  };
  


  const renderizarVistaActual = () => {
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