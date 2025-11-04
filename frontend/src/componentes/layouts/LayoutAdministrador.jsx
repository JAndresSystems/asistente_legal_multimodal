//C:\react\asistente_legal_multimodal\frontend\src/componentes/layouts/LayoutAdministrador.jsx
import React from "react";

import PanelAdministracion from "../administrador/PanelAdministracion/PanelAdministracion";

 import { useAuth } from "../../contextos/ContextoAutenticacion";

const LayoutAdministrador = () => {
  const { logout } = useAuth();

  return (
    <div>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "1rem 2rem",
          backgroundColor: "#333",
          color: "white",
        }}
      >
        <h1>Panel de Administrador del Sistema</h1>
        <button onClick={logout}>Cerrar Sesión</button>
      </header>
      <main>
        <PanelAdministracion />
      </main>
    </div>
  );
};

export default LayoutAdministrador;