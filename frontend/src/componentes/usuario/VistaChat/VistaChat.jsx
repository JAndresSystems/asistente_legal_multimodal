// Ubicación: src/componentes/usuario/VistaChat/VistaChat.jsx
import React from 'react';
import { useChatLogic } from './useChatLogic';
import './VistaChat.css';
import VisualizadorMultimedia from '../../compartidos/VisualizadorMultimedia';

// Componente auxiliar para sugerencias rápidas
const Sugerencias = ({ onSugerenciaClick }) => (
    <div className="contenedor-sugerencias">
      <button onClick={() => onSugerenciaClick("¿Qué servicios ofrecen?")} className="boton-sugerencia">¿Qué servicios ofrecen?</button>
      <button onClick={() => onSugerenciaClick("¿Tiene algún costo?")} className="boton-sugerencia">¿Tiene algún costo?</button>
      <button onClick={() => onSugerenciaClick("¿Cuál es el horario?")} className="boton-sugerencia">¿Cuál es el horario?</button>
    </div>
);
  
// Componente auxiliar para la gestión de archivos
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
                <button onClick={() => onEliminarArchivo(i)} className="boton-eliminar-archivo" title="Eliminar">&times;</button>
              </div>
            ))
          ) : ( <p className="texto-ayuda-subida">Adjunta archivos o graba un audio si es necesario.</p> )}
        </div>
        
        {audioUrl && ( <div className="reproductor-audio-chat"><audio src={audioUrl} controls /></div> )}
        
        <div className="botones-evidencia-contenedor">
          <input type="file" id="seleccion-archivo-chat" multiple onChange={onSeleccionArchivos} style={{ display: 'none' }} />
          <label htmlFor="seleccion-archivo-chat" className="boton-accion-evidencia">📎 Adjuntar Archivo</label>
          {!grabando ? (
              <button onClick={onIniciarGrabacion} className="boton-accion-evidencia">🎤 Grabar Audio</button>
          ) : (
              <button onClick={onDetenerGrabacion} className="boton-accion-evidencia detener">⏹ Detener</button>
          )}
        </div>
      </div>
    );
};

function VistaChat({ mostrarBotonRegistrar = true, mostrarBotonVolver = true, ...props }) {
  
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
    obtenerPlaceholder,
    casoIdActual // <--- IMPORTANTE: Obtenemos el ID del caso del hook
  } = useChatLogic(props);
  
  const manejarEnvioFormulario = (e) => { e.preventDefault(); manejarEnvioUnificado(); };

 return (
    <div className="contenedor-chat">
      {/* 1. Área de Historial de Mensajes */}
      <div className="historial-mensajes">
        {mensajes.map((mensaje, indice) => (
          <div key={indice} className={`mensaje ${mensaje.autor}`}>
            
            {/* Texto del mensaje */}
            <p>{mensaje.texto}</p>

            {/* Si el mensaje tiene una lista de archivos, los mostramos visualmente */}
            {mensaje.archivos && mensaje.archivos.length > 0 && (
              <div 
                className={`contenedor-multimedia-whatsapp ${
                  mensaje.archivos.length === 1 ? 'grid-un-archivo' : 'grid-multiples-archivos'
                }`}
              >
                {mensaje.archivos.map((nombreArchivo, i) => (
                  <VisualizadorMultimedia 
                    key={i} 
                    nombreArchivo={nombreArchivo} 
                    casoId={casoIdActual} 
                  />
                ))}
              </div>
            )}
            
          </div>
        ))}
        
        {modoAgente === 'recepcionista' && mostrarSugerencias && <Sugerencias onSugerenciaClick={manejarClickSugerencia} />}
        
        {estaProcesando && (
            <div className="mensaje agente">
                <div className="indicador-escribiendo">
                    <span>.</span><span>.</span><span>.</span>
                </div>
            </div>
        )}
        <div ref={finalDeMensajesRef} />
      </div>

      {/* 2. Área de Acciones (Condicional) */}
      <div className="area-acciones-chat">
        
        {!triajeFinalizado ? (
          // A. MODO ACTIVO: Formulario de chat y subida de archivos
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
              <button type="submit" disabled={estaProcesando || (entradaUsuario.trim() === '' && archivosParaSubir.length === 0)}>
                Enviar
              </button>
            </form>

            <div className="contenedor-acciones-secundarias">
              {modoAgente === 'recepcionista' && mostrarBotonRegistrar && (
                <button onClick={props.onIniciarTriaje} className="boton-principal-iniciar">
                  Registrar Nuevo Caso
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
          // B. MODO FINALIZADO: Bloque de éxito
          <div className="triaje-finalizado-info">
            <h3>¡Proceso Completado!</h3>
            <p>
              Su caso ha sido registrado y analizado exitosamente.
            </p>
            
            <button onClick={props.onVerInforme} className="boton-principal-informe">
              Ver Informe Final del Caso
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default VistaChat;