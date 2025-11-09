// C:\react\asistente_legal_multimodal\frontend\src\servicios\api\config.js

// ==============================================================================
// Configuracion Compartida
// ==============================================================================

// Usamos la variable de entorno VITE_URL_BASE_BACKEND.
// Si no está definida (por ejemplo, en desarrollo local sin .env),
// usamos 'http://127.0.0.1:8000' como fallback para desarrollo local.
export const URL_BASE_BACKEND = import.meta.env.VITE_URL_BASE_BACKEND || 'http://127.0.0.1:8000';

let authToken = null;

/**
 * Docstring:
 * Configura o limpia el token de autenticacion que se enviara en las
 * cabeceras de las peticiones protegidas.
 * @param {string | null} token El token JWT o null para limpiarlo.
 */
export const setAuthToken = (token) => {
  authToken = token;
};

/**
 * Docstring:
 * Funcion auxiliar para obtener las cabeceras, incluyendo el token si existe.
 * @returns {HeadersInit} Un objeto con las cabeceras para la peticion fetch.
 */
export const obtenerCabeceras = (esFormData = false) => {
  const cabeceras = {};

  if (!esFormData) {
    cabeceras['Content-Type'] = 'application/json';
  }
  
  if (authToken) {
    cabeceras['Authorization'] = `Bearer ${authToken}`;
  }
  
  return cabeceras;
};