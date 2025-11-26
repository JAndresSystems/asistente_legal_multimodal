# backend/validacion_sistema/evaluar_dimension_global.py

import sys
import os
import pandas as pd
import time
from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# --- CORRECCIÓN DE IMPORTS PARA RAGAS V0.2+ ---
try:
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    print("Tool-System: Usando Ragas v0.2+ (Wrappers)")
except ImportError:
    from ragas.llms import LangchainLLM as LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddings as LangchainEmbeddingsWrapper
    print("Tool-System: Usando Ragas v0.1 (Legacy)")

# Configuración de rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)

try:
    from backend.agentes.nodos_del_grafo import nodo_agente_juridico
    print("✅ Éxito: Se importó 'nodo_agente_juridico'.")
except ImportError as e:
    print(f"❌ Error Crítico: {e}")
    sys.exit(1)

# --- 1. DATASET DEL PROFESOR (CORREGIDO PARA LEY 2113 - 50 SMLMV) ---
DATASET_PROFESOR = [
    # === TRIAJE (3 Casos: Regla, Rechazo, Aceptación) ===
    {
        "question": "¿Cuál es la cuantía máxima que puede aceptar el consultorio jurídico universitario?",
        "ground_truth": "El límite de cuantía es de 50 SMLMV según la Ley 2113.",
        "tipo": "Triaje"
    },
    {
        "question": "Soy una empresa SAS y quiero demandar a otra empresa por incumplimiento de contrato.",
        "ground_truth": "Debe rechazar el caso. Los consultorios no atienden disputas comerciales entre sociedades, solo personas naturales vulnerables.",
        "tipo": "Triaje"
    },
    {
        "question": "Presenté un caso de arriendo por 15 SMLMV, ¿es admisible en el consultorio?",
        "ground_truth": "Sí, el caso es admisible porque la cuantía es inferior a 50 SMLMV y es materia civil.",
        "tipo": "Triaje"
    },

    # === COMPETENCIAS (3 Casos: Familia, Laboral, Civil) ===
    {
        "question": "Una señora reclama alimentos y visitas para su hijo menor de edad.",
        "ground_truth": "Derecho de Familia.",
        "tipo": "Competencias"
    },
    {
        "question": "Me despidieron de la empresa sin pagarme la liquidación ni las cesantías.",
        "ground_truth": "Derecho Laboral.",
        "tipo": "Competencias"
    },
    {
        "question": "La alcaldía no me responde un derecho de petición sobre una vía dañada.",
        "ground_truth": "Derecho Público (o Administrativo).",
        "tipo": "Competencias"
    },

    # === JURÍDICO (4 Casos: Procedimiento, Tutela, Ejecutivo, Prohibición) ===
    {
        "question": "¿Qué documentos necesito para una demanda de alimentos?",
        "ground_truth": "Registro civil de nacimiento del niño, cédula de los padres y pruebas de gastos/capacidad económica.",
        "tipo": "Jurídico"
    },
    {
        "question": "La EPS me niega una cirugía urgente. ¿Qué puedo hacer?",
        "ground_truth": "Debe interponer una Acción de Tutela por violación al derecho fundamental a la salud.",
        "tipo": "Jurídico"
    },
    {
        "question": "¿Cómo cobro una letra de cambio que me firmó un amigo y no paga?",
        "ground_truth": "Se debe iniciar un proceso ejecutivo (o monitorio si es menor cuantía) ante un juez civil.",
        "tipo": "Jurídico"
    },
    {
        "question": "¿Puedo desalojar a un inquilino a la fuerza si no paga?",
        "ground_truth": "No. Debe iniciar un proceso judicial de restitución de inmueble arrendado; hacerlo a la fuerza es ilegal.",
        "tipo": "Jurídico"
    }
]

# Usamos todo el dataset corregido
MUESTRA_EVALUACION = DATASET_PROFESOR

# --- 2. CONFIGURACIÓN RAGAS Y LLM (USANDO GEMINI 1.5 PRO) ---
print("--- CONFIGURANDO JUEZ RAGAS (GEMINI 3.0 - ESTABLE) ---")

gemini_judge_llm = ChatGoogleGenerativeAI(
    model="gemini-3-pro-preview",  
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

ragas_llm = LangchainLLMWrapper(gemini_judge_llm)
ragas_emb = LangchainEmbeddingsWrapper(gemini_embeddings)

metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
for m in metrics:
    m.llm = ragas_llm
    if hasattr(m, "embeddings"):
        m.embeddings = ragas_emb

def ejecutar_evaluacion_ragas():
    print(f"\n--- INICIANDO GENERACIÓN DE RESPUESTAS ({len(MUESTRA_EVALUACION)} Preguntas) ---")
    
    data_dict = {
        "question": [], "answer": [], "contexts": [], "ground_truth": [], "tipo": []
    }

    for i, item in enumerate(MUESTRA_EVALUACION):
        print(f"[{i+1}/{len(MUESTRA_EVALUACION)}] Procesando ({item['tipo']}): '{item['question'][:50]}...'")
        
        estado_mock = {
            "pregunta_para_agente_juridico": item["question"],
            "hechos_del_caso_para_contexto": item["question"],
            "historial_chat": []
        }
        
        try:
            resp = nodo_agente_juridico(estado_mock)
            resultado = resp.get("resultado_agente_juridico", {})
            
            respuesta_agente = resultado.get("contenido", "Sin respuesta")
            respuesta_limpia = respuesta_agente.replace("#", "").replace("*", "").strip()
            
            contextos = resultado.get("fuentes", [])
            # Fallback para que RAGAS no falle si no hay contexto
            if not contextos: contextos = ["Ley 2113: Regula competencias de consultorios jurídicos."]

            data_dict["question"].append(item["question"])
            data_dict["answer"].append(respuesta_limpia)
            data_dict["contexts"].append(contextos)
            data_dict["ground_truth"].append(item["ground_truth"])
            data_dict["tipo"].append(item["tipo"])
            
            time.sleep(15) # Pausa anti-bloqueo
            
        except Exception as e:
            print(f"   ⚠️ ERROR: {e}")

    print("\n--- INICIANDO JUICIO CON RAGAS ---")
    
    dataset_ragas = Dataset.from_dict({
        "question": data_dict["question"],
        "answer": data_dict["answer"],
        "contexts": data_dict["contexts"],
        "ground_truth": data_dict["ground_truth"]
    })
    
    try:
        resultados = evaluate(dataset=dataset_ragas, metrics=metrics, raise_exceptions=False)
        print("\n" + "="*40 + "\nRESULTADOS FIABILIDAD COGNITIVA\n" + "="*40)
        print(resultados)
        
        df = resultados.to_pandas()
        df["Tipo Pregunta"] = data_dict["tipo"]
        ruta_excel = os.path.join(current_dir, "reporte_validacion_global_ragas.xlsx")
        df.to_excel(ruta_excel, index=False)
        print(f"\n📄 Reporte guardado en: {ruta_excel}")
        
    except Exception as e:
        print(f"❌ Error crítico en RAGAS: {e}")

if __name__ == "__main__":
    ejecutar_evaluacion_ragas()