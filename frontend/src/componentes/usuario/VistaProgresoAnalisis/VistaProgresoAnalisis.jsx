//C:\react\asistente_legal_multimodal\frontend\src\componentes\usuario\VistaProgresoAnalisis\VistaProgresoAnalisis.jsx
import React, { useState, useEffect, useRef } from 'react';
// --- INICIO DE LA RESTAURACIÓN: Volver a la importación original ---
import { obtenerDetallesCaso } from '../../../servicios/api/ciudadano';
// --- FIN DE LA RESTAURACIÓN ---
import './VistaProgresoAnalisis.css';

function VistaProgresoAnalisis({ casoId, onAnalisisCompletado }) {
  const [evidencias, setEvidencias] = useState([]);
  const [cargandoInicial, setCargandoInicial] = useState(true);
  const [analisisFinalizado, setAnalisisFinalizado] = useState(false);
  const idIntervaloRef = useRef(null);

  useEffect(() => {
    const verificarEstadoDelCaso = async () => {
      if (!casoId) return;
      try {
        const datosCaso = await obtenerDetallesCaso(casoId);
        // La lógica clave: si el estado del CASO ya no es 'en_revision', el análisis terminó.
        if (cargandoInicial) {
            setEvidencias(datosCaso.evidencias || []);
            setCargandoInicial(false);
        }


        if (datosCaso.estado !== 'en_revision') {
          setAnalisisFinalizado(true);
          clearInterval(idIntervaloRef.current);
          console.log(`PROGRESO: El estado del caso cambió a '${datosCaso.estado}'. Sondeo detenido.`);
        }
      } catch (error) {
        console.error("PROGRESO: Error al recargar los detalles del caso", error);
        clearInterval(idIntervaloRef.current);
        setAnalisisFinalizado(true);
      }
    };
    verificarEstadoDelCaso();
    idIntervaloRef.current = setInterval(verificarEstadoDelCaso, 4000);
    return () => clearInterval(idIntervaloRef.current);
  }, [casoId, cargandoInicial]);

 return (
    <div className="vista-progreso-contenedor">
      <h3>Paso 4: Analizando Evidencias del Caso #{casoId}</h3>
      
      {/* --- INICIO DE LA CORRECCION: Volvemos a mostrar la lista de evidencias --- */}
      <ul className="lista-evidencia-progreso">
        {evidencias.map(evidencia => (
          <li key={evidencia.id} className="item-evidencia-progreso">
            {evidencia.nombre_archivo}
          </li>
        ))}
      </ul>
      {/* --- FIN DE LA CORRECCION --- */}

      

      <div className="contenedor-acciones-progreso">
        <p>{analisisFinalizado ? '¡El análisis ha finalizado!' : 'Por favor, espera mientras nuestros agentes analizan tus documentos...'}</p>
        <button className="boton-ver-reporte" onClick={onAnalisisCompletado} disabled={!analisisFinalizado}>
          Continuar al Reporte Final
        </button>
      </div>
    </div>
  );
}
export default VistaProgresoAnalisis;