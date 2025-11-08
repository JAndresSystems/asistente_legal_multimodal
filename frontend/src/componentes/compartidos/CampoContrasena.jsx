//C:\react\asistente_legal_multimodal\frontend\src\componentes\compartidos\CampoContrasena.jsx
//frontend\src\componentes\compartidos\CampoContrasena.jsx
import React, { useState } from 'react';
import './CampoContrasena.css'; // Crearemos este archivo para los estilos

const CampoContrasena = ({ value, onChange, id, name, required, disabled, placeholder }) => {
  const [mostrarContrasena, setMostrarContrasena] = useState(false);

  const toggleVisibilidad = () => {
    setMostrarContrasena(prev => !prev);
  };

  return (
    <div className="campo-contrasena-contenedor">
      <input
        id={id}
        name={name}
        type={mostrarContrasena ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        placeholder={placeholder}
      />
      <button 
        type="button" 
        onClick={toggleVisibilidad} 
        className="boton-ojo"
        title={mostrarContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
      >
        {mostrarContrasena ? '👁️' : '👁️‍🗨️'}
      </button>
    </div>
  );
};

export default CampoContrasena;