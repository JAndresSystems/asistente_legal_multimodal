import React, { useState } from 'react';
import { apiGenerarDocumento } from '../../../../servicios/api';
import styles from './GeneradorDocumentos.module.css';

// Lista de plantillas disponibles. En un futuro, esto podría venir de la API.
const plantillasDisponibles = [
  { nombre: "Derecho de Petición", archivo: "derecho_de_peticion.docx" },
  { nombre: "Acción de Tutela", archivo: "accion_de_tutela.docx" },
];

/**
 * Docstring:
 * Componente de UI para interactuar con el Agente Generador de Documentos.
 * Permite al asesor seleccionar una plantilla y generar un borrador de documento.
 */
const GeneradorDocumentos = ({ idCaso }) => {
  const [plantillaSeleccionada, setPlantillaSeleccionada] = useState('');
  const [documentoGenerado, setDocumentoGenerado] = useState(null);
  const [estaCargando, setEstaCargando] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!plantillaSeleccionada) {
      setError("Por favor, seleccione una plantilla de documento.");
      return;
    }

    setEstaCargando(true);
    setDocumentoGenerado(null);
    setError(null);

    try {
      const data = await apiGenerarDocumento(idCaso, plantillaSeleccionada);
      setDocumentoGenerado(data); // data = { url_descarga, nombre_archivo }
    } catch (err) {
      setError(err.message || "Ocurrió un error al generar el documento.");
    } finally {
      setEstaCargando(false);
    }
  };

  return (
    <div className={styles.contenedorPrincipal}>
      <h3>Generador de Documentos (IA)</h3>
      <p className={styles.descripcion}>
        Seleccione una plantilla para generar un borrador del documento con los datos del caso.
      </p>
      <form onSubmit={handleSubmit}>
        <select
          className={styles.selectPlantilla}
          value={plantillaSeleccionada}
          onChange={(e) => setPlantillaSeleccionada(e.target.value)}
          disabled={estaCargando}
        >
          <option value="">-- Seleccionar plantilla --</option>
          {plantillasDisponibles.map((plantilla) => (
            <option key={plantilla.archivo} value={plantilla.archivo}>
              {plantilla.nombre}
            </option>
          ))}
        </select>
        <button type="submit" className={styles.botonGenerar} disabled={estaCargando}>
          {estaCargando ? "Generando..." : "Generar Documento"}
        </button>
      </form>

      {error && <p className={styles.error}>{error}</p>}

      {documentoGenerado && (
        <div className={styles.contenedorResultado}>
          <h4>Documento Generado:</h4>
          <a 
            href={`http://127.0.0.1:8000${documentoGenerado.url_descarga}`}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.enlaceDescarga}
          >
            Descargar: {documentoGenerado.nombre_archivo}
          </a>
        </div>
      )}
    </div>
  );
};

export default GeneradorDocumentos;