// frontend/src/servicios/api.js

// --- LA CORRECCIÓN ESTÁ EN ESTA LÍNEA ---
// Antes decia '122.0.0.1', lo correcto es '127.0.0.1'.
const URL_BASE = 'http://127.0.0.1:8000';

export const crearNuevoCaso = async (datosDelFormulario) => {
  console.log("Servicio API: Enviando datos para crear caso:", datosDelFormulario);

  try {
    const respuesta = await fetch(`${URL_BASE}/casos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datosDelFormulario),
    });

    if (respuesta.status === 422) {
      console.error("Error de validacion (422). Datos enviados:", datosDelFormulario);
      const detallesError = await respuesta.json();
      console.error("Detalles del error:", detallesError);
      throw new Error(`Error de validacion de datos: ${JSON.stringify(detallesError)}`);
    }

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const casoCreado = await respuesta.json();
    console.log("Servicio API: Caso creado con éxito:", casoCreado);
    return casoCreado;

  } catch (error) {
    console.error("Servicio API: Error al crear el caso:", error);
    throw error;
  }
};

export const obtenerTodosLosCasos = async () => {
  console.log("Servicio API: Pidiendo la lista de todos los casos...");
  try {
    const respuesta = await fetch(`${URL_BASE}/casos`);
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    const casos = await respuesta.json();
    console.log("Servicio API: Lista de casos recibida.", casos);
    return casos;
  } catch (error) {
    console.error("Servicio API: Error al obtener los casos:", error);
    throw error;
  }
};

export const subirEvidencia = async (idCaso, archivo) => {
  const formData = new FormData();
  formData.append("archivo", archivo);

  console.log(`Servicio API: Subiendo archivo '${archivo.name}' para el caso ${idCaso}`);

  try {
    const respuesta = await fetch(`${URL_BASE}/casos/${idCaso}/evidencia`, {
      method: 'POST',
      body: formData,
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }

    const casoActualizado = await respuesta.json();
    console.log("Servicio API: Evidencia subida. Caso actualizado:", casoActualizado);
    return casoActualizado;
  } catch (error) {
    console.error("Servicio API: Error al subir la evidencia:", error);
    throw error;
  }
};

export const obtenerEstadoEvidencia = async (idEvidencia) => {
  try {
    const respuesta = await fetch(`${URL_BASE}/evidencias/${idEvidencia}/estado`);
    
    if (!respuesta.ok) {
      throw new Error(`Error del servidor: ${respuesta.status}`);
    }
    
    const datosEstado = await respuesta.json();
    return datosEstado;

  } catch (error) {
    console.error(`Error al obtener el estado de la evidencia ${idEvidencia}:`, error);
    return { estado_procesamiento: 'error_en_sondeo' };
  }
};



/**
 * Envia una pregunta al Agente de Atencion y devuelve su respuesta.
 * @param {string} preguntaUsuario - El texto de la pregunta del usuario.
 * @returns {Promise<string>} Una promesa que resuelve a la respuesta del agente.
 */
export const chatearConAgente = async (preguntaUsuario) => {
  console.log(`Servicio API: Enviando pregunta al chat: "${preguntaUsuario}"`);
  
  const datosPregunta = {
    pregunta: preguntaUsuario,
  };

  try {
    const respuesta = await fetch(`${URL_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datosPregunta),
    });

    if (!respuesta.ok) {
      throw new Error(`Error del servidor en el chat: ${respuesta.status}`);
    }

    const datosRespuesta = await respuesta.json();
    console.log(`Servicio API: Respuesta del chat recibida: "${datosRespuesta.respuesta}"`);
    return datosRespuesta.respuesta; // Devolvemos directamente el string de la respuesta

  } catch (error) {
    console.error("Servicio API: Error al chatear con el agente:", error);
    // Devolvemos un mensaje de error generico para mostrar en el chat
    return "Lo siento, no pude conectarme con el asistente en este momento.";
  }
};