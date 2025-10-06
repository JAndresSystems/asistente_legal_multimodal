// frontend/src/componentes/FormularioSubirEvidencia/FormularioSubirEvidencia.jsx
import React, { useState } from 'react';
import { subirEvidencia } from '../../servicios/api';
import './FormularioSubirEvidencia.css';

// --- ¡CORRECCIÓN CLAVE EN LOS PARÁMETROS! ---
// Antes esperaba 'onArchivoSeleccionado', ahora espera 'onEvidenciaSubida' para coincidir con su padre.
function FormularioSubirEvidencia({ idCaso, onEvidenciaSubida }) {
  const [archivo, setArchivo] = useState(null);
  const [estaSubiendo, setEstaSubiendo] = useState(false);
  const [mensaje, setMensaje] = useState('');

  const manejarSeleccionArchivo = (evento) => {
    setArchivo(evento.target.files[0]);
    setMensaje(''); // Limpiar mensajes anteriores
  };

  const manejarEnvio = async (evento) => {
    evento.preventDefault();
    if (!archivo) {
      setMensaje('Por favor, selecciona un archivo primero.');
      return;
    }
    if (!idCaso) {
        setMensaje('Error: No hay un caso seleccionado para asociar la evidencia.');
        return;
    }

    setEstaSubiendo(true);
    setMensaje(`Subiendo ${archivo.name}...`);

    try {
      await subirEvidencia(idCaso, archivo);
      setMensaje('¡Evidencia subida! El análisis ha comenzado.');
      
      // --- ¡CORRECCIÓN CLAVE EN LA LLAMADA! ---
      // Llamamos a la función correcta pasada por el padre para notificarle.
      onEvidenciaSubida(); 

      setArchivo(null); // Limpiar el input de archivo
    } catch (error) {
      console.error("Error al subir evidencia:", error);
      setMensaje('Hubo un error al subir el archivo.');
    } finally {
      setEstaSubiendo(false);
    }
  };

  return (
    <div className="formulario-subir-evidencia">
      <h4>Añadir Nueva Evidencia</h4>
      <form onSubmit={manejarEnvio}>
        <div className="input-grupo">
          <input 
            type="file" 
            id="seleccion-archivo" 
            className="input-archivo"
            onChange={manejarSeleccionArchivo} 
            // Para poder seleccionar el mismo archivo dos veces
            onClick={(e) => (e.target.value = null)}
          />
          <label htmlFor="seleccion-archivo" className="label-archivo">
            {archivo ? archivo.name : 'Seleccionar archivo...'}
          </label>
        </div>
        <button type="submit" disabled={!archivo || estaSubiendo}>
          {estaSubiendo ? 'Subiendo...' : 'Subir Archivo'}
        </button>
      </form>
      {mensaje && <p className="mensaje-feedback">{mensaje}</p>}
    </div>
  );
}

export default FormularioSubirEvidencia;