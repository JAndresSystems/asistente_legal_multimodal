//C:\react\asistente_legal_multimodal\frontend\src\servicios\api\config.js

// ==============================================================================
// Configuracion Compartida
// ==============================================================================

export const URL_BASE_BACKEND = import.meta.env.VITE_URL_BASE_BACKEND || 'http://localhost:8000';

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