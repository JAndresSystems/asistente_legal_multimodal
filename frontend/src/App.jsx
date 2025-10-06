import React, { useState } from 'react';
import './App.css';

// ==============================================================================
// Importacion de Componentes Reales
// ==============================================================================
import VistaChat from './componentes/VistaChat/VistaChat';
import FormularioCrearCaso from './componentes/FormularioCrearCaso/FormularioCrearCaso';
import FormularioSubirEvidencia from './componentes/FormularioSubirEvidencia/FormularioSubirEvidencia';


// ==============================================================================
// Componentes Marcadores de Posicion (Stubs)
// ==============================================================================
// Solo nos quedan dos stubs por construir.
const VistaProgresoAnalisis = ({ casoId }) => (
  <div className="vista-contenedor">
    <h1>Paso 4: Analizando Evidencias del Caso #{casoId}</h1>
    <p>Aqui el usuario vera el estado de procesamiento de sus evidencias en tiempo real.</p>
  </div>
);

const VistaReporteFinal = () => (
  <div className="vista-contenedor">
    <h1>Paso 5: Reporte Final</h1>
    <p>Aqui se presentaran los resultados del analisis de la IA de forma estructurada.</p>
  </div>
);


// ==============================================================================
// Componente Principal de la Aplicacion (El Cerebro del Wizard)
// ==============================================================================

function App() {
  /**
   * """
   * Docstring:
   * El componente App es el orquestador principal de la interfaz de usuario.
   * Gestiona la vista activa y el estado global simple (como el ID del caso).
   * """
   */

  // ----------------------------------------------------------------------------
  // Estado
  // ----------------------------------------------------------------------------
  const [vistaActual, setVistaActual] = useState('VISTA_CHAT');
  const [casoId, setCasoId] = useState(null);

  // ----------------------------------------------------------------------------
  // Manejadores de Flujo
  // ----------------------------------------------------------------------------
  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso, ". Avanzando a subida de evidencia.");
    setCasoId(idDelNuevoCaso);
    setVistaActual('VISTA_SUBIR_EVIDENCIA');
  };

  const manejarSubidaCompletada = () => {
    console.log("APP: Todas las evidencias subidas. Avanzando a vista de progreso.");
    setVistaActual('VISTA_PROGRESO_ANALISIS');
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
        // Pasamos el casoId para que esta vista sepa que evidencias consultar.
        return <VistaProgresoAnalisis casoId={casoId} />;
      
      case 'VISTA_REPORTE_FINAL':
        return <VistaReporteFinal />;
      
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