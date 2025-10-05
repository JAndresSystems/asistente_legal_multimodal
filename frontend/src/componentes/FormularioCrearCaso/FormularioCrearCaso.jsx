// frontend/src/componentes/FormularioCrearCaso/FormularioCrearCaso.jsx

import React, { useState } from 'react';
import { crearNuevoCaso } from '../../servicios/api';
import './FormularioCrearCaso.css';

const FormularioCrearCaso = ({ onCasoCreado }) => {
  // El estado ahora solo maneja 'descripcion_hechos'
  const [descripcionHechos, setDescripcionHechos] = useState('');
  const [estaCreando, setEstaCreando] = useState(false);

  const manejarEnvio = async (evento) => {
    evento.preventDefault();
    if (!descripcionHechos.trim()) {
      alert("La descripción de los hechos no puede estar vacía.");
      return;
    }
    setEstaCreando(true);
    try {
      // Creamos el objeto con la estructura que la API espera
      const datosNuevoCaso = {
        descripcion_hechos: descripcionHechos,
        id_usuario: 1 // Usamos el ID del usuario de prueba
      };
      
      const nuevoCaso = await crearNuevoCaso(datosNuevoCaso);
      
      onCasoCreado(nuevoCaso); // Llama a la funcion del padre para recargar
      setDescripcionHechos(''); // Limpia el formulario
    } catch (error) {
      console.error("Detalles del error al crear el caso:", error);
      alert("Hubo un error al crear el caso. Revisa la consola para más detalles.");
    } finally {
      setEstaCreando(false);
    }
  };

  return (
    <div className="formulario-crear-caso-contenedor">
      <h3>Crear Nuevo Caso</h3>
      <form onSubmit={manejarEnvio} className="formulario-crear-caso">
        <div className="grupo-formulario">
          <label htmlFor="descripcion-caso">Descripción de los Hechos</label>
          <textarea
            id="descripcion-caso"
            value={descripcionHechos}
            onChange={(e) => setDescripcionHechos(e.target.value)}
            placeholder="Narra brevemente los hechos principales del caso..."
            rows={5} // Hacemos el area de texto un poco mas grande
            required
          />
        </div>
        <button type="submit" disabled={estaCreando || !descripcionHechos}>
          {estaCreando ? 'Creando...' : 'Crear Caso'}
        </button>
      </form>
    </div>
  );
};

export default FormularioCrearCaso;