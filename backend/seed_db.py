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
        print("-> Se ha añadido 1 cuenta y 1 perfil de usuario.")

        # ==============================================================================
        # INICIO DE LA MODIFICACION: Creacion de Cuenta y Perfil para ESTUDIANTE
        # ==============================================================================
        cuenta_estudiante = Cuenta(
            email="ana.rojas@email.com",
            contrasena_hash=contrasena_hasheada_comun,
            rol="estudiante" # <-- El rol es la clave
        )
        
        # Vinculamos la cuenta a un nuevo perfil de estudiante
        estudiante_ana = Estudiante(
            nombre_completo="Ana Sofia Rojas", 
            area_especialidad="Derecho Privado",
            cuenta=cuenta_estudiante # <-- Vinculo directo
        )
        sesion.add(estudiante_ana)
        print("-> Se ha añadido 1 cuenta y 1 perfil de estudiante.")
        # ==============================================================================
        # FIN DE LA MODIFICACION
        # ==============================================================================

        # Creamos el resto de estudiantes SIN cuenta, ya que no necesitan login por ahora
        otros_estudiantes = [
            Estudiante(nombre_completo="Carlos David Perez", area_especialidad="Derecho Privado"),
            Estudiante(nombre_completo="Laura Valentina Gomez", area_especialidad="Derecho Publico"),
            Estudiante(nombre_completo="Juan Felipe Moreno", area_especialidad="Derecho Laboral"),
        ]

        asesores = [
            Asesor(nombre_completo="Dr. Ricardo Mendoza", area_especialidad="Derecho Privado"),
            Asesor(nombre_completo="Dra. Monica Cifuentes", area_especialidad="Derecho Publico"),
            Asesor(nombre_completo="Dr. Alberto Fernandez", area_especialidad="Derecho Laboral"),
        ]
        
        casos = [
            Caso(descripcion_hechos="Contrato de arrendamiento", id_usuario=1, estado="asignado"),
            Caso(descripcion_hechos="Accidente de trabajo", id_usuario=1, estado="en_revision"),
            Caso(descripcion_hechos="Divorcio con bienes", id_usuario=1, estado="asignado"),
        ]
        
        sesion.add_all(otros_estudiantes)
        sesion.add_all(asesores)
        sesion.commit() # Hacemos un commit para que los IDs se generen antes de las asignaciones

        # Ahora que los IDs existen, creamos las evidencias y asignaciones
        evidencias = [
            Evidencia(id_caso=1, nombre_archivo="contrato.pdf", ruta_archivo="1/contrato.pdf", tipo="application/pdf"),
            Evidencia(id_caso=2, nombre_archivo="certificado.png", ruta_archivo="2/certificado.png", tipo="image/png"),
            Evidencia(id_caso=3, nombre_archivo="escrituras.pdf", ruta_archivo="3/escrituras.pdf", tipo="application/pdf"),
        ]
        
        # Asignamos el caso 1 a Ana (ID de estudiante 1)
        # Asignamos el caso 3 a Laura (ID de estudiante 3)
        asignaciones = [
            Asignacion(id_caso=1, id_estudiante=1, id_asesor=1),
            Asignacion(id_caso=3, id_estudiante=3, id_asesor=2),
        ]
        
        sesion.add_all(casos)
        sesion.add_all(evidencias)
        sesion.add_all(asignaciones)
        
        sesion.commit()

        print("-> Se han añadido 3 estudiantes y 3 asesores.")
        print("-> Se han añadido 3 casos de prueba con evidencias y asignaciones.")
        print("EXITO: La base de datos ha sido reseteada y poblada.")

if __name__ == "__main__":
    resetear_y_poblar_la_base_de_datos()