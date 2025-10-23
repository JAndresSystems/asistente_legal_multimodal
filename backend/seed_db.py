# backend/seed_db.py

from sqlmodel import Session, SQLModel
from .base_de_datos import motor

from .api.modelos_compartidos import Cuenta, Usuario, Estudiante, Asesor, Caso, Evidencia, Asignacion
from .seguridad.contrasenas import obtener_hash_de_contrasena

def resetear_y_poblar_la_base_de_datos():
    print("INICIO: Script de reseteo y poblacion de la base de datos.")
    
    print("PASO 1: Borrando todas las tablas existentes...")
    SQLModel.metadata.drop_all(motor)
    print("-> Tablas borradas exitosamente.")

    print("PASO 2: Creando todas las tablas segun los modelos actualizados...")
    SQLModel.metadata.create_all(motor)
    print("-> Tablas creadas exitosamente.")

    with Session(motor) as sesion:
        print("PASO 3: Poblando las tablas con datos de muestra...")

        contrasena_hasheada_comun = obtener_hash_de_contrasena("secreto123")

        # --- Creacion de la Cuenta y Perfil del USUARIO (CIUDADANO) ---
        cuenta_usuario = Cuenta(
            email="juan.consulta@email.com",
            contrasena_hash=contrasena_hasheada_comun,
            rol="usuario"
        )
        usuario_de_prueba = Usuario(
            nombre="Juan Consultante",
            cedula="123456789",
            cuenta=cuenta_usuario
        )
        sesion.add(usuario_de_prueba)
        print("-> Se ha añadido 1 cuenta de usuario (ciudadano).")

        # --- Creacion de la Cuenta y Perfil para la ESTUDIANTE de prueba ---
        cuenta_estudiante = Cuenta(
            email="ana.rojas@email.com",
            contrasena_hash=contrasena_hasheada_comun,
            rol="estudiante"
        )
        estudiante_ana = Estudiante(
            nombre_completo="Ana Sofia Rojas", 
            area_especialidad="Derecho Privado",
            cuenta=cuenta_estudiante
        )
        sesion.add(estudiante_ana)
        print("-> Se ha añadido 1 cuenta de estudiante (ana.rojas@email.com).")

        # --- INICIO DE LA MODIFICACION: Cobertura completa de areas ---
        # Creamos estudiantes y asesores para TODAS las areas de competencia.
        
        estudiantes = [
            # Se añade uno extra para Derecho Privado para probar el balanceo de carga.
            Estudiante(nombre_completo="Carlos David Perez", area_especialidad="Derecho Privado"),
            Estudiante(nombre_completo="Laura Valentina Gomez", area_especialidad="Derecho Publico"),
            Estudiante(nombre_completo="Juan Felipe Moreno", area_especialidad="Derecho Laboral"),
            Estudiante(nombre_completo="Miguel Angel Torres", area_especialidad="Derecho Penal"),
            Estudiante(nombre_completo="Isabella Cruz", area_especialidad="Derecho Familia"),
        ]

        asesores = [
            Asesor(nombre_completo="Dr. Ricardo Mendoza", area_especialidad="Derecho Privado"),
            Asesor(nombre_completo="Dra. Monica Cifuentes", area_especialidad="Derecho Publico"),
            Asesor(nombre_completo="Dr. Alberto Fernandez", area_especialidad="Derecho Laboral"),
            Asesor(nombre_completo="Dra. Sofia Vergara", area_especialidad="Derecho Penal"),
            Asesor(nombre_completo="Dr. Andres Ramirez", area_especialidad="Derecho Familia"),
        ]
        
        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        
        # --- FIN DE LA MODIFICACION: Se eliminan casos y asignaciones predefinidas ---
        
        sesion.commit()

        print("-> Se han añadido 5 estudiantes adicionales y 5 asesores, cubriendo todas las areas.")
        print("-> No se han creado casos ni asignaciones para asegurar una prueba limpia.")
        print("EXITO: La base de datos ha sido reseteada y poblada con personal completo.")

if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()