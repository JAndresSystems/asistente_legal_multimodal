// C:\react\asistente_legal_multimodal\frontend\src\componentes\layouts\LayoutUsuario.jsx
import React, { useState } from 'react';

// Vistas que este layout controla
import DashboardUsuario from '../usuario/DashboardUsuario/DashboardUsuario';
import VistaDetalleCaso from '../usuario/VistaDetalleCaso/VistaDetalleCaso';
import VistaChat from '../usuario/VistaChat/VistaChat';
import VistaProgresoAnalisis from '../usuario/VistaProgresoAnalisis/VistaProgresoAnalisis';

// (MODIFICACIÓN) Importamos la nueva función de API y el hook de autenticación
import { useAuth } from '../../contextos/ContextoAutenticacion';
import { apiCrearCasoInicial } from '../../servicios/api/ciudadano';

function LayoutUsuario() {
  const [vistaActual, setVistaActual] = useState('VISTA_DASHBOARD_USUARIO');
  const [casoId, setCasoId] = useState(null);
  const [agenteActivo, setAgenteActivo] = useState('recepcionista');
  
  const { logout } = useAuth();

  // --- (NUEVA LÓGICA) Manejador para el flujo de registro directo ---
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
      
      // 4. Cambiamos la vista para mostrar el chat
      setVistaActual('VISTA_CHAT');

    } catch (err) {
      console.error("LayoutUsuario: Error al crear el caso inicial:", err);
      // TODO: Mostrar un mensaje de error al usuario en la UI
    }
  };

  // --- Manejadores de Navegación (Ajustados para el nuevo flujo) ---
  const manejarVerDetalles = (id) => { 
    setCasoId(id); 
    setVistaActual('VISTA_DETALLE_CASO_USUARIO'); 
  };
  const manejarVolverAlDashboard = () => {
    setAgenteActivo('recepcionista'); // Reseteamos el agente por si acaso
    setCasoId(null); // Limpiamos el ID del caso
    setVistaActual('VISTA_DASHBOARD_USUARIO');
  };
  const manejarCasoCreado = (id) => {
    // Esta función ahora es menos crítica, pero la mantenemos por si el chat
    // necesitara confirmar el ID del caso que ya le pasamos.
    setCasoId(id);
    setAgenteActivo('triaje_evidencias');
  };
  const manejarAnalisisIniciado = (fueAdmisible) => {
    if (fueAdmisible) {
      setVistaActual('VISTA_PROGRESO_ANALISIS');
    } else {
      // Si el caso es rechazado, volvemos al dashboard
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
          onVerInforme={() => manejarVerDetalles(casoId)}
          // (MODIFICACIÓN) Deshabilitamos el botón de "iniciar" dentro del chat
          // porque el proceso ya fue iniciado desde el dashboard.
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
          // (MODIFICACIÓN CLAVE) El botón ahora llama a nuestro nuevo manejador
          onIniciarNuevoCaso={manejarIniciarRegistroDirecto} 
          onVerDetalles={manejarVerDetalles} 
        />;
    }
  };

  return (
    <div>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1rem 2rem", backgroundColor: "#005a4b", color: "white" }}>
        <h1>Portal del Ciudadano</h1>
        <button onClick={logout}>Cerrar Sesión</button>
      </header>
      <main>
        {renderizarContenido()}
      </main>
    </div>
  );
}

export default LayoutUsuario;