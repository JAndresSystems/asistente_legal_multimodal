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


  // Simplificamos la lógica de renderizado para eliminar condiciones de carrera.
  
  // 1. Primer caso: La autenticación se está cargando desde localStorage.
  if (cargando) {
    // Mostramos un estado de carga global para evitar parpadeos o errores.
    return <div className="app-cargando">Cargando aplicación...</div>;
  }

  // 2. Segundo caso: No está autenticado.
  if (!estaAutenticado) {
    return (
      <div className="aplicacion-principal">
        <main className="app-contenido">
          {vistaAuth === 'registro' 
            ? <VistaRegistro onRegistroSubmit={registro} onCambiarAVistaLogin={() => setVistaAuth('login')} />
            : <VistaLogin onLoginSubmit={login} onCambiarAVistaRegistro={() => setVistaAuth('registro')} />
          }
        </main>
      </div>
    );
  }

  // 3. Está autenticado. En este punto, 'usuario' DEBE existir.
  // Renderizamos directamente basado en el rol.
  let ContenidoDelRol;
  switch (usuario?.rol) {
    case 'usuario':
      ContenidoDelRol = <LayoutUsuario />;
      break;
    case 'estudiante':
      ContenidoDelRol = <LayoutEstudiante />;
      break;
    case 'asesor':
      ContenidoDelRol = <LayoutAsesor />;
      break;
    case 'administrador':
      ContenidoDelRol = <LayoutAdministrador />;
      break;
    default:
      // Este caso solo se mostraría si el rol es inválido o el objeto usuario es nulo.
      ContenidoDelRol = <div>Error: Rol de usuario no reconocido o perfil no cargado.</div>;
  }

  return (
    <div className="aplicacion-principal">
      <main className="app-contenido">
        {ContenidoDelRol}
      </main>
    </div>
  );
  
}

export default App;