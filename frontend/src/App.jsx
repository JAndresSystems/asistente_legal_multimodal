// C:\react\asistente_legal_multimodal\frontend\src\App.jsx

import React, { useState } from 'react';
import './App.css';
import { useAuth } from './contextos/ContextoAutenticacion';

// Vistas de Autenticación (compartidas)
import VistaLogin from './componentes/VistaAutenticacion/VistaLogin';
import VistaRegistro from './componentes/VistaAutenticacion/VistaRegistro';

// Importamos los NUEVOS Layouts de rol
import LayoutUsuario from './componentes/layouts/LayoutUsuario';
import LayoutEstudiante from './componentes/layouts/LayoutEstudiante';

function App() {
  const { usuario, estaAutenticado, cargando, login, registro, logout } = useAuth();
  const [vistaAuth, setVistaAuth] = useState('login');

  const renderizarContenido = () => {
    if (cargando) {
      return <div>Cargando...</div>;
    }

    if (!estaAutenticado) {
      if (vistaAuth === 'registro') {
        return <VistaRegistro onRegistroSubmit={registro} onCambiarAVistaLogin={() => setVistaAuth('login')} />;
      }
      return <VistaLogin onLoginSubmit={login} onCambiarAVistaRegistro={() => setVistaAuth('registro')} />;
    }

    if (!usuario) {
      return <div>Verificando permisos...</div>;
    }

    // LÓGICA DE ENRUTAMIENTO DE ROLES: SIMPLE, DIRECTA E INFALIBLE
    if (usuario.rol === 'estudiante') {
      return <LayoutEstudiante />;
    }
    
    if (usuario.rol === 'usuario') {
      return <LayoutUsuario />;
    }

    return <div>Rol de usuario no reconocido: {usuario.rol}</div>;
  };

  return (
    <div className="aplicacion-principal">
      <header className="app-header">
        <h1>Asistente Legal Multimodal</h1>
        {estaAutenticado && (<button onClick={logout} className="boton-logout">Cerrar Sesión</button>)}
      </header>
      <main className="app-contenido">{renderizarContenido()}</main>
    </div>
  );
}

export default App;