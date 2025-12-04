//C:\react\asistente_legal_multimodal\frontend\src\componentes\layouts\LayoutUsuario.jsx
import React, { useState } from 'react';

// Vistas que este layout controla
import DashboardUsuario from '../usuario/DashboardUsuario/DashboardUsuario';
import VistaDetalleCaso from '../usuario/VistaDetalleCaso/VistaDetalleCaso';
import VistaChat from '../usuario/VistaChat/VistaChat';
import VistaProgresoAnalisis from '../usuario/VistaProgresoAnalisis/VistaProgresoAnalisis';

// Contexto y Servicios
import { useAuth } from '../../contextos/ContextoAutenticacion';
import { apiCrearCasoInicial } from '../../servicios/api/ciudadano';

function LayoutUsuario() {
  const [vistaActual, setVistaActual] = useState('VISTA_DASHBOARD_USUARIO');
  const [casoId, setCasoId] = useState(null);
  const [agenteActivo, setAgenteActivo] = useState('recepcionista');
  
  const { logout } = useAuth();

  // --- Manejador para el flujo de registro directo (Nuevo Flujo) ---
  const manejarIniciarRegistroDirecto = async () => {
    try {
      console.log("LayoutUsuario: Iniciando creación de un nuevo caso...");
      // 1. Llamamos a la API para crear un caso "esqueleto"
      const nuevoCaso = await apiCrearCasoInicial();
      console.log(`LayoutUsuario: Caso creado con éxito. ID: ${nuevoCaso.id}`);

      // 2. Guardamos el ID del nuevo caso
      setCasoId(nuevoCaso.id);
      
      // 3. Configuramos el chat para que inicie en modo triaje
      setAgenteActivo('triaje_descripcion');
      
      // 4. Cambiamos la vista para mostrar el chat inmediatamente
      setVistaActual('VISTA_CHAT');

    } catch (err) {
      console.error("LayoutUsuario: Error al crear el caso inicial:", err);
      alert("Hubo un error al iniciar el caso. Por favor, intente nuevamente.");
    }
  };

  // --- Manejadores de Navegación ---
  const manejarVerDetalles = (id) => { 
    setCasoId(id); 
    setVistaActual('VISTA_DETALLE_CASO_USUARIO'); 
  };

  const manejarVolverAlDashboard = () => {
    setAgenteActivo('recepcionista'); // Reseteamos el agente
    setCasoId(null); // Limpiamos el ID del caso
    setVistaActual('VISTA_DASHBOARD_USUARIO');
  };

  const manejarCasoCreado = (id) => {
    // Mantener sincronizado el ID si el chat lo requiere
    setCasoId(id);
    setAgenteActivo('triaje_evidencias');
  };

  // --- CORRECCIÓN CRÍTICA: Control del Fin del Análisis ---
  const manejarAnalisisIniciado = (fueAdmisible) => {
    console.log(`LayoutUsuario: El triaje ha terminado. ¿Fue admisible? ${fueAdmisible}`);
    
    // Si el caso es ADMISIBLE, NO cambiamos de vista.
    // Dejamos que VistaChat muestre el bloque final con el botón "Ver Informe Final".
    
    if (!fueAdmisible) {
      // Solo si el caso es rechazado, devolvemos al usuario al dashboard automáticamente.
      // Opcionalmente, VistaChat podría manejar esto mostrando un mensaje de rechazo,
      // pero esta redirección es una salvaguarda segura.
      manejarVolverAlDashboard();
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
          onCasoCreado={manejarCasoCreado} 
          onTriajeTerminado={manejarAnalisisIniciado} 
          onVolverAlDashboard={manejarVolverAlDashboard}
          // Esta es la conexión clave: El botón "Ver Informe" del chat llamará a esto:
          onVerInforme={() => manejarVerDetalles(casoId)}
          // Deshabilitamos el botón de registro manual dentro del chat (ya se creó el caso)
          mostrarBotonRegistrar={false}
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
          onIniciarNuevoCaso={manejarIniciarRegistroDirecto} 
          onVerDetalles={manejarVerDetalles} 
        />;
    }
  };

  return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 2rem", backgroundColor: "#005a4b", color: "white" }}>
        <h1>Portal del Ciudadano</h1>
        <button onClick={logout} style={{ backgroundColor: "transparent", border: "1px solid white", color: "white", padding: "0.5rem 1rem", cursor: "pointer" }}>
          Cerrar Sesión
        </button>
      </header>
      <main>
        {renderizarContenido()}
      </main>
    </div>
  );
}

export default LayoutUsuario;