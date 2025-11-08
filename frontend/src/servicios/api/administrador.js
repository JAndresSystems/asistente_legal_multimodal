//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\administrador.js
import { URL_BASE_BACKEND, obtenerCabeceras } from "./config";

/**
 * Llama al endpoint del backend para obtener la lista completa de Estudiantes y Asesores.
 * Requiere un token de administrador.
 * @returns {Promise<Array>} Una promesa que se resuelve con la lista del personal.
 */
export const apiObtenerPersonal = async () => {
  const respuesta = await fetch(`${URL_BASE_BACKEND}/api/administrador/personal`, {
    method: "GET",
    headers: obtenerCabeceras(),
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(
      error.detail || "No se pudo obtener la lista de personal."
    );
  }
  return respuesta.json();
};

/**
 * Llama al endpoint del backend para crear una nueva cuenta de Estudiante o Asesor.
 * Requiere un token de administrador.
 * @param {Object} datosPersonal - El objeto con los datos del nuevo personal.
 * @param {string} datosPersonal.email
 * @param {string} datosPersonal.contrasena
 * @param {string} datosPersonal.nombre_completo
 * @param {string} datosPersonal.area_especialidad
 * @param {string} datosPersonal.rol - Debe ser 'estudiante' o 'asesor'.
 * @returns {Promise<Object>} Una promesa que se resuelve con los datos del personal creado.
 */
export const apiCrearPersonal = async (datosPersonal) => {
  const respuesta = await fetch(`${URL_BASE_BACKEND}/api/administrador/personal`, {
    method: "POST",
    headers: obtenerCabeceras(),
    body: JSON.stringify(datosPersonal),
  });

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al crear el nuevo personal.");
  }
  return respuesta.json();
};




/**
 * Llama al endpoint para activar o desactivar una cuenta de personal.
 * @param {number} idCuenta - El ID de la cuenta a modificar.
 * @returns {Promise<Object>} Una promesa que se resuelve con los datos actualizados del perfil.
 */
export const apiCambiarEstadoCuenta = async (idCuenta) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/personal/${idCuenta}/cambiar-estado`,
    {
      method: "POST",
      headers: obtenerCabeceras(),
      // Esta petición no necesita un 'body', la acción está implícita en la URL.
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al cambiar el estado de la cuenta.");
  }
  return respuesta.json();
};



/**
 * Llama al endpoint para actualizar los datos de una cuenta de personal.
 * @param {number} idCuenta - El ID de la cuenta a modificar.
 * @param {Object} datosEdicion - Un objeto con los campos a actualizar.
 * @returns {Promise<Object>} Una promesa que se resuelve con los datos actualizados del perfil.
 */
export const apiEditarPersonal = async (idCuenta, datosEdicion) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/personal/${idCuenta}`,
    {
      method: "PUT", // Usamos el método PUT para actualizar
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosEdicion),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al editar la cuenta del personal.");
  }
  return respuesta.json();
};

/**
 * Llama al endpoint para eliminar permanentemente una cuenta de personal.
 * @param {number} idCuenta - El ID de la cuenta a eliminar.
 * @returns {Promise<void>} Una promesa que se resuelve si la eliminación es exitosa.
 */
export const apiEliminarPersonal = async (idCuenta) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/personal/${idCuenta}`,
    {
      method: "DELETE", // Usamos el método DELETE para eliminar
      headers: obtenerCabeceras(),
    }
  );

  // Para DELETE, una respuesta exitosa puede no tener cuerpo (status 204).
  // Por lo tanto, solo verificamos si la respuesta no es 'ok'.
  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al eliminar la cuenta del personal.");
  }
  // No es necesario retornar respuesta.json() porque no hay contenido.
};



/**
 * Llama al endpoint para obtener la lista de todas las Áreas de Especialidad.
 * @returns {Promise<Array>} Una promesa que se resuelve con la lista de áreas.
 */
export const apiObtenerAreas = async () => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/areas-especialidad`,
    {
      method: "GET",
      headers: obtenerCabeceras(),
    }
  );
  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al obtener las áreas de especialidad.");
  }
  return respuesta.json();
};




/**
 * Llama al endpoint para crear una nueva Area de Especialidad.
 * @param {Object} datosArea - Un objeto que debe contener el nombre del área. Ej: { nombre: "Derecho Ambiental" }
 * @returns {Promise<Object>} Una promesa que se resuelve con el objeto del área creada.
 */
export const apiCrearArea = async (datosArea) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/areas-especialidad`,
    {
      method: "POST",
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosArea),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al crear el área.");
  }
  return respuesta.json();
};

/**
 * Llama al endpoint para actualizar el nombre de un Area de Especialidad.
 * @param {number} idArea - El ID del área a modificar.
 * @param {Object} datosArea - Un objeto con el nuevo nombre. Ej: { nombre: "Nuevo Nombre" }
 * @returns {Promise<Object>} Una promesa que se resuelve con el objeto del área actualizada.
 */
export const apiEditarArea = async (idArea, datosArea) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/areas-especialidad/${idArea}`,
    {
      method: "PUT",
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosArea),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al actualizar el área.");
  }
  return respuesta.json();
};

/**
 * Llama al endpoint para eliminar un Area de Especialidad.
 * @param {number} idArea - El ID del área a eliminar.
 * @returns {Promise<void>} Una promesa que se resuelve si la eliminación es exitosa.
 */
export const apiEliminarArea = async (idArea) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/areas-especialidad/${idArea}`,
    {
      method: "DELETE",
      headers: obtenerCabeceras(),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al eliminar el área.");
  }
};



/**
 * Llama al endpoint para obtener la lista de todas las cuentas de rol "usuario".
 * @returns {Promise<Array>} Una promesa que se resuelve con la lista de usuarios.
 */
export const apiObtenerUsuarios = async () => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/usuarios`,
    {
      method: "GET",
      headers: obtenerCabeceras(),
    }
  );
  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al obtener la lista de usuarios.");
  }
  return respuesta.json();
};

/**
 * Llama al endpoint para activar o desactivar una cuenta de usuario (ciudadano).
 * @param {number} idCuenta - El ID de la cuenta a modificar.
 * @returns {Promise<Object>} Una promesa que se resuelve con los datos actualizados del usuario.
 */
export const apiCambiarEstadoCuentaUsuario = async (idCuenta) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/usuarios/${idCuenta}/cambiar-estado`,
    {
      method: "POST",
      headers: obtenerCabeceras(),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al cambiar el estado de la cuenta del usuario.");
  }
  return respuesta.json();
};




/**
 * Llama al endpoint para actualizar los datos de una cuenta de usuario (ciudadano).
 * @param {number} idCuenta - El ID de la cuenta a modificar.
 * @param {Object} datosEdicion - Un objeto con los campos a actualizar (nombre, cedula, contrasena).
 * @returns {Promise<Object>} Una promesa que se resuelve con los datos actualizados del usuario.
 */
export const apiEditarUsuario = async (idCuenta, datosEdicion) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/usuarios/${idCuenta}`,
    {
      method: "PUT",
      headers: obtenerCabeceras(),
      body: JSON.stringify(datosEdicion),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al editar la cuenta del usuario.");
  }
  return respuesta.json();
};

/**
 * Llama al endpoint para asignar o actualizar la lista de estudiantes supervisados por un asesor.
 * @param {Object} asignacion - El objeto con los datos de la asignación.
 * @param {number} asignacion.id_asesor - El ID del asesor supervisor.
 * @param {Array<number>} asignacion.ids_estudiantes - La lista completa de IDs de estudiantes que deben quedar asignados.
 * @returns {Promise<Object>} Una promesa que se resuelve con el mensaje de éxito del backend.
 */
export const apiAsignarSupervisor = async (asignacion) => {
  const respuesta = await fetch(
    `${URL_BASE_BACKEND}/api/administrador/supervision/asignar`,
    {
      method: "POST",
      headers: obtenerCabeceras(),
      body: JSON.stringify(asignacion),
    }
  );

  if (!respuesta.ok) {
    const error = await respuesta.json();
    throw new Error(error.detail || "Error al actualizar la asignación de supervisión.");
  }
  return respuesta.json();
};