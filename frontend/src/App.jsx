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

import LayoutAsesor from './componentes/layouts/LayoutAsesor';

import LayoutAdministrador from "./componentes/layouts/LayoutAdministrador";

function App() {
  const { usuario, estaAutenticado, cargando, login, registro } = useAuth();
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

     if (usuario.rol === "administrador") {
      return <LayoutAdministrador />;
    }

    if (usuario.rol === 'asesor') {
      return <LayoutAsesor />;
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

  // Ahora, App.jsx solo provee el contenedor principal.
  return (
    <div className="aplicacion-principal">
      <main className="app-contenido">
        {renderizarContenido()}
      </main>
    </div>
  );
}

export default App;