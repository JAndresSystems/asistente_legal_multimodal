import React, { useState } from 'react';
import { crearNuevoCaso } from '../../servicios/api';
import './FormularioCrearCaso.css';

function FormularioCrearCaso({ onCasoCreado }) {
  /**
   * """
   * Docstring:
   * Este componente renderiza un formulario para que el usuario describa
   * los hechos de su caso. Al enviarse, llama a la API para crear el
   * registro en la base de datos.
   *
   * Args:
   *   onCasoCreado (function): Callback que se ejecuta cuando el backend
   *                            confirma la creacion del caso. Recibe el ID
   *                            del nuevo caso como argumento.
   *
   * Returns:
   *   (JSX.Element): La interfaz de usuario del formulario.
   * """
   */

  // ----------------------------------------------------------------------------
  // Estado del Componente
  // ----------------------------------------------------------------------------
  const [descripcionDeHechos, setDescripcionDeHechos] = useState('');
  const [estaCreando, setEstaCreando] = useState(false);

  // ----------------------------------------------------------------------------
  // Manejadores de Eventos
  // ----------------------------------------------------------------------------
  /**
   * """
   * Docstring:
   * Se ejecuta al enviar el formulario. Valida la entrada, llama a la
   * API para crear el caso y notifica al componente padre del exito.
   * """
   */
  const manejarEnvio = async (evento) => {
    evento.preventDefault();
    if (!descripcionDeHechos.trim()) {
      alert("Por favor, describe los hechos de tu caso.");
      return;
    }
    setEstaCreando(true);
    try {
      // --- INICIO DE LA CORRECCION ---
      // El backend espera un objeto que incluya tanto la descripcion
      // como el ID del usuario que crea el caso.
      const datosDelCaso = {
        descripcion_hechos: descripcionDeHechos,
        id_usuario: 1, // Usamos un ID de usuario de prueba. ¡ESTA ES LA CORRECCION!
      };
      // --- FIN DE LA CORRECCION ---
      
      const casoCreado = await crearNuevoCaso(datosDelCaso);
      
      // Notificamos al padre (App.jsx) que el caso fue creado y le
      // pasamos el ID del nuevo caso.
      onCasoCreado(casoCreado.id);

    } catch (error) {
      console.error("FORMULARIO: Error al crear el caso:", error);
      alert("Ocurrio un error al registrar tu caso. Por favor, intentalo de nuevo.");
    } finally {
      setEstaCreando(false);
    }
  };

  // ----------------------------------------------------------------------------
  // Renderizado del Componente
  // ----------------------------------------------------------------------------
  return (
    <div className="formulario-crear-caso-contenedor">
      <h3>Paso 2: Describe tu Caso</h3>
      <form onSubmit={manejarEnvio} className="formulario-crear-caso">
        <div className="grupo-formulario">
          <label htmlFor="descripcion-caso">
            Por favor, narra los hechos principales de tu situacion:
          </label>
          <textarea
            id="descripcion-caso"
            value={descripcionDeHechos}
            onChange={(e) => setDescripcionDeHechos(e.target.value)}
            placeholder="Ej: El dia 15 de marzo firme un contrato de arrendamiento y ahora el arrendador no quiere entregarme el inmueble..."
            rows={8}
            required
            disabled={estaCreando}
          />
        </div>
        <button type="submit" disabled={estaCreando || !descripcionDeHechos.trim()}>
          {estaCreando ? 'Guardando...' : 'Continuar al Paso 3'}
        </button>
      </form>
    </div>
  );
}

export default FormularioCrearCaso;