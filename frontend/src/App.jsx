import React, { useState } from 'react';
import './App.css';

// ==============================================================================
// Importacion de Componentes Reales
// ==============================================================================
import VistaChat from './componentes/VistaChat/VistaChat';


// ==============================================================================
// Componentes Marcadores de Posicion (Stubs)
// ==============================================================================
// Mantenemos los stubs para los pasos que aun no hemos construido.

const FormularioCrearCaso = () => (
  <div className="vista-contenedor">
    <h1>Paso 2: Describir el Caso</h1>
    <p>Aqui el usuario describira los hechos de su situacion.</p>
  </div>
);

const FormularioSubirEvidencia = () => (
  <div className="vista-contenedor">
    <h1>Paso 3: Subir Evidencias</h1>
    <p>Aqui el usuario podra subir multiples archivos (PDF, audio, imagenes).</p>
  </div>
);

const VistaProgresoAnalisis = () => (
  <div className="vista-contenedor">
    <h1>Paso 4: Analisis en Progreso</h1>
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
   * Su unica responsabilidad es gestionar la vista que se le muestra al usuario
   * en cada momento del flujo de trabajo, funcionando como un "wizard".
   * """
   */

  // ----------------------------------------------------------------------------
  // Estado
  // ----------------------------------------------------------------------------
  const [vistaActual, setVistaActual] = useState('VISTA_CHAT');

  // ----------------------------------------------------------------------------
  // Renderizado Condicional de Vistas
  // ----------------------------------------------------------------------------
  const renderizarVistaActual = () => {
    switch (vistaActual) {
      case 'VISTA_CHAT':
        // Ahora renderizamos el componente importado, pasandole la funcion
        // para que pueda controlar el cambio a la siguiente vista.
        return <VistaChat onIniciarCaso={() => setVistaActual('VISTA_CREAR_CASO')} />;
      case 'VISTA_CREAR_CASO':
        return <FormularioCrearCaso />;
      case 'VISTA_SUBIR_EVIDENCIA':
        return <FormularioSubirEvidencia />;
      case 'VISTA_PROGRESO_ANALISIS':
        return <VistaProgresoAnalisis />;
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