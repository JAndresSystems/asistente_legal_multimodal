// frontend/src/main.jsx

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';


//  Importamos nuestro proveedor de contexto

import { ProveedorAuth } from './contextos/ContextoAutenticacion.jsx';


createRoot(document.getElementById('root')).render(
  <StrictMode>
    {/*  Envolvemos la aplicacion con el proveedor        */}
   
    <ProveedorAuth>
      <App />
    </ProveedorAuth>
   
  </StrictMode>,
);
