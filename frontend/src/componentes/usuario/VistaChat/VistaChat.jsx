// frontend/src/componentes/usuario/VistaChat/VistaChat.jsx

import React from 'react';
import { useChatLogic } from './useChatLogic';
import './VistaChat.css';

// ... (El componente Sugerencias y SubidorDeEvidencias no cambian, se mantienen igual)
const Sugerencias = ({ onSugerenciaClick }) => (
    <div className="contenedor-sugerencias">
      <button onClick={() => onSugerenciaClick("¿Qué servicios ofrecen?")} className="boton-sugerencia">¿Qué servicios ofrecen?</button>
      <button onClick={() => onSugerenciaClick("¿Tiene algún costo?")} className="boton-sugerencia">¿Tiene algún costo?</button>
      <button onClick={() => onSugerenciaClick("¿Cuál es el horario?")} className="boton-sugerencia">¿Cuál es el horario?</button>
    </div>
);
  
const SubidorDeEvidencias = ({ 
    archivos, 
    onSeleccionArchivos, 
    onIniciarGrabacion, 
    onDetenerGrabacion, 
    grabando, 
    audioUrl,
    onEliminarArchivo
  }) => {
    return (
      <div className="area-subida-evidencias">
        <div className="lista-archivos-para-subir">
          {archivos.length > 0 ? (
            archivos.map((archivo, i) => (
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


// (MODIFICACIÓN) El componente principal ahora recibe las nuevas props para controlar la visibilidad de los botones.
function VistaChat({ mostrarBotonRegistrar = true, mostrarBotonVolver = true, ...props }) {
  
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
        
        {!triajeFinalizado ? (
          // ===== ESTADO: CHAT ACTIVO =====
          <>
            {modoAgente === 'triaje_evidencias' && (
              <SubidorDeEvidencias 
                archivos={archivosParaSubir}
                onSeleccionArchivos={(e) => setArchivosParaSubir(prev => [...prev, ...Array.from(e.target.files)])}
                onIniciarGrabacion={iniciarGrabacion}
                onDetenerGrabacion={detenerGrabacion}
                grabando={grabando}
                audioUrl={audioUrl}
                onEliminarArchivo={manejarEliminarArchivo}
              />
            )}
            
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

            <div className="contenedor-acciones-secundarias">
              {modoAgente === 'recepcionista' && mostrarBotonRegistrar && (
                <button onClick={props.onIniciarTriaje} className="boton-principal-iniciar">
                  Tengo un caso y quiero registrarlo
                </button>
              )}
              
              {mostrarBotonVolver && (
                <button onClick={props.onVolverAlDashboard} className="boton-secundario-volver">
                  Volver al Panel
                </button>
              )}
            </div>
          </>
        ) : (
          // ===== ESTADO: TRIAJE FINALIZADO (LA GUÍA PARA EL USUARIO) =====
          <div className="triaje-finalizado-info">
            <h4>¡El primer paso ha finalizado!</h4>
            <p>
              Su caso ha sido admitido y pre-asignado a nuestro equipo. Toda la información, el estado actual y los resultados de los agentes internos se encuentran en el informe detallado.
            </p>
            <p><strong>Presione el siguiente botón para continuar.</strong></p>
            <button 
              onClick={props.onVerInforme} 
              className="boton-principal-informe"
            >
              Ir al Informe Detallado del Caso
            </button>
             {mostrarBotonVolver && (
                <button onClick={props.onVolverAlDashboard} className="boton-secundario-volver">
                  Volver al Panel
                </button>
              )}
          </div>
        )}
      </div>
    </div>
  );
}

export default VistaChat;