import React, { useState } from 'react';
import './App.css';

// ==============================================================================
// Importacion de Componentes Reales
// ==============================================================================
import VistaChat from './componentes/VistaChat/VistaChat';
import FormularioCrearCaso from './componentes/FormularioCrearCaso/FormularioCrearCaso';


// ==============================================================================
// Componentes Marcadores de Posicion (Stubs)
// ==============================================================================
// Modificamos FormularioSubirEvidencia para que muestre el ID del caso que recibe.
const FormularioSubirEvidencia = ({ casoId }) => (
  <div className="vista-contenedor">
    <h1>Paso 3: Subir Evidencias para el Caso #{casoId}</h1>
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
  /**
   * """
   * Docstring:
   * Se ejecuta cuando el FormularioCrearCaso notifica que un caso ha sido
   * creado exitosamente en el backend.
   *
   * Args:
   *   idDelNuevoCaso (number): El ID del caso devuelto por la API.
   * """
   */
  const manejarCasoCreado = (idDelNuevoCaso) => {
    console.log("APP: Caso creado con ID:", idDelNuevoCaso, ". Avanzando a la siguiente vista.");
    setCasoId(idDelNuevoCaso);
    setVistaActual('VISTA_SUBIR_EVIDENCIA');
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
        return <FormularioSubirEvidencia casoId={casoId} />;
      
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