import React, { useState } from "react";
import { useAuth } from "../../../contextos/ContextoAutenticacion";
import { usePanelAdministracionLogic } from "./usePanelAdministracionLogic";
import "./PanelAdministracion.css";
import CampoContrasena from "../../compartidos/CampoContrasena";

const PanelAdministracion = () => {
   const { usuario } = useAuth();
   // Usamos tu hook existente que ya tiene toda la lógica
   const {
    listaPersonal, listaAreas, listaUsuarios, nuevoPersonal, nuevaAreaNombre,
    setNuevaAreaNombre, areaAEditar, setAreaAEditar, modalVisible, personaAEditar,
    datosFormularioEdicion, cargando, error, setError,
    handleInputChange, handleSubmit, handleCambiarEstado, handleAbrirModal,
    handleCerrarModal, handleInputChangeModal, handleSubmitEdicion,
    handleEliminar, handleCrearArea, handleEliminarArea, handleIniciarEdicionArea,
    handleCancelarEdicionArea, handleGuardarEdicionArea, handleCambiarEstadoUsuario,
    asesorSeleccionadoId, estudiantesSeleccionadosIds, handleAsesorChange,
    handleEstudianteCheckboxChange, handleGuardarAsignacion,
  } = usePanelAdministracionLogic();

   // Estado local para controlar las pestañas
   const [pestanaActiva, setPestanaActiva] = useState('personal'); // 'personal', 'usuarios', 'configuracion'

   const asesores = listaPersonal.filter(p => p.rol === 'asesor');
   const estudiantes = listaPersonal.filter(p => p.rol === 'estudiante');

 return (
    <div className="panel-admin-contenedor">
      <div className="admin-saludo">
        <h1>Bienvenido, {usuario?.nombre_completo}</h1>
        <p>Panel de Control Maestro</p>
      </div>

      {error && <div className="mensaje-error" onClick={() => setError(null)}>Error: {error} (X)</div>}

       {/* --- NUEVO: INDICADOR DE CARGA (Para usar la variable 'cargando') --- */}
      {cargando && <p className="indicador-carga">⏳ Cargando datos del sistema...</p>}
      {/* ------------------------------------------------------------------- */}

      {/* --- NAVEGACIÓN POR PESTAÑAS --- */}
      <div className="admin-tabs">
        <button 
            className={`tab-btn ${pestanaActiva === 'personal' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('personal')}
        >
            👥 Gestión de Personal
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'usuarios' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('usuarios')}
        >
            👤 Ciudadanos Registrados
        </button>
        <button 
            className={`tab-btn ${pestanaActiva === 'configuracion' ? 'active' : ''}`}
            onClick={() => setPestanaActiva('configuracion')}
        >
            ⚙️ Configuración del Sistema
        </button>
      </div>

      <div className="admin-contenido-pestana">
        
        {/* ================================================================= */}
        {/* PESTAÑA 1: GESTIÓN DE PERSONAL (Crear, Listar, Asignar) */}
        {/* ================================================================= */}
        {pestanaActiva === 'personal' && (
            <>
                {/* 1.1 Crear Nuevo */}
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

                {/* 1.2 Asignación de Supervisores */}
                <div className="gestion-seccion">
                    <h2>Asignación de Supervisores</h2>
                    <div className="asignacion-contenedor">
                        <div className="asignacion-columna">
                            <label><strong>1. Seleccione Supervisor:</strong></label>
                            <select value={asesorSeleccionadoId} onChange={handleAsesorChange}>
                                <option value="">-- Elija un asesor --</option>
                                {asesores.map(a => <option key={a.id_cuenta} value={a.id_cuenta}>{a.nombre_completo}</option>)}
                            </select>
                        </div>
                        <div className="asignacion-columna">
                            <label><strong>2. Estudiantes a cargo:</strong></label>
                            <div className="lista-estudiantes-checkbox">
                                {asesorSeleccionadoId ? (
                                    estudiantes.map(est => (
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

                {/* 1.3 Lista de Personal */}
                <div className="gestion-seccion">
                    <h2>Directorio de Personal</h2>
                    <table className="tabla-personal">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Rol</th>
                                <th>Especialidad</th>
                                <th>Supervisor</th>
                                <th>Estado</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {listaPersonal.map((p) => (
                            <tr key={p.id_cuenta}>
                                <td>{p.nombre_completo}<br/><small>{p.email}</small></td>
                                <td><span className={`badge-rol ${p.rol}`}>{p.rol}</span></td>
                                <td>{p.area_especialidad}</td>
                                <td>{p.rol === 'estudiante' ? (p.nombre_supervisor || '-') : 'N/A'}</td>
                                <td><span className={p.esta_activo ? 'estado-activo' : 'estado-inactivo'}>{p.esta_activo ? "Activo" : "Inactivo"}</span></td>
                                <td className="celda-acciones">
                                    <button onClick={() => handleAbrirModal(p)} className="boton-editar">✏️</button>
                                    <button onClick={() => handleCambiarEstado(p.id_cuenta)} className="boton-estado">🔄</button>
                                    <button onClick={() => handleEliminar(p.id_cuenta)} className="boton-eliminar">🗑️</button>
                                </td>
                            </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </>
        )}

        {/* ================================================================= */}
        {/* PESTAÑA 2: USUARIOS (CIUDADANOS) */}
        {/* ================================================================= */}
        {pestanaActiva === 'usuarios' && (
            <div className="gestion-seccion">
                <h2>Cuentas de Ciudadanos</h2>
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
                            <td><span className={u.esta_activo ? 'estado-activo' : 'estado-inactivo'}>{u.esta_activo ? "Activo" : "Inactivo"}</span></td>
                            <td className="celda-acciones">
                                <button onClick={() => handleAbrirModal(u)} className="boton-editar">Editar Datos</button>
                                <button onClick={() => handleCambiarEstadoUsuario(u.id_cuenta)} className="boton-estado">
                                    {u.esta_activo ? "Desactivar" : "Activar"}
                                </button>
                            </td>
                        </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        )}

        {/* ================================================================= */}
        {/* PESTAÑA 3: CONFIGURACIÓN (ÁREAS) */}
        {/* ================================================================= */}
        {pestanaActiva === 'configuracion' && (
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
                                    <button onClick={() => handleIniciarEdicionArea(area)} className="boton-editar">Editar</button>
                                    <button onClick={() => handleEliminarArea(area.id)} className="boton-eliminar">Eliminar</button>
                                </td>
                            </>
                            )}
                        </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        )}

      </div>

      {/* ================================================================= */}
      {/* MODAL DE EDICIÓN (COMPARTIDO) */}
      {/* ================================================================= */}
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