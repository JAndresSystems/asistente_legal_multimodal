# backend/validacion_sistema/evaluar_kpi_1_2.py
import sys
import os
import pandas as pd
import unidecode 
import time

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

try:
    from backend.agentes.nodos_del_grafo import nodo_agente_triaje
    print("✅ Éxito: Se importó 'nodo_agente_triaje'.")
except ImportError as e:
    print(f"❌ Error Crítico: {e}")
    sys.exit(1)

# --- DATASET DE 15 CASOS DE PRUEBA (VACÍOS PROBATORIOS) ---
CASOS_VACIOS = [
    # --- BLOQUE 1: LABORAL (Faltan contratos/pruebas) ---
    {"id": "VAC-01", "tipo": "Laboral", "descripcion": "Me despidieron ayer sin causa. Adjunto mi cédula.", "archivos": ["cedula.pdf"], "docs_faltantes": ["contrato", "carta", "despido", "liquidacion"]},
    {"id": "VAC-02", "tipo": "Laboral", "descripcion": "Acoso laboral en la empresa. Tengo contrato.", "archivos": ["contrato.pdf"], "docs_faltantes": ["cedula", "pruebas", "correos", "testigos"]},
    {"id": "VAC-03", "tipo": "Laboral", "descripcion": "Reclamo de horas extras no pagadas.", "archivos": ["contrato.pdf"], "docs_faltantes": ["cedula", "registro", "horario", "desprendibles"]},

    # --- BLOQUE 2: FAMILIA (Faltan registros civiles) ---
    {"id": "VAC-04", "tipo": "Familia", "descripcion": "Demanda de alimentos para mi hijo Juan.", "archivos": ["cedula.pdf"], "docs_faltantes": ["registro", "civil", "nacimiento"]},
    {"id": "VAC-05", "tipo": "Familia", "descripcion": "Divorcio de mutuo acuerdo.", "archivos": ["registro_matrimonio.pdf"], "docs_faltantes": ["cedula", "identidad"]},
    {"id": "VAC-06", "tipo": "Familia", "descripcion": "Custodia de mi hija María. Tengo mi cédula.", "archivos": ["cedula.pdf"], "docs_faltantes": ["registro", "civil", "nacimiento"]},

    # --- BLOQUE 3: CIVIL (Faltan contratos/facturas) ---
    {"id": "VAC-07", "tipo": "Civil", "descripcion": "Me deben un dinero de un arriendo. Tengo contrato.", "archivos": ["contrato.pdf"], "docs_faltantes": ["cedula", "recibos", "facturas"]},
    {"id": "VAC-08", "tipo": "Civil", "descripcion": "Accidente de tránsito. Tengo cédula y fotos.", "archivos": ["cedula.pdf", "fotos.jpg"], "docs_faltantes": ["croquis", "informe", "transito"]},
    {"id": "VAC-09", "tipo": "Civil", "descripcion": "Letra de cambio sin pagar. Tengo la letra.", "archivos": ["letra.pdf"], "docs_faltantes": ["cedula"]},

    # --- BLOQUE 4: TUTELAS/SALUD (Faltan órdenes médicas) ---
    {"id": "VAC-10", "tipo": "Tutela", "descripcion": "EPS niega cita con especialista. Tengo cédula.", "archivos": ["cedula.pdf"], "docs_faltantes": ["orden", "medica", "historia", "negacion"]},
    {"id": "VAC-11", "tipo": "Tutela", "descripcion": "No me entregan medicamentos. Tengo fórmula.", "archivos": ["formula.pdf"], "docs_faltantes": ["cedula", "sisben"]},
    
    # --- BLOQUE 5: CASOS COMPLETOS (No debe pedir nada) ---
    {"id": "CMP-12", "tipo": "Completo", "descripcion": "Demanda alimentos completa.", "archivos": ["cedula.pdf", "sisben.pdf", "recibo.pdf", "registro_civil.pdf"], "docs_faltantes": []},
    {"id": "CMP-13", "tipo": "Completo", "descripcion": "Tutela salud completa.", "archivos": ["cedula.pdf", "sisben.pdf", "orden_medica.pdf", "historia.pdf"], "docs_faltantes": []},
    {"id": "CMP-14", "tipo": "Completo", "descripcion": "Laboral completo.", "archivos": ["cedula.pdf", "sisben.pdf", "contrato.pdf", "carta_despido.pdf"], "docs_faltantes": []},
    {"id": "CMP-15", "tipo": "Completo", "descripcion": "Accidente completo.", "archivos": ["cedula.pdf", "sisben.pdf", "croquis.pdf", "fotos.pdf"], "docs_faltantes": []}
]

def normalizar(texto):
    if not texto: return ""
    return unidecode.unidecode(texto.lower())

def evaluar_deteccion_vacios():
    total_docs_reales = 0
    total_docs_detectados = 0
    resultados = []

    print("\n" + "="*60)
    print(f" INICIANDO EVALUACIÓN KPI 1.2 (15 CASOS) ".center(60, "="))
    print("="*60)

    for caso in CASOS_VACIOS:
        print(f"\n🔍 Evaluando Caso {caso['id']} ({caso['tipo']})...")
        
        estado_mock = {
            "rutas_archivos_evidencia": caso["archivos"], 
            "texto_adicional_usuario": caso["descripcion"]
        }

        try:
            resp = nodo_agente_triaje(estado_mock)
            res_triaje = resp.get("resultado_triaje", {})
            
            pregunta_ia = res_triaje.get("pregunta_para_usuario", "")
            info_suficiente = res_triaje.get("informacion_suficiente", False)
            
            pregunta_norm = normalizar(pregunta_ia)
            faltantes_reales = caso["docs_faltantes"]
            
            # Lógica de Evaluación
            if len(faltantes_reales) == 0: # Caso Completo
                exito = info_suficiente # Debe ser True (Info suficiente = True)
                tipo_res = "✅ CORRECTO (Completo)" if exito else "❌ ERROR (Pidió extra)"
            else: # Caso Incompleto
                # Debe pedir docs (info_suficiente=False) Y mencionar al menos una palabra clave
                if info_suficiente:
                    exito = False
                    tipo_res = "❌ ERROR (Falso Positivo - Dijo completo)"
                else:
                    # Buscar coincidencias de palabras clave
                    encontrado = False
                    keywords_encontradas = []
                    for keyword in faltantes_reales:
                        if keyword in pregunta_norm:
                            encontrado = True
                            keywords_encontradas.append(keyword)
                    exito = encontrado
                    tipo_res = f"✅ DETECTADO ({', '.join(keywords_encontradas)})" if exito else "⚠️ NO DETECTADO (Pregunta vaga)"

            # Métricas
            total_docs_reales += 1
            total_docs_detectados += 1 if exito else 0

            print(f"   📝 IA Preguntó: '{pregunta_ia[:60]}...'")
            print(f"   🎯 Resultado: {tipo_res}")
            
            # Pequeña pausa para evitar saturar la API
            time.sleep(1.5)

            resultados.append({
                "ID": caso["id"],
                "Tipo": caso["tipo"],
                "Faltaban": str(faltantes_reales),
                "IA Preguntó": pregunta_ia,
                "Resultado": tipo_res,
                "Exito": 1 if exito else 0
            })

        except Exception as e:
            print(f"   🔥 ERROR TÉCNICO: {e}")

    # Cálculo KPI 1.2
    indice_dvp = total_docs_detectados / total_docs_reales if total_docs_reales > 0 else 0
    
    print("\n" + "="*60)
    print(f" RESULTADOS FINALES KPI 1.2 ".center(60, "="))
    print("="*60)
    print(f"📊 Total Casos Evaluados: {total_docs_reales}")
    print(f"✅ Vacíos Detectados Correctamente: {total_docs_detectados}")
    print(f"❌ Fallos en Detección: {total_docs_reales - total_docs_detectados}")
    print("-" * 60)
    print(f"🏆 KPI 1.2 (Índice Detección): {indice_dvp:.4f}")
    
    # Meta sugerida: > 0.8 (80%)
    meta = 0.8
    estado = "APROBADO 🟢" if indice_dvp >= meta else "RECHAZADO 🔴"
    print(f"🏁 Estado Final: {estado} (Meta: {meta})")
    print("="*60)
    
    # Guardar
    df = pd.DataFrame(resultados)
    df.to_excel(os.path.join(current_dir, "reporte_validacion_kpi_1_2.xlsx"), index=False)
    print(f"\n📄 Reporte Excel guardado exitosamente.")

if __name__ == "__main__":
    evaluar_deteccion_vacios()