/**
 * frontend\src\servicios\api.js
 * 
 * 
 * """
 * Docstring:
 * Este modulo centraliza todas las funciones que interactuan con la API
 * del backend (FastAPI). Abstrae la logica de las llamadas fetch, el
 * manejo de errores y la estructura de los datos JSON.
 * """
 */

// ==============================================================================
// Configuracion
// ==============================================================================
const URL_BASE_BACKEND = "http://127.0.0.1:8000";


// ==============================================================================
// Funciones de la API
// ==============================================================================


// ==============================================================================
// INICIO DE LA MODIFICACION: Gestion del Token de Autenticacion
// ==============================================================================
let authToken = null;



/**
 * Docstring:
 * Configura o limpia el token de autenticacion que se enviara en las
 * cabeceras de las peticiones protegidas.
 * Args:
 *   token (string | null): El token JWT o null para limpiarlo.
 */
export const setAuthToken = (token) => {
  authToken = token;
};

// Funcion auxiliar para obtener las cabeceras, incluyendo el token si existe.
const obtenerCabeceras = () => {
  const cabeceras = {
    'Content-Type': 'application/json',
  };
  if (authToken) {
    cabeceras['Authorization'] = `Bearer ${authToken}`;
  }
  return cabeceras;
};



// ==============================================================================
// INICIO DE LA MODIFICACION: Nuevas funciones de autenticacion
// ==============================================================================

/**
 * Docstring:
 * Llama al endpoint de registro del backend.
 * Args:
 *   datosRegistro (object): Objeto con nombre, cedula, email, contrasena.
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
 * Args:
 *   email (string): El correo del usuario.
 *   contrasena (string): La contraseña del usuario.
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

    return await respuesta.json(); // Devuelve { access_token, token_type }
  } catch (error) {
    console.error("API: Error en el login:", error);
    throw error;
  }
};




export const chatearConAgente = async (textoPregunta) => {
  console.log(`API: Enviando pregunta al chat: "${textoPregunta}"`);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pregunta: textoPregunta }),
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor en el chat: ${respuesta.status}`);
    }

    const datosRespuesta = await respuesta.json();
    let respuestaDelAgente = datosRespuesta.respuesta;
    console.log(`API: Respuesta original recibida: "${respuestaDelAgente}"`);

    const palabrasClaveDeViabilidad = ["califica", "cumple", "atendemos", "requisitos", "elegibilidad", "procedente", "admisible"];
    const respuestaEnMinusculas = respuestaDelAgente.toLowerCase();
    const esViable = palabrasClaveDeViabilidad.some(palabra => respuestaEnMinusculas.includes(palabra));

    if (esViable) {
      console.log("API (Simulacion): Se detecto un caso viable. Añadiendo señal.");
      respuestaDelAgente += " [INICIAR_CASO]";
    }
    
    return respuestaDelAgente;

  } catch (error) {
    console.error("API: Error al chatear con el agente:", error);
    return "Lo siento, no pude conectarme con el asistente en este momento.";
  }
};

export const crearNuevoCaso = async (datosCaso) => {
  console.log("API: Enviando datos para crear caso:", datosCaso);
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos`, {
      method: 'POST',
      headers: obtenerCabeceras(), // <-- AHORA USA EL TOKEN
      body: JSON.stringify(datosCaso),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error("API: Error al crear el caso:", error);
    throw error;
  }
};

/**
 * Docstring:
 * Llama al endpoint protegido para obtener la lista de casos
 * del usuario actualmente autenticado.
 */
export const apiObtenerMisCasos = async () => {
  console.log("API: Solicitando la lista de casos para el usuario logueado.");
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/mis-casos`, {
      method: 'GET',
      headers: obtenerCabeceras(), // <-- Clave: Usa el token para la autenticacion
    });

    if (!respuesta.ok) {
      // Si el token es invalido o expiro, el backend devolvera un error 401
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    return await respuesta.json(); // Devuelve la lista de casos
  } catch (error) {
    console.error("API: Error al obtener los casos del usuario:", error);
    throw error; // Propagamos el error para que el componente que llama pueda manejarlo
  }
};



export const subirEvidencia = async (idCaso, archivo) => {
  const formData = new FormData();
  formData.append("archivo", archivo);

  // Para FormData, las cabeceras se manejan de forma diferente.
  const cabeceras = {};
  if (authToken) {
    cabeceras['Authorization'] = `Bearer ${authToken}`;
  }

  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/${idCaso}/subir-evidencia-simple`, {
      method: 'POST',
      headers: cabeceras, // <-- AHORA USA EL TOKEN
      body: formData,
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return { exito: true };
  } catch (error) {
    console.error("API: Error al subir la evidencia:", error);
    throw error;
  }
};


export const analizarCaso = async (idCaso, textoAdicional = "") => {
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/${idCaso}/analizar`, {
      method: 'POST',
      headers: obtenerCabeceras(), // <-- AHORA USA EL TOKEN
      body: JSON.stringify({ texto_adicional_usuario: textoAdicional }),
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al solicitar el analisis del caso ${idCaso}:`, error);
    throw error;
  }
};

export const obtenerDetallesCaso = async (idCaso) => {
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/casos/${idCaso}`, {
      headers: obtenerCabeceras() // <-- AHORA USA EL TOKEN
    });
    if (!respuesta.ok) { throw new Error(`Error del servidor: ${respuesta.status}`); }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener los detalles del caso ${idCaso}:`, error);
    throw error;
  } 

 
};


/**
 * Docstring:
 * Llama al endpoint para consultar el estado de una evidencia especifica.
 * Utilizado para el sondeo (polling) del progreso del analisis.
 */
export const obtenerEstadoEvidencia = async (idEvidencia) => {
  try {
    const respuesta = await fetch(`${URL_BASE_BACKEND}/evidencias/${idEvidencia}/estado`, {
      headers: obtenerCabeceras(),
    });
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    return await respuesta.json();
  } catch (error) {
    console.error(`API: Error al obtener el estado de la evidencia ${idEvidencia}:`, error);
    throw error;
  }
};