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

        # Crear casos de prueba asociados al usuario (ID 1)
        casos = [
            Caso(
                descripcion_hechos="Caso de prueba 1: Contrato de arrendamiento con problemas de pago",
                id_usuario=1,
                estado="asignado",
                fecha_creacion="2025-10-01 10:00:00"
            ),
            Caso(
                descripcion_hechos="Caso de prueba 2: Reclamación por accidente de trabajo",
                id_usuario=1,
                estado="en_revision",
                fecha_creacion="2025-10-05 14:30:00"
            ),
            Caso(
                descripcion_hechos="Caso de prueba 3: Divorcio con bienes compartidos",
                id_usuario=1,
                estado="asignado",
                fecha_creacion="2025-10-10 09:15:00"
            ),
        ]

        # Crear evidencias de prueba
        evidencias = [
            Evidencia(
                id_caso=1,
                nombre_archivo="contrato_arrendamiento.pdf",
                ruta_archivo="1/contrato_arrendamiento.pdf",
                estado="completado"
            ),
            Evidencia(
                id_caso=2,
                nombre_archivo="certificado_medico_accidente.png",
                ruta_archivo="2/certificado_medico_accidente.png",
                estado="subido"
            ),
            Evidencia(
                id_caso=3,
                nombre_archivo="escrituras_bienes.pdf",
                ruta_archivo="3/escrituras_bienes.pdf",
                estado="completado"
            ),
        ]

        # Crear asignaciones de prueba
        asignaciones = [
            Asignacion(
                id_caso=1,
                id_estudiante=1,
                id_asesor=1
            ),
            Asignacion(
                id_caso=3,
                id_estudiante=3,
                id_asesor=2
            ),
        ]
        
        # Al añadir el usuario, SQLModel también añadirá la cuenta vinculada.
        sesion.add(usuario_de_prueba)
        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        sesion.add_all(casos)
        sesion.add_all(evidencias)
        sesion.add_all(asignaciones)
        
        sesion.commit()

        print("-> Se ha añadido 1 cuenta y 1 perfil de usuario.")
        print("-> Se han añadido 4 estudiantes y 3 asesores.")
        print("-> Se han añadido 3 casos de prueba con evidencias y asignaciones.")
        print("EXITO: La base de datos ha sido reseteada y poblada.")

if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()