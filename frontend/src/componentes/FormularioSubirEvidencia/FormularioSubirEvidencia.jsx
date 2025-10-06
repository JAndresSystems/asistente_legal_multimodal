import React, { useState, useRef } from 'react';
import { subirEvidencia } from '../../servicios/api';
import './FormularioSubirEvidencia.css';

function FormularioSubirEvidencia({ casoId, onSubidaCompletada }) {
  /**
   * """
   * Docstring:
   * Gestiona la seleccion y subida de multiples archivos de evidencia
   * para un caso especifico.
   *
   * Args:
   *   casoId (number): El ID del caso al que se asociaran las evidencias.
   *   onSubidaCompletada (function): Callback que se ejecuta cuando todos
   *                                 los archivos se han subido con exito.
   *
   * Returns:
   *   (JSX.Element): La interfaz de usuario para la subida de archivos.
   * """
   */

  // ----------------------------------------------------------------------------
  // Referencias y Estado
  // ----------------------------------------------------------------------------
  const inputArchivoRef = useRef(null);
  const [archivosSeleccionados, setArchivosSeleccionados] = useState([]);
  const [estaSubiendo, setEstaSubiendo] = useState(false);
  const [progreso, setProgreso] = useState({ actual: 0, total: 0 });
  const [mensaje, setMensaje] = useState('');

  // ----------------------------------------------------------------------------
  // Manejadores de Eventos
  // ----------------------------------------------------------------------------

  const manejarClickZona = () => inputArchivoRef.current.click();

  const manejarSeleccionArchivos = (evento) => {
    // Convertimos el FileList a un Array y lo añadimos al estado
    setArchivosSeleccionados(prev => [...prev, ...Array.from(evento.target.files)]);
  };

  const manejarEliminarArchivo = (indiceAEliminar) => {
    setArchivosSeleccionados(prev => prev.filter((_, indice) => indice !== indiceAEliminar));
  };

  const manejarSubida = async () => {
    setEstaSubiendo(true);
    setMensaje('Iniciando subida...');
    setProgreso({ actual: 0, total: archivosSeleccionados.length });

    for (let i = 0; i < archivosSeleccionados.length; i++) {
      const archivo = archivosSeleccionados[i];
      setProgreso(prev => ({ ...prev, actual: i + 1 }));
      setMensaje(`Subiendo archivo ${i + 1} de ${archivosSeleccionados.length}: ${archivo.name}`);
      
      try {
        await subirEvidencia(casoId, archivo);
      } catch (error) {
        setMensaje(`Error al subir ${archivo.name}. Por favor, intentalo de nuevo.`);
        console.error("Error en subida de archivo:", error);
        setEstaSubiendo(false);
        return; // Detenemos la subida si un archivo falla
      }
    }

    setMensaje('¡Todas las evidencias se han subido correctamente!');
    // Notificamos al padre que hemos terminado para que pueda avanzar
    onSubidaCompletada();
  };

  // ----------------------------------------------------------------------------
  // Renderizado
  // ----------------------------------------------------------------------------
  return (
    <div className="formulario-subir-evidencia-contenedor">
      <h3>Paso 3: Adjuntar Evidencias para el Caso #{casoId}</h3>

      <input
        type="file"
        multiple
        ref={inputArchivoRef}
        onChange={manejarSeleccionArchivos}
        className="input-oculto"
      />

      <div className="zona-seleccion-archivo" onClick={manejarClickZona}>
        <p>Arrastra tus archivos aquí o haz clic para seleccionarlos</p>
        <small>(PDF, JPG, PNG, MP3, WAV, etc.)</small>
      </div>

      {archivosSeleccionados.length > 0 && (
        <>
          <h4>Archivos listos para subir:</h4>
          <ul className="lista-archivos-seleccionados">
            {archivosSeleccionados.map((archivo, indice) => (
              <li key={indice} className="item-archivo">
                <span className="nombre-archivo">{archivo.name}</span>
                <button 
                  onClick={() => manejarEliminarArchivo(indice)}
                  className="boton-eliminar-archivo"
                  disabled={estaSubiendo}
                >
                  &times;
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="contenedor-acciones-subida">
        <button 
          onClick={manejarSubida}
          className="boton-subir"
          disabled={estaSubiendo || archivosSeleccionados.length === 0}
        >
          {estaSubiendo ? 'Subiendo...' : `Subir ${archivosSeleccionados.length} Archivo(s)`}
        </button>

        {estaSubiendo && (
          <div className="progreso-subida">
            <div 
              className="barra-progreso" 
              style={{ width: `${(progreso.actual / progreso.total) * 100}%` }}
            ></div>
          </div>
        )}

        {mensaje && <p className="mensaje-feedback">{mensaje}</p>}
      </div>
    </div>
  );
}

export default FormularioSubirEvidencia;