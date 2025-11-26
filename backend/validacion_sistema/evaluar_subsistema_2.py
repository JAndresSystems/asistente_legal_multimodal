# backend/validacion_sistema/evaluar_subsistema_2.py
import sys
import os
import pandas as pd
import random
from sqlmodel import SQLModel, Session, create_engine, select, func
from typing import List

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

# Importamos tus modelos reales
try:
    from backend.api.modelos_compartidos import Estudiante, Asesor, AreaEspecialidad, Asignacion, Caso, EstadoCaso
    # Importamos la lógica de reparto real
    from backend.agentes.nodos_del_grafo import encontrar_persona_con_menos_carga
    print("✅ Modelos importados correctamente.")
except ImportError as e:
    print(f"❌ Error de importación: {e}")
    sys.exit(1)

# --- CONFIGURACIÓN DE BASE DE DATOS EN MEMORIA (SIMULACIÓN) ---
engine_test = create_engine("sqlite:///:memory:") # BD volátil solo para el test

def preparar_entorno_simulacion():
    """Crea estudiantes y áreas ficticias para la prueba (INCLUYENDO FAMILIA)."""
    SQLModel.metadata.create_all(engine_test)
    
    with Session(engine_test) as session:
        # 1. Crear Áreas (Ahora son 5)
        areas = [
            AreaEspecialidad(nombre="Derecho Privado"), # ID 1
            AreaEspecialidad(nombre="Derecho Publico"), # ID 2
            AreaEspecialidad(nombre="Derecho Penal"),   # ID 3
            AreaEspecialidad(nombre="Derecho Laboral"), # ID 4
            AreaEspecialidad(nombre="Derecho Familia")  # ID 5 
        ]
        session.add_all(areas)
        session.commit()
        
        # 2. Crear Asesores (1 por área)
        for i, area in enumerate(areas, 1):
            asesor = Asesor(
                nombre_completo=f"Profe {area.nombre}", 
                id_area_especialidad=area.id,
                email=f"profe{i}@test.com", contrasena_hash="x", rol="asesor"
            )
            session.add(asesor)
        
        # 3. Crear Estudiantes (Distribución realista)
        # Privado: 3
        # Público: 2
        # Penal: 2
        # Laboral: 3
        # Familia: 3 (Suele ser alta demanda)
        estudiantes_data = [
            ("Estudiante Priv 1", 1), ("Estudiante Priv 2", 1), ("Estudiante Priv 3", 1),
            ("Estudiante Pub 1", 2), ("Estudiante Pub 2", 2),
            ("Estudiante Pen 1", 3), ("Estudiante Pen 2", 3),
            ("Estudiante Lab 1", 4), ("Estudiante Lab 2", 4), ("Estudiante Lab 3", 4),
            ("Estudiante Fam 1", 5), ("Estudiante Fam 2", 5), ("Estudiante Fam 3", 5)
        ]
        
        for nombre, id_area in estudiantes_data:
            est = Estudiante(
                nombre_completo=nombre, 
                id_area_especialidad=id_area,
                email=f"{nombre.replace(' ', '')}@test.com", contrasena_hash="x", rol="estudiante"
            )
            session.add(est)
        
        session.commit()
        print(f"✅ Entorno Simulado Creado: 5 Áreas (Inc. Familia), 5 Asesores, {len(estudiantes_data)} Estudiantes.")

def calcular_gini_inverso(cargas: List[int]) -> float:
    """
    Calcula el KPI 2.1: Coeficiente de Balanceo (1 - Gini).
    """
    n = len(cargas)
    if n == 0 or sum(cargas) == 0: return 0.0
    
    media = sum(cargas) / n
    suma_diferencias = 0
    
    for x_i in cargas:
        for x_j in cargas:
            suma_diferencias += abs(x_i - x_j)
            
    gini = suma_diferencias / (2 * (n**2) * media)
    gini_inverso = 1 - gini
    return gini_inverso

def ejecutar_auditoria_reparto():
    preparar_entorno_simulacion()
    
    # --- SIMULACIÓN DE 50 CASOS ---
    casos_a_asignar = []
    
    # Ahora incluimos "Derecho Familia" en la tómbola
    areas_nombres = [
        "Derecho Privado", 
        "Derecho Publico", 
        "Derecho Penal", 
        "Derecho Laboral", 
        "Derecho Familia" 
    ]
    
    # Generamos 50 casos aleatorios
    for i in range(1, 51):
        area_random = random.choice(areas_nombres)
        casos_a_asignar.append({"id_caso": i, "area_competencia": area_random})

    print(f"\n--- INICIANDO ASIGNACIÓN DE {len(casos_a_asignar)} CASOS ---")
    
    aciertos_tematicos = 0
    errores_tematicos = 0
    
    with Session(engine_test) as session:
        for caso_mock in casos_a_asignar:
            # 1. Simular lógica del nodo_agente_repartidor
            nombre_area = caso_mock["area_competencia"]
            
            # Buscar ID del área
            area_obj = session.exec(select(AreaEspecialidad).where(AreaEspecialidad.nombre == nombre_area)).first()
            
            if not area_obj:
                print(f"⚠️ Área no encontrada: {nombre_area}")
                continue

            id_area = area_obj.id
            
            # USAR LA FUNCIÓN REAL DE TU BACKEND
            id_estudiante_elegido = encontrar_persona_con_menos_carga(session, Estudiante, id_area)
            
            # Nota: Solo necesitamos asignar estudiante para probar balanceo, el asesor es secundario en este KPI
            if id_estudiante_elegido:
                # Validar KPI 2.2 (Alineación Temática)
                estudiante = session.get(Estudiante, id_estudiante_elegido)
                if estudiante.id_area_especialidad == id_area:
                    aciertos_tematicos += 1
                else:
                    errores_tematicos += 1
                    print(f"❌ Error de asignación: Caso {nombre_area} -> Estudiante de {estudiante.area.nombre}")
                
                # Registrar asignación en BD (Esto afecta la carga para el siguiente ciclo)
                # Creamos una asignación mínima válida
                nueva_asignacion = Asignacion(
                    id_caso=caso_mock["id_caso"],
                    id_estudiante=id_estudiante_elegido,
                    id_asesor=1 # Dummy ID, no afecta el KPI de carga estudiantil
                )
                session.add(nueva_asignacion)
                session.commit() # Commit para que el conteo se actualice para el siguiente caso
            else:
                print(f"⚠️ No se encontró estudiante disponible para {nombre_area}.")

        # --- CÁLCULO DE MÉTRICAS ---
        
        # KPI 2.2: Precisión Temática
        total_casos = len(casos_a_asignar)
        kpi_alineacion = (aciertos_tematicos / total_casos) * 100 if total_casos > 0 else 0
        
        # KPI 2.1: Balanceo de Cargas (Gini Inverso)
        estudiantes = session.exec(select(Estudiante)).all()
        cargas_finales = []
        detalle_cargas = []
        
        for est in estudiantes:
            carga = session.exec(
                select(func.count(Asignacion.id)).where(Asignacion.id_estudiante == est.id)
            ).one()
            cargas_finales.append(carga)
            # Obtenemos el nombre del área de forma segura
            nombre_area_est = est.area.nombre if est.area else "Sin Área"
            detalle_cargas.append({"Estudiante": est.nombre_completo, "Área": nombre_area_est, "Casos Asignados": carga})
            
        kpi_gini = calcular_gini_inverso(cargas_finales)

    # --- REPORTE ---
    print("\n" + "="*50)
    print("RESULTADOS SUBSISTEMA 2 (AGENTE DE REPARTO)")
    print("="*50)
    
    print(f"\n📊 KPI 2.2: Precisión Alineación Temática (A_Tema)")
    print(f"   Aciertos: {aciertos_tematicos}/{total_casos}")
    print(f"   Resultado: {kpi_alineacion:.2f}%")
    print(f"   Meta: > 95% -> {'APROBADO ✅' if kpi_alineacion >= 95 else 'RECHAZADO ❌'}")

    print(f"\n⚖️ KPI 2.1: Coeficiente Balanceo (Gini Inverso)")
    print(f"   Distribución de Cargas: {cargas_finales}")
    print(f"   Resultado: {kpi_gini:.4f}")
    print(f"   Meta: > 0.80 -> {'APROBADO ✅' if kpi_gini >= 0.8 else 'RECHAZADO ❌'}")

    # Exportar Excel
    df = pd.DataFrame(detalle_cargas)
    # Añadir resumen
    df.loc[len(df)] = {"Estudiante": "KPI 2.1 (Gini)", "Área": f"{kpi_gini:.4f}", "Casos Asignados": ""}
    df.loc[len(df)] = {"Estudiante": "KPI 2.2 (Tema)", "Área": f"{kpi_alineacion:.2f}%", "Casos Asignados": ""}
    
    ruta_excel = os.path.join(current_dir, "reporte_validacion_subsistema_2.xlsx")
    df.to_excel(ruta_excel, index=False)
    print(f"\n📄 Reporte detallado guardado en: {ruta_excel}")

if __name__ == "__main__":
    ejecutar_auditoria_reparto()