//C:\react\asistente_legal_multimodal\frontend\src\servicios\api.js

/**
 * Docstring:
 * Este modulo actua como un punto de entrada central ("barrel file") para
 * todos los servicios de la API, re-exportando las funciones desde
 * modulos organizados por rol.
 * Esto mantiene la compatibilidad de las importaciones en toda la aplicacion
 * mientras se mejora la estructura interna del codigo.
 */

// Exportar la configuracion compartida (especialmente setAuthToken que se usa globalmente)
export * from './api/config.js';

// Exportar todas las funciones del modulo de autenticacion
export * from './api/autenticacion.js';

// Exportar todas las funciones del modulo del ciudadano
export * from './api/ciudadano.js';

// Exportar todas las funciones del modulo del estudiante
export * from './api/estudiante.js';

// Exportar todas las funciones del modulo del asesor
export * from './api/asesor.js';

// Exportar las funcones de expedientes (comunes a varios roles)
export * from './api/expediente.js';