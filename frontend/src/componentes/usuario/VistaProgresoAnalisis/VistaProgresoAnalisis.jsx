// frontend/src/componentes/VistaProgresoAnalisis/VistaProgresoAnalisis.jsx

import React, { useState, useEffect, useRef } from 'react';
import { obtenerDetallesCaso } from '../../../servicios/api';
import './VistaProgresoAnalisis.css';

function VistaProgresoAnalisis({ casoId, onAnalisisCompletado }) {
  const [evidencias, setEvidencias] = useState([]);
  const [cargandoInicial, setCargandoInicial] = useState(true);
  const [analisisFinalizado, setAnalisisFinalizado] = useState(false);
  const idIntervaloRef = useRef(null);

  useEffect(() => {
    // Definimos la función que se ejecutará repetidamente
    const verificarEstadoDelCaso = async () => {
      if (!casoId) return;

      try {
        const datosCaso = await obtenerDetallesCaso(casoId);
        
        // Siempre actualizamos la lista de evidencias para que el usuario la vea
        setEvidencias(datosCaso.evidencias || []);
        
        // ======================================================================
        // INICIO DE LA CORRECCION: Revisamos el estado del CASO, no de las evidencias
        // ======================================================================
        // Si el estado del caso principal ya no es 'en_revision', significa
        // que el backend ha terminado el proceso (ya sea a 'asignado' o 'rechazado').
        if (datosCaso.estado !== 'en_revision') {
          setAnalisisFinalizado(true);
          // Detenemos las futuras verificaciones
          clearInterval(idIntervaloRef.current);
          console.log(`PROGRESO: El estado del caso cambió a '${datosCaso.estado}'. Sondeo detenido.`);
        }
        // ======================================================================
        // FIN DE LA CORRECCION
        // ======================================================================

      } catch (error) {
        console.error("PROGRESO: Error al recargar los detalles del caso", error);
        // Si hay un error, también detenemos el sondeo para no insistir.
        clearInterval(idIntervaloRef.current);
      } finally {
        setCargandoInicial(false);
      }
    };

    // Ejecutamos la verificación una vez de inmediato
    verificarEstadoDelCaso();
    
    // Y luego la programamos para que se repita
    idIntervaloRef.current = setInterval(verificarEstadoDelCaso, 4000); // 4 segundos

    // Esta es la función de "limpieza" que se ejecuta si el usuario navega a otra pantalla
    return () => {
      clearInterval(idIntervaloRef.current);
    };
  }, [casoId]); // Dependemos solo de casoId para iniciar el proceso

  if (cargandoInicial) {
    return <div className="vista-progreso-contenedor"><h3>Cargando información del caso...</h3></div>;
  }

  return (
    <div className="vista-progreso-contenedor">
      <h3>Paso 4: Analizando Evidencias del Caso #{casoId}</h3>
      
      <ul className="lista-evidencia-progreso">
        {evidencias.map(evidencia => (
          <li key={evidencia.id} className="item-evidencia-progreso">
            {evidencia.nombre_archivo}
          </li>
        ))}
      </ul>
      
      <div className="contenedor-acciones-progreso">
        <p>
          {analisisFinalizado
            ? '¡El análisis ha finalizado!' 
            : 'Por favor, espera mientras nuestros agentes analizan tus documentos...'}
        </p>
        <button 
          className="boton-ver-reporte"
          onClick={onAnalisisCompletado}
          disabled={!analisisFinalizado}
        >
          Continuar al Reporte Final
        </button>
      </div>
    </div>
  );
}

export default VistaProgresoAnalisis;