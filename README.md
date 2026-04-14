#Se instalo en el computador de manera global : 

-> Instalar el "Traductor Universal" FFmpeg
Comando: Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))


backend
ven: .\venv\Scripts\Activate.ps1  
luego: (venv) PS C:\react\asistente_legal_multimodal> uvicorn backend.main:aplicacion --reload
(venv) PS C:\react\asistente_legal_multimodal> celery -A backend.tareas worker --loglevel=info -P solo
frontend
PS C:\react\asistente_legal_multimodal\frontend> npm run dev





---

## 🚀 Puesta en Marcha y Requisitos

Para ejecutar este proyecto en un entorno de desarrollo local, se necesitan las siguientes herramientas y dependencias.

### Requisitos del Sistema

Estas son las dependencias que deben estar instaladas directamente en el sistema operativo.

1.  **Python:** Versión 3.9 o superior.
2.  **PostgreSQL:** La base de datos relacional para la persistencia de datos.
3.  **Docker Desktop:** Necesario para ejecutar el contenedor de Redis.
4.  **FFmpeg:** La herramienta de procesamiento de audio y video. La forma más sencilla de instalarla en Windows 10/11 es a través de `winget` en una terminal de administrador:
    ```bash
    winget install Gyan.FFmpeg
    ```

### Configuración del Entorno

1.  **Clonar el Repositorio:**
    ```bash
    git clone [URL-DE-TU-REPOSITORIO]
    cd asistente_legal_multimodal
    ```

2.  **Configurar el Backend:**
    *   Crea y activa un entorno virtual de Python.
    *   Instala las dependencias: `pip install -r requirements.txt`
    *   Crea un archivo `.env` en la raíz del proyecto y configura las variables de la base de datos y las claves de API.

3.  **Configurar el Frontend:**
    *   Navega a la carpeta `frontend`.
    *   Instala las dependencias: `npm install`

### Ejecución

Para correr la aplicación, necesitas 3 terminales:
1.  **Redis (Docker):** `docker start broker-asistente-legal`
2.  **Backend (API):** `uvicorn backend.main:aplicacion --reload`
3.  **Backend (Worker):** `celery -A backend.tareas worker --loglevel=info -P solo`
4.  **Frontend:** `cd frontend && npm run dev`

pip install git+https://github.com/huggingface/transformers:librería llamada "Transformers" creada por una compañía llamada Hugging Face. Esta librería es como una caja de herramientas para usar modelos de inteligencia artificial (IA) pre-entrenados, como el que usamos para transcribir audio (Qwen2-Audio).


pip install librosa soundfile torchaudio: Instala tres librerías pequeñas para manejar archivos de audio en Python. Son como herramientas para "leer", "cortar" y "procesar" sonidos, ya que el modelo de IA necesita el audio en un formato específico.

pip install accelerate: . Esto permite que el modelo se cargue correctamente usando device_map="auto. 


pip install einops transformers_stream_generator "sentence-transformers>=3.0.0": einops y transformers_stream_generator: Instala las dos piezas que Qwen nos pidió explícitamente.
"sentence-transformers>=3.0.0": Le decimos a pip: "Asegúrate de que la librería sentence-transformers esté actualizada a la versión 3.0.0 o una más nueva". Esto resolverá el conflicto de importación.
