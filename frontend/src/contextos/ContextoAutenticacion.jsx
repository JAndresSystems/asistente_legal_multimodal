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
    const perfilGuardado = localStorage.getItem('userProfile');

    if (tokenGuardado && perfilGuardado) {
      try {
        const decodedToken = jwtDecode(tokenGuardado);
        if (decodedToken.exp * 1000 > Date.now()) {
          setAuthToken(tokenGuardado);
          
          // --- INICIO DE LA MODIFICACIÓN ---
          // Reconstruimos el objeto de usuario consistente al cargar
          const perfil = JSON.parse(perfilGuardado);
          setUsuario({ ...perfil, rol: decodedToken.rol }); // Fusionamos perfil y rol
          // --- FIN DE LA MODIFICACIÓN ---
          
          setEstaAutenticado(true);
        } else {
          localStorage.clear(); // Limpiar todo si el token expira
        }
      } catch (error) {
        console.error("Error al procesar la sesión guardada:", error);
        localStorage.clear();
      }
    }
    setCargando(false);
  }, []);

  // Funcion de LOGIN
 const login = async (email, contrasena) => {
    try {
      const data = await apiLogin(email, contrasena);
      const decodedToken = jwtDecode(data.access_token);
      
      // --- INICIO DE LA MODIFICACIÓN ---
      // Creamos un objeto de usuario unificado que contiene todo lo que necesitamos
      const usuarioCompleto = { ...data.perfil, rol: decodedToken.rol };
      
      localStorage.setItem('authToken', data.access_token);
      localStorage.setItem('userProfile', JSON.stringify(usuarioCompleto)); // Guardamos el objeto unificado
      
      setAuthToken(data.access_token);
      setUsuario(usuarioCompleto); // Establecemos el objeto unificado en el estado
      // --- FIN DE LA MODIFICACIÓN ---
      
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
    localStorage.clear(); // La forma más segura de limpiar todo
    setUsuario(null);
    setEstaAutenticado(false);
    setAuthToken(null);
  };

  // El valor que sera accesible por todos los componentes hijos
   const valor = { usuario, estaAutenticado, cargando, login, registro, logout };

   return <ContextoAuth.Provider 

   value={valor}>{children}

   </ContextoAuth.Provider>;

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