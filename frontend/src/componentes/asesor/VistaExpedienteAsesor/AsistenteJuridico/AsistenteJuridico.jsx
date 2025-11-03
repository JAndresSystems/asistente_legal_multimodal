//C:\react\asistente_legal_multimodal\frontend\src\componentes\asesor\VistaExpedienteAsesor\AsistenteJuridico\AsistenteJuridico.jsx
import React, { useState } from 'react';
import { apiConsultarAgenteJuridico } from '../../../../servicios/api';
import styles from './AsistenteJuridico.module.css';
import ReactMarkdown from 'react-markdown'; // Necesitaremos esta librería

/**
 * Docstring:
 * Componente de UI para interactuar con el Agente Jurídico.
 * Permite al asesor hacer una pregunta sobre el caso y ver una respuesta estructurada.
 */
const AsistenteJuridico = ({ idCaso }) => {
  const [pregunta, setPregunta] = useState('');
  const [respuesta, setRespuesta] = useState(null);
  const [estaCargando, setEstaCargando] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!pregunta.trim()) return;

    setEstaCargando(true);
    setRespuesta(null);
    setError(null);

    try {
      const data = await apiConsultarAgenteJuridico(idCaso, pregunta);
      setRespuesta(data);
    } catch (err) {
      setError(err.message || "Ocurrió un error al consultar al agente.");
    } finally {
      setEstaCargando(false);
    }
  };

  return (
    <div className={styles.contenedorPrincipal}>
      <h3>Asistente Jurídico (IA)</h3>
      <p className={styles.descripcion}>
        Realice una consulta específica sobre el caso para obtener un análisis basado en la evidencia y el contexto legal.
      </p>
      <form onSubmit={handleSubmit}>
        <textarea
          className={styles.textareaPregunta}
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="Ej: ¿Cuáles son los fundamentos de derecho para una demanda de responsabilidad civil extracontractual en este caso?"
          rows="4"
          disabled={estaCargando}
        />
        <button type="submit" className={styles.botonConsultar} disabled={estaCargando}>
          {estaCargando ? "Consultando..." : "Enviar Consulta"}
        </button>
      </form>

      {error && <p className={styles.error}>{error}</p>}

      {respuesta && (
        <div className={styles.contenedorRespuesta}>
          <h4>Respuesta del Asistente:</h4>
          <div className={styles.contenidoRespuesta}>
            <ReactMarkdown>{respuesta.contenido}</ReactMarkdown>
          </div>
          {respuesta.fuentes && respuesta.fuentes.length > 0 && (
            <div className={styles.fuentes}>
              <h5>Fuentes Consultadas:</h5>
              <ul>
                {respuesta.fuentes.map((fuente, index) => (
                  <li key={index}>{fuente}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AsistenteJuridico;