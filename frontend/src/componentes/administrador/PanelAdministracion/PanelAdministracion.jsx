// C:\react\asistente_legal_multimodal\frontend\src\componentes\administrador\PanelAdministracion\PanelAdministracion.jsx

import React from "react";
import { useAuth } from "../../../contextos/ContextoAutenticacion";
import { usePanelAdministracionLogic } from "./usePanelAdministracionLogic"; // Importamos nuestro Hook
import "./PanelAdministracion.css";

const PanelAdministracion = () => {
   const { usuario } = useAuth();
  // Obtenemos todos los estados y funciones desde nuestro Hook de lógica
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


   const asesores = listaPersonal.filter(p => p.rol === 'asesor');
  const estudiantes = listaPersonal.filter(p => p.rol === 'estudiante');

  // El componente ahora solo se encarga de renderizar el JSX
 return (
    <div className="panel-admin-contenedor">
      <div className="admin-saludo">
        <h1>Bienvenido, {usuario?.nombre_completo}</h1>
        <p>Desde aquí puede gestionar el personal y la configuración del sistema.</p>
      </div>
      <h1>Panel de Administración</h1>
      {error && <p className="mensaje-error" onClick={() => setError(null)}>Error: {error} (clic para cerrar)</p>}

      {/* SECCION DE GESTION DE AREAS */}
      <div className="gestion-seccion">
        <h2>Gestión de Áreas de Especialidad</h2>
        <div className="area-creacion-fila">
          <form onSubmit={handleCrearArea} className="area-form">
            <input
              type="text"
              value={nuevaAreaNombre}
              onChange={(e) => setNuevaAreaNombre(e.target.value)}
              placeholder="Nombre de la nueva área"
              required
            />
            <button type="submit">Crear Área</button>
          </form>
        </div>
        <table className="tabla-areas">
          <thead>
            <tr>
              <th>Nombre del Área</th>
              <th style={{ width: "200px" }}>Acciones</th>
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

      {/* SECCION DE ASIGNACION DE SUPERVISORES (CON LOGICA DE FILTRADO MEJORADA) */}
      <div className="gestion-seccion">
        <h2>Asignación de Supervisores</h2>
        <div className="asignacion-contenedor">
          <div className="asignacion-columna">
            <label htmlFor="asesor-select"><strong>1. Seleccione un Asesor Supervisor:</strong></label>
            <select id="asesor-select" value={asesorSeleccionadoId} onChange={handleAsesorChange}>
              <option value="">-- Elija un asesor --</option>
              {asesores.map(asesor => (
                <option key={asesor.id_cuenta} value={asesor.id_cuenta}>
                  {asesor.nombre_completo}
                </option>
              ))}
            </select>
          </div>
          <div className="asignacion-columna">
            <label><strong>2. Asigne los Estudiantes a su cargo:</strong></label>
            <div className="lista-estudiantes-checkbox">
              {asesorSeleccionadoId ? (
                (() => {
                  const asesorSeleccionado = asesores.find(a => a.id_cuenta === parseInt(asesorSeleccionadoId));
                  const estudiantesFiltrados = estudiantes.filter(estudiante => 
                    !estudiante.nombre_supervisor || (asesorSeleccionado && estudiante.nombre_supervisor === asesorSeleccionado.nombre_completo)
                  );

                  if (estudiantesFiltrados.length === 0) {
                    return <p>No hay estudiantes disponibles para asignar a este asesor.</p>;
                  }

                  return estudiantesFiltrados.map(estudiante => (
                    <div key={estudiante.id_cuenta} className="checkbox-item">
                      <input type="checkbox" id={`estudiante-${estudiante.id_cuenta}`} checked={estudiantesSeleccionadosIds.has(estudiante.id_cuenta)} onChange={() => handleEstudianteCheckboxChange(estudiante.id_cuenta)} />
                      <label htmlFor={`estudiante-${estudiante.id_cuenta}`}>{estudiante.nombre_completo}</label>
                    </div>
                  ));
                })()
              ) : <p>Por favor, seleccione un asesor para ver los estudiantes.</p>}
            </div>
          </div>
        </div>
        <div className="asignacion-acciones">
          <button onClick={handleGuardarAsignacion} disabled={!asesorSeleccionadoId}>Guardar Asignación</button>
        </div>
      </div>

      {/* SECCION DE GESTION DE PERSONAL (TABLA MODIFICADA) */}
      <div className="gestion-seccion">
        <h2>Gestión de Personal del Sistema</h2>
        <div className="form-creacion-seccion">
            <h3>Crear Nuevo Personal</h3>
            <form onSubmit={handleSubmit}>
              <div className="form-grupo"><label>Email:</label><input type="email" name="email" value={nuevoPersonal.email} onChange={handleInputChange} required /></div>
              <div className="form-grupo"><label>Contraseña:</label><input type="password" name="contrasena" value={nuevoPersonal.contrasena} onChange={handleInputChange} required /></div>
              <div className="form-grupo"><label>Nombre Completo:</label><input type="text" name="nombre_completo" value={nuevoPersonal.nombre_completo} onChange={handleInputChange} required /></div>
              <div className="form-grupo">
                  <label>Área de Especialidad:</label>
                  <select name="id_area_especialidad" value={nuevoPersonal.id_area_especialidad} onChange={handleInputChange}>
                  {listaAreas.map(area => (<option key={area.id} value={area.id}>{area.nombre}</option>))}
                  </select>
              </div>
              <div className="form-grupo"><label>Rol:</label><select name="rol" value={nuevoPersonal.rol} onChange={handleInputChange}><option value="estudiante">Estudiante</option><option value="asesor">Asesor</option></select></div>
              <button type="submit">Crear Cuenta</button>
            </form>
        </div>
        {cargando ? <p>Cargando lista de personal...</p> : (
            <table className="tabla-personal">
            <thead>
                <tr>
                    <th>Nombre Completo</th>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Especialidad</th>
                    <th>Supervisor</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {listaPersonal.map((persona) => (
                <tr key={persona.id_cuenta}>
                    <td>{persona.nombre_completo}</td>
                    <td>{persona.email}</td>
                    <td>{persona.rol}</td>
                    <td>{persona.area_especialidad}</td>
                    <td>{persona.rol === 'estudiante' ? (persona.nombre_supervisor || <span style={{color: 'gray'}}>No asignado</span>) : 'N/A'}</td>
                    <td><span className={persona.esta_activo ? 'estado-activo' : 'estado-inactivo'}>{persona.esta_activo ? "Activo" : "Inactivo"}</span></td>
                    <td className="celda-acciones">
                        <button onClick={() => handleAbrirModal(persona)} className="boton-editar">Editar</button>
                        <button onClick={() => handleCambiarEstado(persona.id_cuenta)} className={persona.esta_activo ? 'boton-desactivar' : 'boton-activar'}>{persona.esta_activo ? "Desactivar" : "Activar"}</button>
                        <button onClick={() => handleEliminar(persona.id_cuenta)} className="boton-eliminar">Eliminar</button>
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        )}
      </div>

      {/* SECCION DE GESTION DE USUARIOS (CIUDADANOS) */}
      <div className="gestion-seccion">
        <h2>Gestión de Cuentas de Ciudadanos</h2>
        {cargando ? <p>Cargando lista de usuarios...</p> : (
            <table className="tabla-personal">
            <thead>
                <tr>
                    <th>Nombre Completo</th>
                    <th>Email</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
                {listaUsuarios.map((usuario) => (
                <tr key={usuario.id_cuenta}>
                    <td>{usuario.nombre_completo}</td>
                    <td>{usuario.email}</td>
                    <td><span className={usuario.esta_activo ? 'estado-activo' : 'estado-inactivo'}>{usuario.esta_activo ? "Activo" : "Inactivo"}</span></td>
                    <td className="celda-acciones">
                    <button onClick={() => handleCambiarEstadoUsuario(usuario.id_cuenta)} className={usuario.esta_activo ? 'boton-desactivar' : 'boton-activar'}>{usuario.esta_activo ? "Desactivar" : "Activar"}</button>
                    </td>
                </tr>
                ))}
            </tbody>
            </table>
        )}
      </div>

      {/* MODAL DE EDICION DE PERSONAL */}
      {modalVisible && personaAEditar && (
        <div className="modal-overlay">
          <div className="modal-contenido">
            <h2>Editando a: {personaAEditar.nombre_completo}</h2>
            <form onSubmit={handleSubmitEdicion}>
              <div className="form-grupo"><label>Nombre Completo:</label><input type="text" name="nombre_completo" value={datosFormularioEdicion.nombre_completo} onChange={handleInputChangeModal} required /></div>
              <div className="form-grupo">
                <label>Área de Especialidad:</label>
                <select name="id_area_especialidad" value={datosFormularioEdicion.id_area_especialidad} onChange={handleInputChangeModal}>
                  {listaAreas.map(area => (<option key={area.id} value={area.id}>{area.nombre}</option>))}
                </select>
              </div>
              <div className="form-grupo"><label>Email:</label><input type="email" name="email" value={datosFormularioEdicion.email} onChange={handleInputChangeModal} required /></div>
              <div className="form-grupo"><label>Nueva Contraseña (dejar en blanco para no cambiar):</label><input type="password" name="contrasena" value={datosFormularioEdicion.contrasena} onChange={handleInputChangeModal} /></div>
              <div className="modal-acciones">
                <button type="submit" className="boton-guardar">Guardar Cambios</button>
                <button type="button" onClick={handleCerrarModal}>Cancelar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PanelAdministracion;