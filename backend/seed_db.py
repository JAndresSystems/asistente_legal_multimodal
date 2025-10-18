# backend/seed_db.py

from sqlmodel import Session, SQLModel
from .base_de_datos import motor

# ¡IMPORTANTE! Importamos el nuevo modelo 'Cuenta'
from .api.modelos_compartidos import Cuenta, Usuario, Estudiante, Asesor, Caso, Evidencia, Asignacion

# Importamos nuestra nueva utilidad para hashear contraseñas
from .seguridad.contrasenas import obtener_hash_de_contrasena

def resetear_y_poblar_la_base_de_datos():
    """
    Script para resetear y poblar la base de datos con datos de muestra.
    ¡ADVERTENCIA! Este script es destructivo.
    """
    print("INICIO: Script de reseteo y poblacion de la base de datos.")
    
    print("PASO 1: Borrando todas las tablas existentes...")
    SQLModel.metadata.drop_all(motor)
    print("-> Tablas borradas exitosamente.")

    print("PASO 2: Creando todas las tablas segun los modelos actualizados...")
    SQLModel.metadata.create_all(motor)
    print("-> Tablas creadas exitosamente.")

    with Session(motor) as sesion:
        print("PASO 3: Poblando las tablas con datos de muestra...")

        # --- INICIO DE LA MODIFICACION ---
        # Ahora, primero creamos la CUENTA y luego el USUARIO
        
        # 3.1. Hasheamos una contraseña de prueba
        contrasena_hasheada = obtener_hash_de_contrasena("secreto123")

        # 3.2. Creamos la instancia de la Cuenta
        cuenta_de_prueba = Cuenta(
            email="juan.consulta@email.com",
            contrasena_hash=contrasena_hasheada,
            rol="usuario"
        )
        
        # 3.3. Creamos la instancia del Usuario y la VINCULAMOS a su cuenta
        usuario_de_prueba = Usuario(
            nombre="Juan Consultante",
            cedula="123456789",
            cuenta=cuenta_de_prueba  # SQLModel se encarga de la magia de la relación
        )
        # --- FIN DE LA MODIFICACION ---

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
        
        # Al añadir el usuario, SQLModel tambien añadirá la cuenta vinculada.
        sesion.add(usuario_de_prueba)
        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        
        sesion.commit()

        print("-> Se ha añadido 1 cuenta y 1 perfil de usuario.")
        print("-> Se han añadido 4 estudiantes y 3 asesores.")
        print("EXITO: La base de datos ha sido reseteada y poblada.")


if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()