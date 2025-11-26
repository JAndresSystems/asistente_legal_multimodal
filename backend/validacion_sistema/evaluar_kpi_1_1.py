# backend/validacion_sistema/evaluar_kpi_1_1.py
import sys
import os
import pandas as pd
import time # Para evitar saturar la API

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

# --- DATASET EQUILIBRADO (15 CASOS) ---
CASOS_PRUEBA = [
    # 1. Admisibles Claros
    {"id": "CP-01", "tipo": "Civil < 50 SMLMV", "descripcion": "Choque simple, daños 15M.", "archivos": ["cedula.pdf", "croquis.pdf"], "ground_truth_admisible": True},
    {"id": "CP-02", "tipo": "Laboral < 20 SMLMV", "descripcion": "Despido injustificado, reclamo 3M.", "archivos": ["cedula.pdf", "carta.pdf"], "ground_truth_admisible": True},
    {"id": "CP-03", "tipo": "Familia (Alimentos)", "descripcion": "Fijación cuota alimentos hijo.", "archivos": ["cedula.pdf", "registro.pdf"], "ground_truth_admisible": True},
    {"id": "CP-04", "tipo": "Tutela (Salud)", "descripcion": "EPS niega medicamentos.", "archivos": ["cedula.pdf", "orden.pdf"], "ground_truth_admisible": True},
    {"id": "CP-05", "tipo": "Divorcio Mutuo", "descripcion": "Divorcio sin bienes.", "archivos": ["cedula.pdf", "registro_matrimonio.pdf"], "ground_truth_admisible": True},

    # 2. Inadmisibles Claros
    {"id": "CP-06", "tipo": "Civil > 50 SMLMV", "descripcion": "Incumplimiento contrato edificio 800M.", "archivos": ["cedula.pdf", "contrato.pdf"], "ground_truth_admisible": False},
    {"id": "CP-07", "tipo": "Comercial (Prohibido)", "descripcion": "Cobro pagaré entre empresas.", "archivos": ["pagare.pdf"], "ground_truth_admisible": False},
    {"id": "CP-08", "tipo": "Laboral > 20 SMLMV", "descripcion": "Indemnización laboral 150M.", "archivos": ["cedula.pdf"], "ground_truth_admisible": False},
    {"id": "CP-09", "tipo": "Penal (Homicidio)", "descripcion": "Me acusaron de homicidio.", "archivos": ["notificacion.pdf"], "ground_truth_admisible": False},
    {"id": "CP-10", "tipo": "Penal (Robo)", "descripcion": "Denuncia robo celular.", "archivos": [], "ground_truth_admisible": False},

    # 3. Casos Especiales / Bordes
    {"id": "CP-11", "tipo": "Falta Info (Admisible)", "descripcion": "Quiero custodia de mis hijos.", "archivos": [], "ground_truth_admisible": True}, # Tema válido
    {"id": "CP-12", "tipo": "Admin (Tutela)", "descripcion": "Derecho petición no respondido.", "archivos": ["radicado.pdf"], "ground_truth_admisible": True},
    {"id": "CP-13", "tipo": "Civil Borde (45M)", "descripcion": "Deuda de 45 millones.", "archivos": ["letra.pdf"], "ground_truth_admisible": True},
    {"id": "CP-14", "tipo": "Admin Cuantía (Inadmisible)", "descripcion": "Nulidad contrato estatal 300M.", "archivos": [], "ground_truth_admisible": False},
    {"id": "CP-15", "tipo": "Sin Fundamento", "descripcion": "Demandar vecino porque me cae mal.", "archivos": [], "ground_truth_admisible": False}
]

def evaluar_sistema():
    resultados = []
    tp, fp, fn, tn = 0, 0, 0, 0
    META_KPI = 0.95

    print(f"\n--- INICIANDO AUDITORÍA (15 CASOS) ---")

    for i, caso in enumerate(CASOS_PRUEBA):
        print(f"[{i+1}/15] Caso {caso['id']} ({caso['tipo']})...")
        
        estado_mock = {
            "rutas_archivos_evidencia": caso["archivos"], 
            "texto_adicional_usuario": caso["descripcion"],
            "historial_chat": [],
            "id_caso": 999
        }

        try:
            resp = nodo_agente_triaje(estado_mock)
            res_triaje = resp.get("resultado_triaje", {})
            
            admisible_ia = res_triaje.get("admisible", False)
            justificacion = res_triaje.get("justificacion", "Sin justificación")
            gt = caso["ground_truth_admisible"]
            
            if gt and admisible_ia:
                tp += 1
                res = "TP"
            elif not gt and not admisible_ia:
                tn += 1
                res = "TN"
            elif not gt and admisible_ia:
                fp += 1
                res = "FP (Error)"
                print(f"   ⚠️ FALLO FP: {justificacion}")
            elif gt and not admisible_ia:
                fn += 1
                res = "FN (Error)"
                print(f"   ⚠️ FALLO FN: {justificacion}")

            resultados.append({
                "ID": caso["id"],
                "Tipo": caso["tipo"],
                "IA": admisible_ia,
                "Real": gt,
                "Res": res,
                "Justificación": justificacion
            })
            
            # PAUSA DE SEGURIDAD: Esperar 2 segundos entre llamadas para evitar errores 504/429 de Google
            time.sleep(2)

        except Exception as e:
            print(f"   !!! ERROR TÉCNICO: {e}")

    # Cálculo
    denominador = tp + fp + (fn * 1.5)
    p_an = tp / denominador if denominador > 0 else 0.0
    
    print("\n" + "="*30)
    print(f"KPI 1.1: {p_an:.4f}")
    print(f"TP:{tp} TN:{tn} FP:{fp} FN:{fn}")
    print("="*30)
    
    df = pd.DataFrame(resultados)
    df.to_excel(os.path.join(current_dir, "reporte_validacion_kpi_1_1.xlsx"), index=False)
    print(f"Reporte guardado.")

if __name__ == "__main__":
    evaluar_sistema()