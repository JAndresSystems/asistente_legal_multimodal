from sqlmodel import Session
from sqlalchemy import text  # <-- 1. IMPORTACIÓN CLAVE
from .base_de_datos import motor
from .api.modelos_compartidos import Estudiante, Asesor

def poblar_datos_iniciales():
    """
    Script para poblar la base de datos con estudiantes y asesores de muestra.
    Se debe ejecutar una sola vez.
    """
    print("INFO: Iniciando el script de población de la base de datos (seeding)...")
    
    with Session(motor) as sesion:
        # Verificamos si ya hay datos para no duplicarlos
        # 2. CAMBIO CLAVE: "Envolvemos" el string de SQL con la función text()
        if sesion.exec(text("SELECT 1 FROM estudiante")).first():
            print("INFO: La base de datos ya contiene datos de muestra. Omitiendo la población.")
            return

        print("INFO: Creando estudiantes y asesores de muestra...")

        estudiantes = [
            Estudiante(nombre_completo="Ana Sofia Rojas", area_competencia="Derecho Privado"),
            Estudiante(nombre_completo="Carlos David Perez", area_competencia="Derecho Privado"),
            Estudiante(nombre_completo="Laura Valentina Gomez", area_competencia="Derecho Publico"),
            Estudiante(nombre_completo="Juan Felipe Moreno", area_competencia="Derecho Laboral"),
        ]

        asesores = [
            Asesor(nombre_completo="Dr. Ricardo Mendoza", area_competencia="Derecho Privado"),
            Asesor(nombre_completo="Dra. Monica Cifuentes", area_competencia="Derecho Publico"),
            Asesor(nombre_completo="Dr. Alberto Fernandez", area_competencia="Derecho Laboral"),
        ]

        sesion.add_all(estudiantes)
        sesion.add_all(asesores)
        sesion.commit()

        print("SUCCESS: Se han añadido 4 estudiantes y 3 asesores a la base de datos.")

if __name__ == "__main__":
    poblar_datos_iniciales()