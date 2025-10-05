# backend/seed_db.py

from sqlmodel import Session, SQLModel
from .base_de_datos import motor
# ¡IMPORTANTE! Ahora importamos TODOS los modelos para que el script sepa que tablas crear.
from .api.modelos_compartidos import Usuario, Estudiante, Asesor, Caso, Evidencia, Asignacion

def resetear_y_poblar_la_base_de_datos():
    """
    Script para resetear y poblar la base de datos con datos de muestra.
    
    ¡ADVERTENCIA! Este script es destructivo. Borrara TODAS las tablas y datos existentes
    y los reemplazara con los datos de muestra definidos aqui.
    Es una herramienta para el desarrollo.
    """
    print("INICIO: Script de reseteo y poblacion de la base de datos.")
    
    # 1. BORRAR todas las tablas existentes de la base de datos.
    #    SQLModel.metadata contiene la informacion de todas las tablas que hemos definido.
    #    drop_all le dice a la base de datos que las elimine.
    print("PASO 1: Borrando todas las tablas existentes...")
    SQLModel.metadata.drop_all(motor)
    print("-> Tablas borradas exitosamente.")

    # 2. CREAR todas las tablas de nuevo, ahora con la estructura actualizada.
    #    create_all lee nuestros modelos de Python y crea las tablas correspondientes.
    print("PASO 2: Creando todas las tablas segun los modelos actualizados...")
    SQLModel.metadata.create_all(motor)
    print("-> Tablas creadas exitosamente.")

    # 3. POBLAR las tablas recien creadas con datos de muestra.
    with Session(motor) as sesion:
        print("PASO 3: Poblando las tablas con datos de muestra...")

        # Creamos un usuario de muestra, ya que ahora es necesario para crear casos.
        usuario_de_prueba = Usuario(
            nombre="Juan Consultante",
            cedula="123456789",
            email="juan.consulta@email.com"
        )

        estudiantes = [
            Estudiante(nombre_completo="Ana Sofia Rojas", area_especialidad="Derecho Privado"),
            Estudiante(nombre_completo="Carlos David Perez", area_especialidad="Derecho Privado"),
            Estudiante(nombre_completo="Laura Valentina Gomez", area_especialidad="Derecho Publico"),
            Estudiante(nombre_completo="Juan Felipe Moreno", area_especialidad="Derecho Laboral"),
        ]

        asesores = [
            Asesor(nombre_completo="Dr. Ricardo Mendoza", area_especialidad="Derecho Privado"),
            Asesor(nombre_completo="Dra. Monica Cifuentes", area_especialidad="Derecho Publico"),
            Asesor(nombre_completo="Dr. Alberto Fernandez", area_especialidad="Derecho Laboral"),
        ]
        
        sesion.add(usuario_de_prueba)
        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        
        sesion.commit()

        print("-> Se ha añadido 1 usuario, 4 estudiantes y 3 asesores a la base de datos.")
        print("EXITO: La base de datos ha sido reseteada y poblada.")


if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()