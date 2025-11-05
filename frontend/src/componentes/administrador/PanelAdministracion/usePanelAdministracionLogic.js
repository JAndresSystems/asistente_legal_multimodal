//C:\react\asistente_legal_multimodal\frontend\src\componentes\administrador\PanelAdministracion\usePanelAdministracionLogic.js
import { useState, useEffect } from "react";
import {
  apiObtenerPersonal, apiCrearPersonal, apiCambiarEstadoCuenta, apiEditarPersonal, apiEliminarPersonal,
  apiObtenerAreas, apiCrearArea, apiEditarArea, apiEliminarArea,
  apiObtenerUsuarios, apiCambiarEstadoCuentaUsuario,apiAsignarSupervisor
} from "../../../servicios/api/administrador";

// Este es nuestro Hook Personalizado. Empieza con "use" por convención.
export const usePanelAdministracionLogic = () => {
  // --- ESTADOS ---
  const [listaPersonal, setListaPersonal] = useState([]);
  const [listaAreas, setListaAreas] = useState([]);
  const [listaUsuarios, setListaUsuarios] = useState([]);
  const [nuevoPersonal, setNuevoPersonal] = useState({ email: "", contrasena: "", nombre_completo: "", id_area_especialidad: "", rol: "estudiante" });
  const [nuevaAreaNombre, setNuevaAreaNombre] = useState("");
  const [areaAEditar, setAreaAEditar] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [personaAEditar, setPersonaAEditar] = useState(null);
  const [datosFormularioEdicion, setDatosFormularioEdicion] = useState({ nombre_completo: "", id_area_especialidad: "", email: "", contrasena: "" });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [asesorSeleccionadoId, setAsesorSeleccionadoId] = useState("");
  const [estudiantesSeleccionadosIds, setEstudiantesSeleccionadosIds] = useState(new Set());
  // --- EFECTO DE CARGA INICIAL ---
   useEffect(() => {
    const cargarDatosIniciales = async () => {
      try {
        setCargando(true);
        setError(null);
        const [personalData, areasData, usuariosData] = await Promise.all([
          apiObtenerPersonal(), apiObtenerAreas(), apiObtenerUsuarios(),
        ]);
        setListaPersonal(personalData);
        setListaAreas(areasData);
        setListaUsuarios(usuariosData);
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







   const cargarPersonal = async () => {
    try {
      // No necesitamos poner 'cargando' aquí para no mostrar el spinner en cada recarga simple
      const data = await apiObtenerPersonal();
      setListaPersonal(data);
    } catch (error) {
      setError(error.message || "Ocurrió un error al recargar los datos del personal.");
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
  
  
  
  
  
     const handleCrearArea = async (e) => {
      e.preventDefault();
      if (!nuevaAreaNombre.trim()) {
        setError("El nombre del área no puede estar vacío.");
        return;
      }
      try {
        setError(null);
        const areaCreada = await apiCrearArea({ nombre: nuevaAreaNombre });
        setListaAreas([...listaAreas, areaCreada]); // Añadimos la nueva area a la lista
        setNuevaAreaNombre(""); // Limpiamos el input
        alert("Área creada exitosamente.");
      } catch (err) {
        setError(err.message);
      }
    };
  
    const handleEliminarArea = async (idArea) => {
      if (!confirm("¿Está seguro de que desea eliminar esta área? Esta acción no se puede deshacer.")) return;
      try {
        setError(null);
        await apiEliminarArea(idArea);
        setListaAreas(listaAreas.filter(area => area.id !== idArea)); // Filtramos el area eliminada
        alert("Área eliminada exitosamente.");
      } catch (err) {
        alert(`Error: ${err.message}`); // Usamos alert para errores criticos de borrado
        setError(err.message);
      }
    };
  
    const handleIniciarEdicionArea = (area) => {
      setAreaAEditar({ ...area }); // Copiamos el area al estado de edicion
    };
  
    const handleCancelarEdicionArea = () => {
      setAreaAEditar(null); // Limpiamos el estado para cancelar
    };
  
    const handleGuardarEdicionArea = async (e) => {
      e.preventDefault();
      try {
        setError(null);
        const areaActualizada = await apiEditarArea(areaAEditar.id, { nombre: areaAEditar.nombre });
        setListaAreas(listaAreas.map(area => area.id === areaAEditar.id ? areaActualizada : area));
        setAreaAEditar(null); // Salimos del modo edicion
        alert("Área actualizada.");
      } catch (err) {
        setError(err.message);
      }
    };
  
  
  
    const handleCambiarEstadoUsuario = async (idCuenta) => {
      if (!confirm("¿Está seguro de que desea cambiar el estado de esta cuenta de usuario?")) return;
  
      try {
        setError(null);
        const usuarioActualizado = await apiCambiarEstadoCuentaUsuario(idCuenta);
        // Actualizamos la lista de usuarios para reflejar el cambio instantáneamente
        setListaUsuarios(listaUsuarios.map(usuario =>
          usuario.id_cuenta === idCuenta ? usuarioActualizado : usuario
        ));
        alert("El estado de la cuenta del usuario ha sido actualizado.");
      } catch (err) {
        setError(err.message);
      }
    };




     const handleAsesorChange = (e) => {
    const idAsesor = e.target.value;
    setAsesorSeleccionadoId(idAsesor);

    if (idAsesor) {
      // Buscamos el nombre completo del asesor seleccionado
      const asesor = listaPersonal.find(p => p.id_cuenta === parseInt(idAsesor));
      // Filtramos los estudiantes que ya están asignados a este asesor
      const idsAsignados = listaPersonal
        .filter(p => p.rol === 'estudiante' && p.nombre_supervisor === asesor.nombre_completo)
        .map(p => p.id_cuenta);
      setEstudiantesSeleccionadosIds(new Set(idsAsignados));
    } else {
      setEstudiantesSeleccionadosIds(new Set()); // Limpiamos la selección si no hay asesor
    }
  };

  const handleEstudianteCheckboxChange = (idEstudiante) => {
    const nuevosIds = new Set(estudiantesSeleccionadosIds);
    if (nuevosIds.has(idEstudiante)) {
      nuevosIds.delete(idEstudiante);
    } else {
      nuevosIds.add(idEstudiante);
    }
    setEstudiantesSeleccionadosIds(nuevosIds);
  };

  const handleGuardarAsignacion = async () => {
    if (!asesorSeleccionadoId) {
      setError("Por favor, seleccione un asesor supervisor.");
      return;
    }
    try {
      setError(null);
      await apiAsignarSupervisor({
        id_asesor: parseInt(asesorSeleccionadoId),
        ids_estudiantes: Array.from(estudiantesSeleccionadosIds),
      });
      alert("Asignación de supervisión guardada exitosamente.");
      // Recargamos el personal para que la tabla principal muestre los cambios
      cargarPersonal();
    } catch (err) {
      setError(err.message);
    }
  };


 return {
    listaPersonal, listaAreas, listaUsuarios, nuevoPersonal, nuevaAreaNombre,
    setNuevaAreaNombre, areaAEditar, setAreaAEditar, modalVisible, personaAEditar,
    datosFormularioEdicion, cargando, error, setError,
    handleInputChange, handleSubmit, handleCambiarEstado, handleAbrirModal,
    handleCerrarModal, handleInputChangeModal, handleSubmitEdicion,
    handleEliminar, handleCrearArea, handleEliminarArea, handleIniciarEdicionArea,
    handleCancelarEdicionArea, handleGuardarEdicionArea, handleCambiarEstadoUsuario,
    // --- 4. EXPORTAMOS LO NUEVO ---
    asesorSeleccionadoId,
    estudiantesSeleccionadosIds,
    handleAsesorChange,
    handleEstudianteCheckboxChange,
    handleGuardarAsignacion,
  };
};


