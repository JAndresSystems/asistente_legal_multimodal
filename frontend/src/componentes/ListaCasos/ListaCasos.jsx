// frontend/src/componentes/ListaCasos/ListaCasos.jsx
import React from 'react';
import './ListaCasos.css';

function ListaCasos({ casos, onSeleccionarCaso, casoActivoId }) {
  // Verificamos que 'casos' sea un array antes de intentar ordenarlo para evitar errores.
  const casosOrdenados = Array.isArray(casos) 
    ? [...casos].sort((a, b) => new Date(b.fecha_creacion) - new Date(a.fecha_creacion))
    : [];

  return (
    <div className="lista-casos-contenedor">
      <h4>Casos Creados</h4>
      <div className="lista-scrollable">
        {casosOrdenados.length > 0 ? (
          <ul>
            {casosOrdenados.map((caso) => {
              // Comprobacion adicional para robustez, aunque no deberia ser necesaria.
              if (!caso || !caso.id) return null;

              const estaActivo = caso.id === casoActivoId;
              return (
                <li
                  key={caso.id}
                  className={`item-caso ${estaActivo ? 'activo' : ''}`}
                  onClick={() => onSeleccionarCaso(caso)}
                >
                  <span className="item-caso-id">ID DEL CASO: {caso.id}</span>
                  <p className="item-caso-descripcion">
                    {/* Usamos 'descripcion_hechos' como la fuente principal de texto */}
                    {caso.descripcion_hechos || "Este caso no tiene descripción."}
                  </p>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="lista-vacia-mensaje">No hay casos registrados en el sistema.</p>
        )}
      </div>
    </div>
  );
}

export default ListaCasos;