// frontend/src/contextos/ContextoAutenticacion.jsx

/**
 * Docstring:
 * Este archivo crea y gestiona el Contexto de Autenticacion para toda la aplicacion.
 * Proporciona un estado global para saber si un usuario esta autenticado, su informacion,
 * y las funciones para realizar el login, registro y logout.
 */
import React, { createContext, useState, useContext, useEffect } from 'react';
import { apiLogin, apiRegistro, setAuthToken } from '../servicios/api';
import { jwtDecode } from 'jwt-decode'; // Necesitaremos una nueva libreria
// Todavia no hemos creado estas funciones en api.js, pero las añadiremos en el siguiente paso.
// import { apiLogin, apiRegistro, setAuthToken } from '../servicios/api';

// 1. CREACION DEL CONTEXTO
// Este es el canal a traves del cual se distribuira la informacion.
const ContextoAuth = createContext(null);

export const ProveedorAuth = ({ children }) => {
  const [usuario, setUsuario] = useState(null);
  const [estaAutenticado, setEstaAutenticado] = useState(false);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const tokenGuardado = localStorage.getItem('authToken');
    if (tokenGuardado) {
      try {
        // Decodificamos el token para verificar si ha expirado
        const decodedToken = jwtDecode(tokenGuardado);
        if (decodedToken.exp * 1000 > Date.now()) {
          
          setAuthToken(tokenGuardado);
          // ==============================================================================
          // INICIO DE LA CORRECCION: Leemos el ROL al cargar la página
          // ==============================================================================
          setUsuario({ email: decodedToken.sub, rol: decodedToken.rol });
          // ==============================================================================
          // FIN DE LA CORRECCION
          // ==============================================================================
          setEstaAutenticado(true);
        } else {
          // Si el token ha expirado, lo limpiamos
          localStorage.removeItem('authToken');
        }
      } catch (error) {
        console.error("Error al decodificar el token:", error);
        // Si el token es invalido, lo limpiamos
        localStorage.removeItem('authToken');
      }
    }
    setCargando(false);
  }, []);

  // Funcion de LOGIN
 const login = async (email, contrasena) => {
    try {
      const data = await apiLogin(email, contrasena);
      localStorage.setItem('authToken', data.access_token);
      setAuthToken(data.access_token);
      const decodedToken = jwtDecode(data.access_token);
      // ==============================================================================
      // INICIO DE LA CORRECCION: Leemos el ROL al iniciar sesión
      // ==============================================================================
      setUsuario({ email: decodedToken.sub, rol: decodedToken.rol });
      // ==============================================================================
      // FIN DE LA CORRECCION
      // ==============================================================================
      setEstaAutenticado(true);
    } catch (error) {
      console.error("Error en el login:", error);
      throw error;
    }
  };

  const registro = async (datos) => {
    try {
      await apiRegistro(datos);
    } catch (error) {
      console.error("Error en el registro:", error);
      throw error;
    }
  };
  
   const logout = () => {
    localStorage.removeItem('authToken');
    setUsuario(null);
    setEstaAutenticado(false);
    setAuthToken(null);
    // Adicionalmente, limpiamos el estado guardado de la app para evitar fugas de datos
    localStorage.removeItem('app_vistaActual');
    localStorage.removeItem('app_casoId');
    localStorage.removeItem('app_agenteActivo');
  };

  // El valor que sera accesible por todos los componentes hijos
  const valor = {
    usuario,
    estaAutenticado,
    cargando,
    login,
    registro,
    logout
  };

   return (
    <ContextoAuth.Provider value={valor}>
      {children}
    </ContextoAuth.Provider>
  );
};

// 3. CREACION DEL HOOK PERSONALIZADO
// Esta es la forma facil y segura para que los componentes accedan al contexto.
// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const contexto = useContext(ContextoAuth);
  if (contexto === undefined) {
    throw new Error('useAuth debe ser usado dentro de un ProveedorAuth');
  }
  return contexto;
};