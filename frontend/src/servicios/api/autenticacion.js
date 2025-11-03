
//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\autenticacion.js

import { URL_BASE_BACKEND } from './config.js';

/**
 * Docstring:
 * Llama al endpoint de registro del backend.
 * @param {object} datosRegistro Objeto con nombre, cedula, email, contrasena.
 */
export const apiRegistro = async (datosRegistro) => {
  console.log("API: Enviando datos para registrar nueva cuenta:", datosRegistro);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/registro`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datosRegistro),
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json();
  } catch (error) {
    console.error("API: Error en el registro:", error);
    throw error;
  }
};

/**
 * Docstring:
 * Llama al endpoint de login. Usa un formato especial (FormData)
 * como lo espera FastAPI para OAuth2PasswordRequestForm.
 * @param {string} email El correo del usuario.
 * @param {string} contrasena La contraseña del usuario.
 */
export const apiLogin = async (email, contrasena) => {
  console.log(`API: Solicitando token para el usuario: ${email}`);
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', contrasena);

  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });

    if (!respuesta.ok) {
      const errorData = await respuesta.json();
      throw new Error(errorData.detail || `Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json();
  } catch (error) {
    console.error("API: Error en el login:", error);
    throw error;
  }
};