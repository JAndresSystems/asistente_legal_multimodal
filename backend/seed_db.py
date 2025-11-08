from sqlmodel import Session, SQLModel
from .base_de_datos import motor
from .api.modelos_compartidos import Cuenta, Usuario, Estudiante, Asesor, AreaEspecialidad
from .seguridad.contrasenas import obtener_hash_de_contrasena

def resetear_y_poblar_la_base_de_datos():
    """
    Este script borra y reconstruye la base de datos, poblándola con un
    conjunto de datos de prueba consistente y limpio para el entorno de desarrollo.
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

        # Contraseña común para todas las cuentas de prueba para facilitar el login
        contrasena_hasheada_comun = obtener_hash_de_contrasena("secreto123")

        # 3.1: Crear las Áreas de Especialidad
        print(" -> Creando Areas de Especialidad...")
        nombres_areas = [
            "Derecho Privado", "Derecho Publico", "Derecho Laboral",
            "Derecho Penal", "Derecho Familia"
        ]
        areas_db = {nombre: AreaEspecialidad(nombre=nombre) for nombre in nombres_areas}
        sesion.add_all(list(areas_db.values()))
        sesion.commit()
        for area in areas_db.values():
            sesion.refresh(area)
        print(f" -> Se crearon {len(areas_db)} areas.")

        # 3.2: Crear cuenta de Administrador
        print(" -> Creando cuenta de Administrador...")
        cuenta_admin = Cuenta(email="admin@sistema.com", contrasena_hash=contrasena_hasheada_comun, rol="administrador")
        sesion.add(cuenta_admin)
        print(" -> admin@sistema.com | pass: secreto123")

        # 3.3: Crear cuenta de Usuario (Ciudadano) de prueba
        print(" -> Creando cuenta de Usuario (Ciudadano)...")
        cuenta_usuario = Cuenta(email="juan.consulta@email.com", contrasena_hash=contrasena_hasheada_comun, rol="usuario")
        usuario_de_prueba = Usuario(nombre="Juan Consultante", cedula="123456789", cuenta=cuenta_usuario)
        sesion.add(usuario_de_prueba)
        print(" -> juan.consulta@email.com | pass: secreto123")
        
        # 3.4: Crear un Asesor por cada Área de Especialidad
        print(" -> Creando un Asesor por cada Area...")
        asesores_data = [
            {"nombre": "Dr. Ricardo Mendoza", "email": "ricardo.mendoza@email.com", "area": "Derecho Privado"},
            {"nombre": "Dra. Monica Cifuentes", "email": "monica.cifuentes@email.com", "area": "Derecho Publico"},
            {"nombre": "Dr. Alberto Fernandez", "email": "alberto.fernandez@email.com", "area": "Derecho Laboral"},
            {"nombre": "Dra. Sofia Vergara", "email": "sofia.vergara@email.com", "area": "Derecho Penal"},
            {"nombre": "Dr. Andres Ramirez", "email": "andres.ramirez@email.com", "area": "Derecho Familia"},
        ]
        
        for data in asesores_data:
            cuenta_asesor = Cuenta(email=data["email"], contrasena_hash=contrasena_hasheada_comun, rol="asesor")
            perfil_asesor = Asesor(
                nombre_completo=data["nombre"],
                cuenta=cuenta_asesor,
                area=areas_db[data["area"]]
            )
            sesion.add(perfil_asesor)
            print(f"    - Asesor Creado: {data['nombre']} ({data['email']}) en {data['area']}")

        # 3.5: Crear un Estudiante por cada Área de Especialidad
        print(" -> Creando un Estudiante por cada Area...")
        estudiantes_data = [
            {"nombre": "Carlos Perez", "email": "carlos.perez@email.com", "area": "Derecho Privado"},
            {"nombre": "Laura Gomez", "email": "laura.gomez@email.com", "area": "Derecho Publico"},
            {"nombre": "Juan Moreno", "email": "juan.moreno@email.com", "area": "Derecho Laboral"},
            {"nombre": "Miguel Torres", "email": "miguel.torres@email.com", "area": "Derecho Penal"},
            {"nombre": "Isabella Cruz", "email": "isabella.cruz@email.com", "area": "Derecho Familia"},
        ]

        for data in estudiantes_data:
            cuenta_estudiante = Cuenta(email=data["email"], contrasena_hash=contrasena_hasheada_comun, rol="estudiante")
            perfil_estudiante = Estudiante(
                nombre_completo=data["nombre"],
                cuenta=cuenta_estudiante,
                area=areas_db[data["area"]]
            )
            sesion.add(perfil_estudiante)
            print(f"    - Estudiante Creado: {data['nombre']} ({data['email']}) en {data['area']}")

        # 3.6: Crear el estudiante adicional solicitado
        print(" -> Creando estudiante adicional...")
        cuenta_estudiante_extra = Cuenta(email="ana.rojas@email.com", contrasena_hash=contrasena_hasheada_comun, rol="estudiante")
        estudiante_extra = Estudiante(
            nombre_completo="Ana Sofia Rojas",
            cuenta=cuenta_estudiante_extra,
            area=areas_db["Derecho Privado"] # La asignamos a un área existente
        )
        sesion.add(estudiante_extra)
        print("    - Estudiante Adicional: Ana Sofia Rojas (ana.rojas@email.com)")

        # 3.7: Guardar todos los cambios en la base de datos
        print("PASO 4: Guardando todos los registros en la base de datos...")
        sesion.commit()
        print("-> Registros guardados exitosamente.")

    print("EXITO: La base de datos ha sido reseteada y poblada con los datos solicitados.")

if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()