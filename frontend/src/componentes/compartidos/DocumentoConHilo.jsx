import React, { useState } from 'react';
import './DocumentoConHilo.css';

const DocumentoConHilo = ({ 
    documento, 
    notasRelacionadas, 
    onEnviarComentario, 
    onAprobar, 
    onSolicitarCambios,
    esAsesor, 
    baseURL 
}) => {
    const [mostrarHilo, setMostrarHilo] = useState(false);
    const [nuevoComentario, setNuevoComentario] = useState("");
    const [enviando, setEnviando] = useState(false);

    const handleEnviar = async (e) => {
        e.preventDefault();
        if (!nuevoComentario.trim()) return;
        
        setEnviando(true);
        await onEnviarComentario(documento.id, nuevoComentario); 
        setNuevoComentario("");
        setEnviando(false);
    };

    // --- CORRECCIÓN 1: ORDENAR MENSAJES CRONOLÓGICAMENTE ---
    // Ordenamos ascendente (el más viejo primero) para que se lea como una conversación natural
    const notasOrdenadas = [...notasRelacionadas].sort((a, b) => 
        new Date(a.fecha_creacion) - new Date(b.fecha_creacion)
    );

    // --- CORRECCIÓN 2: FORMATEAR FECHA DEL DOCUMENTO ---
    // Intentamos usar fecha_creacion, si no existe (algunos docs viejos), usamos fecha actual o fallback
    const fechaDocumento = documento.fecha_creacion 
        ? new Date(documento.fecha_creacion).toLocaleString('es-CO') 
        : (documento.fecha ? new Date(documento.fecha).toLocaleString('es-CO') : "Fecha no disponible");

    return (
        <div className="documento-item-contenedor">
            {/* --- CABECERA DEL DOCUMENTO --- */}
            <div className="documento-cabecera">
                <span className="icono-doc">📄</span>
                <div className="info-doc">
                    <strong>{documento.nombre_archivo}</strong>
                    <br/>
                    
                    {/* AQUI AGREGAMOS LA FECHA VISIBLE EN LA TARJETA PRINCIPAL */}
                    <div className="metadata-doc">
                        <small>Subido por: {documento.autor_nombre}</small>
                        <span className="separador">•</span>
                        <small className="fecha-doc">{fechaDocumento}</small>
                    </div>

                    <div className="acciones-doc">
                        <a href={`${baseURL}${documento.ruta_archivo}`} target="_blank" rel="noopener noreferrer" className="btn-descargar">Descargar</a>
                        <button onClick={() => setMostrarHilo(!mostrarHilo)} className="btn-comentarios">
                            💬 {mostrarHilo ? 'Ocultar' : 'Ver'} Comentarios ({notasRelacionadas.length})
                        </button>
                    </div>
                </div>
                
                <div className="estado-doc">
                    <span className={`badge-estado ${documento.estado}`}>{documento.estado.replace('_', ' ')}</span>
                    {esAsesor && documento.estado === 'en_revision' && (
                        <div className="botones-revision-mini">
                            <button onClick={() => onAprobar(documento.id)} className="btn-ok" title="Aprobar">Aprobar</button>
                            <button onClick={() => onSolicitarCambios(documento.id)} className="btn-x" title="Solicitar Cambios">Devolver</button>
                        </div>
                    )}
                </div>
            </div>

            {/* --- HILO DE COMENTARIOS (DESPLEGABLE) --- */}
            {mostrarHilo && (
                <div className="hilo-comentarios">
                    {notasOrdenadas.length === 0 ? (
                        <p className="sin-comentarios">No hay comentarios sobre este documento.</p>
                    ) : (
                        notasOrdenadas.map(nota => (
                            <div key={nota.id} className={`burbuja-hilo ${nota.rol_autor === 'asesor' ? 'asesor' : 'estudiante'}`}>
                                <div className="burbuja-header">
                                    <strong>{nota.autor_nombre}</strong>
                                    <span className="burbuja-fecha">{new Date(nota.fecha_creacion).toLocaleString()}</span>
                                </div>
                                <div className="burbuja-body">
                                    {nota.contenido}
                                </div>
                            </div>
                        ))
                    )}

                    <form onSubmit={handleEnviar} className="form-hilo">
                        <input 
                            type="text" 
                            value={nuevoComentario} 
                            onChange={(e) => setNuevoComentario(e.target.value)} 
                            placeholder="Escribe un comentario específico..."
                            disabled={enviando}
                        />
                        <button type="submit" disabled={enviando}>➤</button>
                    </form>
                </div>
            )}
        </div>
    );
};

export default DocumentoConHilo;