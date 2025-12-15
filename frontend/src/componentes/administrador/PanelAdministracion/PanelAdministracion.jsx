import React, { useState } from "react";
import { useAuth } from "../../../contextos/ContextoAutenticacion";
import { usePanelAdministracionLogic } from "./usePanelAdministracionLogic";
import "./PanelAdministracion.css";
import CampoContrasena from "../../compartidos/CampoContrasena";

const PanelAdministracion = () => {
   const { usuario } = useAuth();
   
   // --- DESESTRUCTURACIÓN COMPLETA DEL HOOK (Sin omitir nada) ---
   const {
    listaPersonal, listaAreas, listaUsuarios, nuevoPersonal, nuevaAreaNombre,
    setNuevaAreaNombre, areaAEditar, setAreaAEditar, modalVisible, personaAEditar,
    datosFormularioEdicion, cargando, error, setError,
    handleInputChange, handleSubmit, handleCambiarEstado, handleAbrirModal,
    handleCerrarModal, handleInputChangeModal, handleSubmitEdicion,
    handleEliminar, handleCrearArea, handleEliminarArea, 
    handleIniciarEdicionArea, 
    handleCancelarEdicionArea, 
    handleGuardarEdicionArea, 
    handleCambiarEstadoUsuario,
    asesorSeleccionadoId, estudiantesSeleccionadosIds, handleAsesorChange,
    handleEstudianteCheckboxChange, handleGuardarAsignacion,
  } = usePanelAdministracionLogic();

   // Estado local para controlar las pestañas
   const [pestanaActiva, setPestanaActiva] = useState('personal'); // 'personal', 'usuarios', 'configuracion'

   // --- LÓGICA DE AGRUPACIÓN POR ÁREA (Para el nuevo diseño Grid) ---
   const obtenerPersonalAgrupado = (rol) => {
     const filtrados = listaPersonal.filter(p => p.rol === rol);
     const agrupados = filtrados.reduce((acc, persona) => {
       const area = persona.area_especialidad || 'Sin Área';
       if (!acc[area]) acc[area] = [];
       acc[area].push(persona);
       return acc;
     }, {});
     return agrupados;
   };

   // Calculamos los datos para la vista actual
   const personalAgrupado = obtenerPersonalAgrupado(pestanaActiva === 'asesor' ? 'asesor' : 'estudiante');
   const areasOrdenadas = Object.keys(personalAgrupado).sort();

   // --- FUNCIÓN AUXILIAR PARA RENDERIZAR TARJETAS ---
   const renderTarjetaPersonal = (persona) => (
     <div key={persona.id_cuenta} className="tarjeta-usuario">
        <div className="avatar-rol">
            {persona.rol === 'estudiante' ? '🎓' : '⚖️'}
        </div>
        <div className="info-usuario">
            <h4>{persona.nombre_completo}</h4>
            <span className="email">{persona.email}</span>
            <span className={`badge-estado ${persona.esta_activo ? 'activo' : 'inactivo'}`}>
                {persona.esta_activo ? 'Activo' : 'Inactivo'}
            </span>
            
            {persona.rol === 'estudiante' && (
                <div className="dato-extra">
                    <small>Supervisor:</small><br/>
                    <strong>{persona.nombre_supervisor || 'Sin asignar'}</strong>
                </div>
            )}
        </div>
        <div className="acciones-usuario">
            <button onClick={() => handleAbrirModal(persona)} className="btn-icon editar" title="Editar">✏️</button>
            <button onClick={() => handleCambiarEstado(persona.id_cuenta)} className="btn-icon estado" title="Cambiar Estado">🔄</button>
            <button onClick={() => handleEliminar(persona.id_cuenta)} className="btn-icon eliminar" title="Eliminar">🗑️</button>
        </div>
     </div>
   );

 return (
    <div className="panel-admin-contenedor">
      <div className="admin-saludo">
        <h1>Bienvenido, {usuario?.nombre_completo}</h1>
        <p>Panel de Control Maestro</p>
      </div>

      {error && <div className="mensaje-error" onClick={() => setError(null)}>Error: {error} (X)</div>}
      {cargando && <p className="indicador-carga">⏳ Cargando datos del sistema...</p>}

      {/* --- NAVEGACIÓN POR PESTAÑAS --- */}
      <div className="admin-tabs">
        <button 
            className={`tab-btn ${pestanaActiva === 'personal' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('personal')}
        >
             Estudiantes (Grid)
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'asesor' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('asesor')}
        >
         Asesores (Grid)
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'asignacion' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('asignacion')}
        >
             Asignaciones
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'usuarios' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('usuarios')}
        >
             Ciudadanos
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'configuracion' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('configuracion')}
        >
             Configuración
        </button>
      </div>

      <div className="admin-contenido-pestana">
        
       
        {(pestanaActiva === 'personal' || pestanaActiva === 'asesor') && (
            <div className="vista-directorio">
                {areasOrdenadas.length === 0 ? (
                    <div className="vacio">No hay personal registrado en esta categoría.</div>
                ) : (
                    areasOrdenadas.map(area => (
                        <div key={area} className="seccion-area">
                            <h3 className="titulo-area">{area}</h3>
                            <div className="grid-tarjetas">
                                {personalAgrupado[area].map(renderTarjetaPersonal)}
                            </div>
                        </div>
                    ))
                )}
            </div>
        )}

       
        {pestanaActiva === 'asignacion' && (
            <div className="gestion-seccion">
                <h2>Asignación de Supervisores</h2>
                <div className="asignacion-contenedor">
                    <div className="asignacion-columna">
                        <label><strong>1. Seleccione Supervisor:</strong></label>
                        <select value={asesorSeleccionadoId} onChange={handleAsesorChange}>
                            <option value="">-- Elija un asesor --</option>
                            {listaPersonal.filter(p => p.rol === 'asesor').map(a => (
                                <option key={a.id_cuenta} value={a.id_cuenta}>{a.nombre_completo}</option>
                            ))}
                        </select>
                    </div>
                    <div className="asignacion-columna">
                        <label><strong>2. Estudiantes a cargo:</strong></label>
                        <div className="lista-estudiantes-checkbox">
                            {asesorSeleccionadoId ? (
                                listaPersonal.filter(p => p.rol === 'estudiante').map(est => (
                                    <div key={est.id_cuenta} className="checkbox-item">
                                        <input 
                                            type="checkbox" 
                                            checked={estudiantesSeleccionadosIds.has(est.id_cuenta)} 
                                            onChange={() => handleEstudianteCheckboxChange(est.id_cuenta)} 
                                        />
                                        <label>{est.nombre_completo} <small>({est.nombre_supervisor || 'Sin asignar'})</small></label>
                                    </div>
                                ))
                            ) : <span className="texto-gris">Seleccione un asesor primero.</span>}
                        </div>
                    </div>
                </div>
                <button onClick={handleGuardarAsignacion} disabled={!asesorSeleccionadoId} className="boton-guardar-asignacion">Guardar Asignación</button>
            </div>
        )}

    
        {pestanaActiva === 'usuarios' && (
            <div className="gestion-seccion">
                <h2>Cuentas de Ciudadanos</h2>
                <div className="tabla-responsive">
                    <table className="tabla-personal">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Email</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {listaUsuarios.map((u) => (
                            <tr key={u.id_cuenta}>
                                <td>{u.nombre_completo}</td>
                                <td>{u.email}</td>
                                <td><span className={`badge-estado ${u.esta_activo ? 'activo' : 'inactivo'}`}>{u.esta_activo ? "Activo" : "Inactivo"}</span></td>
                                <td className="celda-acciones">
                                    <button onClick={() => handleAbrirModal(u)} className="btn-icon editar">✏️</button>
                                    <button onClick={() => handleCambiarEstadoUsuario(u.id_cuenta)} className="btn-icon estado">🔄</button>
                                </td>
                            </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        )}

        {pestanaActiva === 'configuracion' && (
            <>
                {/* 1. CREAR PERSONAL */}
                <div className="gestion-seccion">
                    <h2>Registrar Nuevo Colaborador</h2>
                    <div className="form-creacion-seccion">
                        <form onSubmit={handleSubmit} className="form-grid">
                            <div className="form-grupo">
                                <label>Rol:</label>
                                <select name="rol" value={nuevoPersonal.rol} onChange={handleInputChange}>
                                    <option value="estudiante">Estudiante</option>
                                    <option value="asesor">Asesor</option>
                                </select>
                            </div>
                            <div className="form-grupo">
                                <label>Nombre Completo:</label>
                                <input type="text" name="nombre_completo" value={nuevoPersonal.nombre_completo} onChange={handleInputChange} required />
                            </div>
                            <div className="form-grupo">
                                <label>Email Institucional:</label>
                                <input type="email" name="email" value={nuevoPersonal.email} onChange={handleInputChange} required />
                            </div>
                            <div className="form-grupo">
                                <label>Área:</label>
                                <select name="id_area_especialidad" value={nuevoPersonal.id_area_especialidad} onChange={handleInputChange}>
                                {listaAreas.map(area => (<option key={area.id} value={area.id}>{area.nombre}</option>))}
                                </select>
                            </div>
                            <div className="form-grupo">
                                <label>Contraseña:</label>
                                <CampoContrasena name="contrasena" value={nuevoPersonal.contrasena} onChange={handleInputChange} required />
                            </div>
                            <button type="submit" className="boton-crear-personal">Crear Cuenta</button>
                        </form>
                    </div>
                </div>

                {/* 2. ÁREAS */}
                <div className="gestion-seccion">
                    <h2>Áreas de Especialidad Jurídica</h2>
                    <div className="area-creacion-fila">
                        <form onSubmit={handleCrearArea} className="area-form">
                            <input
                                type="text"
                                value={nuevaAreaNombre}
                                onChange={(e) => setNuevaAreaNombre(e.target.value)}
                                placeholder="Nombre de la nueva área..."
                                required
                            />
                            <button type="submit">Agregar Área</button>
                        </form>
                    </div>
                    <table className="tabla-areas">
                        <thead>
                            <tr>
                                <th>Nombre del Área</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {listaAreas.map((area) => (
                            <tr key={area.id}>
                                {areaAEditar && areaAEditar.id === area.id ? (
                                <>
                                    <td>
                                        <form onSubmit={handleGuardarEdicionArea}>
                                            <input
                                            type="text"
                                            value={areaAEditar.nombre}
                                            onChange={(e) => setAreaAEditar({ ...areaAEditar, nombre: e.target.value })}
                                            autoFocus
                                            />
                                        </form>
                                    </td>
                                    <td className="celda-acciones">
                                        <button onClick={handleGuardarEdicionArea} className="boton-guardar">Guardar</button>
                                        <button onClick={handleCancelarEdicionArea}>Cancelar</button>
                                    </td>
                                </>
                                ) : (
                                <>
                                    <td>{area.nombre}</td>
                                    <td className="celda-acciones">
                                        <button onClick={() => handleIniciarEdicionArea(area)} className="btn-icon editar">Editar</button>
                                        <button onClick={() => handleEliminarArea(area.id)} className="btn-icon eliminar">Eliminar</button>
                                    </td>
                                </>
                                )}
                            </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </>
        )}

      </div>

    
      {modalVisible && personaAEditar && (
        <div className="modal-overlay">
          <div className="modal-contenido">
            <h2>Editando: {personaAEditar.nombre_completo}</h2>
            <form onSubmit={handleSubmitEdicion}>
              
              <div className="form-grupo">
                  <label>Nombre Completo:</label>
                  <input type="text" name="nombre_completo" value={datosFormularioEdicion.nombre_completo} onChange={handleInputChangeModal} required />
              </div>
              
              {/* Si es Personal (tiene rol) */}
              {personaAEditar.rol && (
                <>
                  <div className="form-grupo">
                    <label>Especialidad:</label>
                    <select name="id_area_especialidad" value={datosFormularioEdicion.id_area_especialidad} onChange={handleInputChangeModal}>
                      {listaAreas.map(area => (<option key={area.id} value={area.id}>{area.nombre}</option>))}
                    </select>
                  </div>
                  <div className="form-grupo">
                      <label>Email:</label>
                      <input type="email" name="email" value={datosFormularioEdicion.email} onChange={handleInputChangeModal} required />
                  </div>
                </>
              )}

              {/* Si es Usuario (no tiene rol en el objeto listaUsuarios original de la tabla, o lo inferimos) */}
              {!personaAEditar.rol && (
                 <div className="form-grupo">
                     <label>Cédula:</label>
                     <input type="text" name="cedula" value={datosFormularioEdicion.cedula} onChange={handleInputChangeModal} placeholder="Dejar vacío si no cambia" />
                 </div>
              )}

              <div className="form-grupo">
                <label>Nueva Contraseña (Opcional):</label>
                <CampoContrasena
                  name="contrasena"
                  value={datosFormularioEdicion.contrasena}
                  onChange={handleInputChangeModal}
                />
              </div>
              
              <div className="modal-acciones">
                <button type="submit" className="boton-guardar">Guardar Cambios</button>
                <button type="button" onClick={handleCerrarModal} className="boton-cancelar">Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PanelAdministracion;