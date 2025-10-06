import React, { useState } from 'react';
import './App.css';

// ==============================================================================
// Importacion de Todos los Componentes Reales
// ==============================================================================
import VistaChat from './componentes/VistaChat/VistaChat';
import FormularioCrearCaso from './componentes/FormularioCrearCaso/FormularioCrearCaso';
import FormularioSubirEvidencia from './componentes/FormularioSubirEvidencia/FormularioSubirEvidencia';
import VistaProgresoAnalisis from './componentes/VistaProgresoAnalisis/VistaProgresoAnalisis';
import VistaReporteFinal from './componentes/VistaReporteFinal/VistaReporteFinal';


// ==============================================================================
// Componente Principal de la Aplicacion (El Cerebro del Wizard)
// ==============================================================================

function App() {
  /**
   * """
   * Docstring:
   * El componente App es el orquestador principal de la interfaz de usuario.
   * Gestiona la vista activa y el estado global simple (como el ID del caso),
   * guiando al usuario a traves del flujo completo de la aplicacion.
   * """
   */

  const [vistaActual, setVistaActual] = useState('VISTA_CHAT');
  const [casoId, setCasoId] = useState(null);

  // ----------------------------------------------------------------------------
  // Manejadores de Flujo
  // ----------------------------------------------------------------------------
  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso);
    setCasoId(idDelNuevoCaso);
    setVistaActual('VISTA_SUBIR_EVIDENCIA');
  };

  const manejarSubidaCompletada = () => {
    console.log("APP: Todas las evidencias subidas. Avanzando a vista de progreso.");
    setVistaActual('VISTA_PROGRESO_ANALISIS');
  };

  const manejarAnalisisCompletado = () => {
    console.log("APP: Todos los analisis completados. Avanzando al reporte final.");
    setVistaActual('VISTA_REPORTE_FINAL');
  };

  // ----------------------------------------------------------------------------
  // Renderizado Condicional de Vistas
  // ----------------------------------------------------------------------------
  const renderizarVistaActual = () => {
    switch (vistaActual) {
      case 'VISTA_CHAT':
        return <VistaChat onIniciarCaso={() => setVistaActual('VISTA_CREAR_CASO')} />;
      
      case 'VISTA_CREAR_CASO':
        return <FormularioCrearCaso onCasoCreado={manejarCasoCreado} />;
      
      case 'VISTA_SUBIR_EVIDENCIA':
        return <FormularioSubirEvidencia casoId={casoId} onSubidaCompletada={manejarSubidaCompletada} />;
      
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis casoId={casoId} onAnalisisCompletado={manejarAnalisisCompletado} />;
      
      case 'VISTA_REPORTE_FINAL':
        return <VistaReporteFinal casoId={casoId} />;
      
      default:
        return <VistaChat onIniciarCaso={() => setVistaActual('VISTA_CREAR_CASO')} />;
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