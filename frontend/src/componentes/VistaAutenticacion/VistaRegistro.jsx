// frontend/src/componentes/VistaAutenticacion/VistaRegistro.jsx

/**
 * Docstring:
 * Componente de UI para el formulario de registro de nuevos usuarios.
 * Es un componente "tonto" que recibe el estado y los manejadores como props.
 */
import React, { useState } from 'react';
import './Autenticacion.css'; // Crearemos este archivo de estilos a continuacion
import CampoContrasena from '../compartidos/CampoContrasena';

const VistaRegistro = ({ onRegistroSubmit, onCambiarAVistaLogin }) => {
  const [nombre, setNombre] = useState('');
  const [cedula, setCedula] = useState('');
  const [email, setEmail] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [error, setError] = useState('');
  const [estaProcesando, setEstaProcesando] = useState(false);

const manejarRegistro = async (e) => {
    e.preventDefault();
    setError('');
    setEstaProcesando(true);

    try {
      // CORRECCION: Llamamos a la funcion del prop
      await onRegistroSubmit({ nombre, cedula, email, contrasena });
      alert('¡Registro exitoso! Por favor, inicie sesión.');
      onCambiarAVistaLogin(); // Cambiamos a la vista de login
    } catch (err) {
      setError(err.message || 'Error al registrar la cuenta.');
    } finally {
      setEstaProcesando(false);
    }
  };

  return (
    <div className="contenedor-autenticacion">
      <form onSubmit={manejarRegistro} className="formulario-autenticacion">
        <h2>Crear una Cuenta</h2>
        <p>Regístrese para acceder a los servicios del consultorio.</p>
        
        {error && <div className="mensaje-error">{error}</div>}
        
        <div className="campo-formulario">
          <label htmlFor="nombre">Nombre Completo</label>
          <input
            id="nombre"
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

        <div className="campo-formulario">
          <label htmlFor="cedula">Cédula de Ciudadanía</label>
          <input
            id="cedula"
            type="text"
            value={cedula}
            onChange={(e) => setCedula(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

        <div className="campo-formulario">
          <label htmlFor="email">Correo Electrónico</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

      <div className="campo-formulario">
          <label htmlFor="contrasena">Contraseña</label>
          <CampoContrasena
            id="contrasena"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

        <button type="submit" disabled={estaProcesando} className="boton-principal">
          {estaProcesando ? 'Registrando...' : 'Crear Cuenta'}
        </button>

        <div className="enlace-cambio">
          <p>¿Ya tiene una cuenta?</p>
          <button type="button" onClick={onCambiarAVistaLogin} className="boton-enlace">
            Inicie Sesión aquí
          </button>
        </div>
      </form>
    </div>
  );
};

export default VistaRegistro;