// frontend/src/componentes/VistaChat/VistaChat.jsx

/**
 * 
 * C:\react\asistente_legal_multimodal\frontend\src\componentes\usuario\VistaChat\VistaChat.jsx
 * Docstring:
 * Este componente es responsable UNICAMENTE de la presentacion (UI)
 * de la interfaz de chat. No contiene logica de negocio.
 * Obtiene todos sus datos y funciones del Hook personalizado 'useChatLogic'.
 */
import React from 'react';
import { useChatLogic } from './useChatLogic'; // <-- Importamos nuestro nuevo Hook
import './VistaChat.css';

// Componente de UI para las sugerencias
const Sugerencias = ({ onSugerenciaClick }) => (
  <div className="contenedor-sugerencias">
    <button onClick={() => onSugerenciaClick("¿Qué servicios ofrecen?")} className="boton-sugerencia">¿Qué servicios ofrecen?</button>
    <button onClick={() => onSugerenciaClick("¿Tiene algún costo?")} className="boton-sugerencia">¿Tiene algún costo?</button>
    <button onClick={() => onSugerenciaClick("¿Cuál es el horario?")} className="boton-sugerencia">¿Cuál es el horario?</button>
  </div>
);

// Componente de UI para el subidor de archivos
const SubidorDeEvidencias = ({ 
  archivos, 
  onSeleccionArchivos, 
  onIniciarGrabacion, 
  onDetenerGrabacion, 
  grabando, 
  audioUrl,
  onEliminarArchivo // <-- 1. Recibimos la nueva prop
}) => {
  return (
    <div className="area-subida-evidencias">
      <div className="lista-archivos-para-subir">
        {archivos.length > 0 ? (
          archivos.map((archivo, i) => (
            // 2. Añadimos el botón de eliminar junto a cada archivo
            <div key={i} className="archivo-item">
              <span>{archivo.name}</span>
              <button 
                onClick={() => onEliminarArchivo(i)} 
                className="boton-eliminar-archivo"
                title="Eliminar archivo"
              >
                &times;
              </button>
            </div>
          ))
        ) : ( <p>Adjunta archivos o graba un audio si es necesario.</p> )}
      </div>
      {audioUrl && ( <div className="reproductor-audio-chat"><audio src={audioUrl} controls /></div> )}
      <div className="botones-evidencia-contenedor">
        <input type="file" id="seleccion-archivo-chat" multiple onChange={onSeleccionArchivos} style={{ display: 'none' }} />
        <label htmlFor="seleccion-archivo-chat" className="boton-accion-evidencia">Adjuntar Archivo</label>
        {!grabando ? (
            <button onClick={onIniciarGrabacion} className="boton-accion-evidencia">Grabar Audio</button>
        ) : (
            <button onClick={onDetenerGrabacion} className="boton-accion-evidencia detener">Detener</button>
        )}
      </div>
    </div>
  );
};




// El componente principal ahora es mucho mas simple
function VistaChat(props) {
  // Simplemente pasamos TODAS las props al hook que contiene la logica
  const logic = useChatLogic(props);// Extraemos la nueva prop
  // Usamos el Hook para obtener toda la logica y el estado.
   const {
    mensajes,
    entradaUsuario,
    setEntradaUsuario,
    estaProcesando,
    mostrarSugerencias,
    modoAgente,
    archivosParaSubir,
    setArchivosParaSubir,
    grabando,
    audioUrl,
    triajeFinalizado,
    finalDeMensajesRef,
    textareaRef,
    manejarEnvioUnificado,
    manejarClickSugerencia,
    iniciarGrabacion,
    detenerGrabacion,
     manejarEliminarArchivo,
    obtenerPlaceholder
  } = useChatLogic(props);
  
  const manejarEnvioFormulario = (e) => { e.preventDefault(); manejarEnvioUnificado(); };

  return (
    <div className="contenedor-chat">
      <div className="historial-mensajes">
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            <p>{mensaje.texto}</p>
          </div>
        ))}
        {modoAgente === 'recepcionista' && mostrarSugerencias && <Sugerencias onSugerenciaClick={manejarClickSugerencia} />}
        {estaProcesando && <div className="mensaje agente"><p>...</p></div>}
        <div ref={finalDeMensajesRef} />
      </div>

      <div className="area-acciones-chat">
        {modoAgente === 'triaje_evidencias' && !triajeFinalizado && (
            <SubidorDeEvidencias 
          archivos={archivosParaSubir}
          onSeleccionArchivos={(e) => setArchivosParaSubir(prev => [...prev, ...Array.from(e.target.files)])}
          onIniciarGrabacion={iniciarGrabacion}
          onDetenerGrabacion={detenerGrabacion}
          grabando={grabando}
          audioUrl={audioUrl}
          onEliminarArchivo={manejarEliminarArchivo} // <-- Añadir esta línea
        />
        )}
        
        {(modoAgente === 'recepcionista' || !triajeFinalizado) && (
            <form className="formulario-chat" onSubmit={manejarEnvioFormulario}>
            <textarea
                ref={textareaRef}
                value={entradaUsuario}
                onChange={(e) => setEntradaUsuario(e.target.value)}
                placeholder={obtenerPlaceholder()}
                disabled={estaProcesando}
                rows={1}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); manejarEnvioFormulario(e); } }}
            />
            <button type="submit" disabled={estaProcesando}>Enviar</button>
            </form>
        )}

        <div className="contenedor-acciones-secundarias">
          {logic.modoAgente === 'recepcionista' && (
            <button onClick={props.onIniciarTriaje} className="boton-principal-iniciar">
              Tengo un caso y quiero registrarlo
            </button>
          )}
          
          {/* El botón de volver ahora es visible en todo momento en el chat */}
          <button onClick={props.onVolverAlDashboard} className="boton-secundario-volver">
            Volver al Panel
          </button>
        </div>


        
        
      </div>
    </div>
  );
}

export default VistaChat;