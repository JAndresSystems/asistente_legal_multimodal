//C:\react\asistente_legal_multimodal\frontend\src\componentes\administrador\PanelAdministracion\PanelAdministracion.jsx
import React, { useState, useEffect } from "react";
import {
  apiObtenerPersonal,
  apiCrearPersonal,
  apiCambiarEstadoCuenta, 
  apiEditarPersonal,
  apiEliminarPersonal,
  apiObtenerAreas, 
} from "../../../servicios/api/administrador";

import "./PanelAdministracion.css";


const PanelAdministracion = () => {
   const [listaAreas, setListaAreas] = useState([]);
  const [listaPersonal, setListaPersonal] = useState([]);
  const [nuevoPersonal, setNuevoPersonal] = useState({
    email: "",
    contrasena: "",
    nombre_completo: "",
    area_especialidad: "",
    rol: "estudiante",
  });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);



   const [modalVisible, setModalVisible] = useState(false);
  const [personaAEditar, setPersonaAEditar] = useState(null);
  const [datosFormularioEdicion, setDatosFormularioEdicion] = useState({
    nombre_completo: "",
    area_especialidad: "",
    email: "",
    contrasena: "", // Este campo es para la *nueva* contraseña
  });


useEffect(() => {
    const cargarDatosIniciales = async () => {
      try {
        setCargando(true);
        setError(null);
        const [personalData, areasData] = await Promise.all([
          apiObtenerPersonal(),
          apiObtenerAreas(),
        ]);
        setListaPersonal(personalData);
        setListaAreas(areasData);
        // Pre-seleccionar la primera área en el formulario de creación
        if (areasData.length > 0) {
          setNuevoPersonal(prev => ({ ...prev, id_area_especialidad: areasData[0].id }));
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setCargando(false);
      }
    };
    cargarDatosIniciales();
  }, []);




  useEffect(() => {
    cargarPersonal();
  }, []);

  const cargarPersonal = async () => {
    try {
      setCargando(true);
      setError(null);
      const data = await apiObtenerPersonal();
      setListaPersonal(data);
    } catch (error) {
      setError(
        error.message ||
          "Ocurrió un error al cargar los datos del personal."
      );
    } finally {
      setCargando(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNuevoPersonal((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

 const handleSubmit = async (e) => {
    e.preventDefault();
    // --- INICIO DE LA CORRECCION ---
    // La validación ahora comprueba 'id_area_especialidad'.
    if (!nuevoPersonal.email || !nuevoPersonal.contrasena || !nuevoPersonal.nombre_completo || !nuevoPersonal.id_area_especialidad) {
      setError("Todos los campos son obligatorios.");
      return;
    }
    // --- FIN DE LA CORRECCION ---
    try {
      setError(null);
      await apiCrearPersonal(nuevoPersonal);
      alert("Personal creado exitosamente.");
      // Limpiamos el formulario y volvemos a cargar los datos
      const idAreaDefault = listaAreas.length > 0 ? listaAreas[0].id : "";
      setNuevoPersonal({ email: "", contrasena: "", nombre_completo: "", id_area_especialidad: idAreaDefault, rol: "estudiante" });
      cargarPersonal(); // Función simplificada para solo recargar personal
    } catch (err) {
      setError(err.message || "Error al crear el nuevo personal.");
    }
  };


const handleCambiarEstado = async (idCuenta) => {
    // Preguntamos para seguridad, es una buena práctica.
    if (!confirm("¿Está seguro de que desea cambiar el estado de esta cuenta?")) {
      return;
    }

    try {
      setError(null);
      const perfilActualizado = await apiCambiarEstadoCuenta(idCuenta);
      
      // Actualizamos el estado local para reflejar el cambio en la UI al instante,
      // sin necesidad de volver a cargar toda la lista desde el servidor.
      setListaPersonal(listaPersonal.map(persona => 
        persona.id_cuenta === idCuenta ? perfilActualizado : persona
      ));

      alert("El estado de la cuenta ha sido actualizado exitosamente.");

    } catch (error) {
      setError(error.message || "Error al actualizar el estado de la cuenta.");
      // Mostramos el error en la UI, pero no detenemos la aplicación.
    }
  };




  const handleAbrirModal = (persona) => {
    setPersonaAEditar(persona);
    
    // Buscamos el objeto 'area' completo que corresponde al nombre del área de la persona.
    const areaActual = listaAreas.find(area => area.nombre === persona.area_especialidad);
    // Obtenemos su ID. Si no lo encontramos, dejamos el campo vacío.
    const idAreaActual = areaActual ? areaActual.id : "";

    setDatosFormularioEdicion({
      nombre_completo: persona.nombre_completo,
      // Usamos el ID que acabamos de encontrar para inicializar el formulario.
      id_area_especialidad: idAreaActual,
      email: persona.email,
      contrasena: "", 
    });
    setModalVisible(true);
  };

  const handleCerrarModal = () => {
    setModalVisible(false);
    setPersonaAEditar(null);
  };

  const handleInputChangeModal = (e) => {
    const { name, value } = e.target;
    setDatosFormularioEdicion(prevState => ({ ...prevState, [name]: value }));
  };

  const handleSubmitEdicion = async (e) => {
    e.preventDefault();
    
    // Preparamos los datos: solo enviamos los campos que tienen valor.
    // Si la contraseña está vacía, no se envía, y el backend no la cambiará.
    const datosParaEnviar = { ...datosFormularioEdicion };
    if (!datosParaEnviar.contrasena) {
      delete datosParaEnviar.contrasena;
    }

    try {
      setError(null);
      const perfilActualizado = await apiEditarPersonal(personaAEditar.id_cuenta, datosParaEnviar);
      setListaPersonal(listaPersonal.map(p => (p.id_cuenta === personaAEditar.id_cuenta ? perfilActualizado : p)));
      alert("Personal actualizado exitosamente.");
      handleCerrarModal();
    } catch (error) {
      // Idealmente, mostraríamos este error dentro del modal
      alert(`Error al actualizar: ${error.message}`);
      setError(error.message);
    }
  };

  const handleEliminar = async (idCuenta) => {
    if (!confirm("¡ADVERTENCIA!\n¿Está seguro de que desea ELIMINAR permanentemente esta cuenta?\nEsta acción no se puede deshacer.")) {
      return;
    }

    try {
      setError(null);
      await apiEliminarPersonal(idCuenta);
      // Actualizamos la lista filtrando la persona eliminada.
      setListaPersonal(listaPersonal.filter(p => p.id_cuenta !== idCuenta));
      alert("La cuenta ha sido eliminada exitosamente.");
    } catch (error) {
      setError(error.message);
    }
  };





  return (
    <div className="panel-admin-contenedor">
      <h1>Panel de Administración</h1>
      <p>Gestión de cuentas de Estudiantes y Asesores.</p>

      {/* --- Formulario de Creación --- */}
      <div className="form-creacion-seccion">
        <h2>Crear Nuevo Personal</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-grupo"><label>Email:</label><input type="email" name="email" value={nuevoPersonal.email} onChange={handleInputChange} required /></div>
          <div className="form-grupo"><label>Contraseña:</label><input type="password" name="contrasena" value={nuevoPersonal.contrasena} onChange={handleInputChange} required /></div>
          <div className="form-grupo"><label>Nombre Completo:</label><input type="text" name="nombre_completo" value={nuevoPersonal.nombre_completo} onChange={handleInputChange} required /></div>
          
          {/* --- INICIO DE LA CORRECCION: Reemplazar input de texto por menú desplegable --- */}
          <div className="form-grupo">
            <label>Área de Especialidad:</label>
            <select name="id_area_especialidad" value={nuevoPersonal.id_area_especialidad} onChange={handleInputChange}>
              {listaAreas.map(area => (
                <option key={area.id} value={area.id}>{area.nombre}</option>
              ))}
            </select>
          </div>
          {/* --- FIN DE LA CORRECCION --- */}

          <div className="form-grupo"><label>Rol:</label><select name="rol" value={nuevoPersonal.rol} onChange={handleInputChange}><option value="estudiante">Estudiante</option><option value="asesor">Asesor</option></select></div>
          <button type="submit">Crear Cuenta</button>
        </form>
      </div>

      {/* --- Tabla de Personal del Sistema --- */}
      <h2>Personal del Sistema</h2>
      {cargando && <p>Cargando lista de personal...</p>}
      {error && <p className="mensaje-error">Error: {error}</p>}
      {!cargando && !error && (
        <table className="tabla-personal">
          <thead>
            <tr>
              <th>Nombre Completo</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Especialidad</th>
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
                <td>
                  <span className={persona.esta_activo ? 'estado-activo' : 'estado-inactivo'}>
                    {persona.esta_activo ? "Activo" : "Inactivo"}
                  </span>
                </td>
                <td className="celda-acciones">
                  <button onClick={() => handleAbrirModal(persona)} className="boton-editar">Editar</button>
                  <button onClick={() => handleCambiarEstado(persona.id_cuenta)} className={persona.esta_activo ? 'boton-desactivar' : 'boton-activar'}>
                    {persona.esta_activo ? "Desactivar" : "Activar"}
                  </button>
                  <button onClick={() => handleEliminar(persona.id_cuenta)} className="boton-eliminar">Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* --- Modal de Edición --- */}
      {modalVisible && personaAEditar && (
        <div className="modal-overlay">
          <div className="modal-contenido">
            <h2>Editando a: {personaAEditar.nombre_completo}</h2>
            <form onSubmit={handleSubmitEdicion}>
              <div className="form-grupo"><label>Nombre Completo:</label><input type="text" name="nombre_completo" value={datosFormularioEdicion.nombre_completo} onChange={handleInputChangeModal} required /></div>
              
              {/* --- INICIO DE LA CORRECCION: Reemplazar input de texto por menú desplegable --- */}
              <div className="form-grupo">
                <label>Área de Especialidad:</label>
                <select name="id_area_especialidad" value={datosFormularioEdicion.id_area_especialidad} onChange={handleInputChangeModal}>
                  {listaAreas.map(area => (
                    <option key={area.id} value={area.id}>{area.nombre}</option>
                  ))}
                </select>
              </div>
              {/* --- FIN DE LA CORRECCION --- */}

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