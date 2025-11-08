// frontend/src/componentes/VistaAutenticacion/VistaLogin.jsx

/**
 * Docstring:
 * Componente de UI para el formulario de inicio de sesion de usuarios existentes.
 * Es un componente "tonto" que recibe el estado y los manejadores como props.
 */
import React, { useState } from 'react';
import './Autenticacion.css'; // Reutilizamos el mismo archivo de estilos
import CampoContrasena from '../compartidos/CampoContrasena';
const VistaLogin = ({ onLoginSubmit, onCambiarAVistaRegistro }) => {
  const [email, setEmail] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [error, setError] = useState('');
  const [estaProcesando, setEstaProcesando] = useState(false);

  const manejarLogin = async (e) => {
    e.preventDefault();
    setError('');
    setEstaProcesando(true);

    try {
      // CORRECCION: Llamamos a la funcion del prop
      await onLoginSubmit(email, contrasena);
      // onLoginExitoso ya no es necesario, el contexto se encarga de todo
    } catch (err) {
      setError(err.message || 'Error al iniciar sesión.');
    } finally {
      setEstaProcesando(false);
    }
  };

  return (
    <div className="contenedor-autenticacion">
      <form onSubmit={manejarLogin} className="formulario-autenticacion">
        <h2>Iniciar Sesión</h2>
        <p>Bienvenido de nuevo. Ingrese a su cuenta.</p>
        
        {error && <div className="mensaje-error">{error}</div>}

        <div className="campo-formulario">
          <label htmlFor="email-login">Correo Electrónico</label>
          <input
            id="email-login"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

        <div className="campo-formulario">
          <label htmlFor="contrasena-login">Contraseña</label>
          <CampoContrasena
            id="contrasena-login"
            value={contrasena}
            onChange={(e) => setContrasena(e.target.value)}
            required
            disabled={estaProcesando}
          />
        </div>

        <button type="submit" disabled={estaProcesando} className="boton-principal">
          {estaProcesando ? 'Ingresando...' : 'Iniciar Sesión'}
        </button>

        <div className="enlace-cambio">
          <p>¿No tiene una cuenta?</p>
          <button type="button" onClick={onCambiarAVistaRegistro} className="boton-enlace">
            Regístrese aquí
          </button>
        </div>
      </form>
    </div>
  );
};

export default VistaLogin;