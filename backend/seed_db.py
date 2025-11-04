#C:\react\asistente_legal_multimodal\backend\seed_db.py
from sqlmodel import Session, SQLModel
from .base_de_datos import motor

# --- INICIO DE LA MODIFICACION: Importar el nuevo modelo ---
from .api.modelos_compartidos import Cuenta, Usuario, Estudiante, Asesor, AreaEspecialidad
# --- FIN DE LA MODIFICACION ---
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

        # --- INICIO DE LA MODIFICACION: Crear primero las Áreas de Especialidad ---
        print("PASO 3.1: Creando las Areas de Especialidad...")
        nombres_areas = [
            "Derecho Privado", "Derecho Publico", "Derecho Laboral",
            "Derecho Penal", "Derecho Familia"
        ]
        # Creamos un diccionario de objetos AreaEspecialidad para fácil acceso
        areas_db = {nombre: AreaEspecialidad(nombre=nombre) for nombre in nombres_areas}
        sesion.add_all(areas_db.values())
        sesion.commit() # Hacemos commit para que se generen los IDs
        # Refrescamos los objetos para que SQLModel cargue los IDs generados
        for area in areas_db.values():
            sesion.refresh(area)
        print(f"-> Se han creado {len(areas_db)} areas de especialidad.")
        # --- FIN DE LA MODIFICACION ---

        print("PASO 3.2: Creando cuentas de prueba y perfiles...")
        
        # Creacion de la Cuenta del ADMINISTRADOR
        cuenta_admin = Cuenta(email="admin@sistema.com", contrasena_hash=contrasena_hasheada_comun, rol="administrador")
        sesion.add(cuenta_admin)
        print("-> Se ha añadido 1 cuenta de administrador.")

        # Creacion de la Cuenta y Perfil del USUARIO (CIUDADANO)
        cuenta_usuario = Cuenta(email="juan.consulta@email.com", contrasena_hash=contrasena_hasheada_comun, rol="usuario")
        usuario_de_prueba = Usuario(nombre="Juan Consultante", cedula="123456789", cuenta=cuenta_usuario)
        sesion.add(usuario_de_prueba)
        print("-> Se ha añadido 1 cuenta de usuario (ciudadano).")

        # --- INICIO DE LA MODIFICACION: Asignar el objeto AreaEspecialidad en lugar de un string ---
        # Creacion de la Cuenta y Perfil para la ESTUDIANTE de prueba
        cuenta_estudiante = Cuenta(email="ana.rojas@email.com", contrasena_hash=contrasena_hasheada_comun, rol="estudiante")
        estudiante_ana = Estudiante(
            nombre_completo="Ana Sofia Rojas",
            cuenta=cuenta_estudiante,
            area=areas_db["Derecho Privado"] # Asignamos el objeto completo
        )
        sesion.add(estudiante_ana)
        print("-> Se ha añadido 1 cuenta de estudiante (ana.rojas@email.com).")

        # Creacion de la Cuenta y Perfil para el ASESOR de prueba
        cuenta_asesor = Cuenta(email="ricardo.mendoza@email.com", contrasena_hash=contrasena_hasheada_comun, rol="asesor")
        asesor_ricardo = Asesor(
            nombre_completo="Dr. Ricardo Mendoza",
            cuenta=cuenta_asesor,
            area=areas_db["Derecho Privado"] # Asignamos el objeto completo
        )
        sesion.add(asesor_ricardo)
        print("-> Se ha añadido 1 cuenta de asesor (ricardo.mendoza@email.com).")

        # Creacion de perfiles de Estudiantes y Asesores para cubrir todas las areas
        estudiantes = [
            Estudiante(nombre_completo="Carlos David Perez", area=areas_db["Derecho Privado"]),
            Estudiante(nombre_completo="Laura Valentina Gomez", area=areas_db["Derecho Publico"]),
            Estudiante(nombre_completo="Juan Felipe Moreno", area=areas_db["Derecho Laboral"]),
            Estudiante(nombre_completo="Miguel Angel Torres", area=areas_db["Derecho Penal"]),
            Estudiante(nombre_completo="Isabella Cruz", area=areas_db["Derecho Familia"]),
        ]
        # --- FIN DE LA MODIFICACION ---
        
        asesores = [
            # El Dr. Mendoza ya fue creado, asi que lo omitimos
            Asesor(nombre_completo="Dra. Monica Cifuentes", area=areas_db["Derecho Publico"]),
            Asesor(nombre_completo="Dr. Alberto Fernandez", area=areas_db["Derecho Laboral"]),
            Asesor(nombre_completo="Dra. Sofia Vergara", area=areas_db["Derecho Penal"]),
            Asesor(nombre_completo="Dr. Andres Ramirez", area=areas_db["Derecho Familia"]),
        ]
        
        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        
        sesion.commit()

        print("-> Se han añadido perfiles adicionales de estudiantes y asesores.")
        print("EXITO: La base de datos ha sido reseteada y poblada.")

if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()