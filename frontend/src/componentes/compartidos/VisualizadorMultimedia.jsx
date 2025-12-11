// src/componentes/compartidos/VisualizadorMultimedia.jsx
import React, { useState } from 'react';
import './VisualizadorMultimedia.css'; // <--- Importamos el CSS nuevo

// MODO RENDER (Nube) -> ¡ACTIVO!
const API_URL = "https://asistente-legal-backend-897g.onrender.com";

// MODO LOCAL (PC) -> Comentado
// const API_URL = "http://localhost:8000";

const VisualizadorMultimedia = ({ nombreArchivo, casoId }) => {
  const [errorCarga, setErrorCarga] = useState(false);

  if (!nombreArchivo) return null;

  const nombreSeguro = encodeURIComponent(nombreArchivo);
  const rutaIntermedia = casoId ? `${casoId}/` : ''; 
  const urlRecurso = `${API_URL}/archivos_subidos/${rutaIntermedia}${nombreSeguro}`;
  const extension = nombreArchivo.split('.').pop().toLowerCase();

  // Manejo de error visual
  if (errorCarga) {
    return (
      <div className="vm-imagen-contenedor vm-error">
        📄 {nombreArchivo} <br/>(No disponible)
      </div>
    );
  }

  // 1. IMÁGENES
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension)) {
    return (
      <div className="vm-imagen-contenedor" onClick={() => window.open(urlRecurso, '_blank')}>
        <img 
          src={urlRecurso} 
          alt="Evidencia" 
          className="vm-imagen"
          onError={() => setErrorCarga(true)}
          loading="lazy"
        />
      </div>
    );
  }

  // 2. AUDIOS
  if (['mp3', 'wav', 'ogg', 'm4a'].includes(extension)) {
    return (
      <div className="vm-audio-contenedor">
        <div className="vm-audio-player">
          <span style={{fontSize: '16px'}}>🎤</span>
          <audio controls style={{height: '30px', width: '100%'}} onError={() => setErrorCarga(true)}>
            <source src={urlRecurso} />
          </audio>
        </div>
        <div className="vm-audio-etiqueta">Nota de voz</div>
      </div>
    );
  }

  // 3. DOCUMENTOS
  return (
    <div className="vm-documento-contenedor">
      <a href={urlRecurso} target="_blank" rel="noopener noreferrer" className="vm-documento-link">
        <span style={{fontSize: '20px'}}>📄</span>
        <div className="vm-doc-info">
          <div className="vm-doc-nombre">{nombreArchivo}</div>
          <div className="vm-doc-ext">{extension.toUpperCase()}</div>
        </div>
      </a>
    </div>
  );
};

export default VisualizadorMultimedia;