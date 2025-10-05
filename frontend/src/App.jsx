// frontend/src/App.jsx

import { useState, useEffect, useCallback } from 'react';
import './App.css';
import ListaCasos from './componentes/ListaCasos/ListaCasos';
import VistaDetalleCaso from './componentes/VistaDetalleCaso/VistaDetalleCaso';
import FormularioCrearCaso from './componentes/FormularioCrearCaso/FormularioCrearCaso';
import { obtenerTodosLosCasos } from './servicios/api';

// ¡NUEVA IMPORTACION! Importamos el componente de chat.
import VistaChat from './componentes/VistaChat/VistaChat';

function App() {
  const [casos, setCasos] = useState([]);
  const [casoSeleccionado, setCasoSeleccionado] = useState(null);

  // Tu logica para recargar datos se mantiene intacta, es excelente.
  const recargarDatosYSeleccionar = useCallback(async (idCasoSeleccionado) => {
    console.log("APP: Recargando todos los datos desde la API...");
    const datosActualizados = await obtenerTodosLosCasos();
    setCasos(datosActualizados);

    if (idCasoSeleccionado) {
      const casoRefrescado = datosActualizados.find(c => c.id_caso === idCasoSeleccionado);
      setCasoSeleccionado(casoRefrescado);
    }
  }, []);

  useEffect(() => {
    recargarDatosYSeleccionar();
  }, [recargarDatosYSeleccionar]);

  const manejarSeleccionCaso = (caso) => {
    setCasoSeleccionado(caso);
  };

  const manejarCasoCreado = (nuevoCaso) => {
    recargarDatosYSeleccionar(nuevoCaso.id_caso);
  };
  
  return (
    <div className="app-contenedor">
      <header><h1>Asistente Legal Multimodal</h1></header>
      
      {/* --- NUEVA SECCION DE CHAT --- */}
      {/* La colocamos aqui, antes del layout principal de casos. */}
      <section className="seccion-chat-introductoria">
        <VistaChat />
      </section>

      <main className="main-layout">
        <div className="columna-izquierda">
          <FormularioCrearCaso onCasoCreado={manejarCasoCreado} />
          <ListaCasos 
            casos={casos} 
            onSeleccionarCaso={manejarSeleccionCaso} 
            casoActivoId={casoSeleccionado ? casoSeleccionado.id_caso : null}
          />
        </div>
        <div className="columna-derecha">
          <VistaDetalleCaso 
            casoSeleccionado={casoSeleccionado}
            onEvidenciaSubida={() => recargarDatosYSeleccionar(casoSeleccionado?.id_caso)}
            onAnalisisCompleto={() => recargarDatosYSeleccionar(casoSeleccionado?.id_caso)}
          />
        </div>
      </main>
    </div>
  );
}

export default App;