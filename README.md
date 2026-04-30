# Cluster Doc AI - Sistema Distribuido de Procesamiento de Documentos

Este proyecto es una plataforma distribuida diseñada para procesar, analizar y clasificar documentos PDF utilizando Modelos de Lenguaje Grande (LLMs) ejecutados localmente con **Ollama**. El sistema consta de **4 máquinas en total** para repartir la carga computacional, permitiendo que la IA se ejecute de manera eficiente.

## 🏗 Arquitectura de las 4 Máquinas

Para asegurar la mayor eficiencia, **la Base de Datos se almacena en el Servidor Principal (Frontend)**. Esto libera la memoria RAM y procesador de las Máquinas 1, 2 y 3 para que se dediquen exclusivamente a correr los modelos pesados de Inteligencia Artificial.

### 1. Servidor Principal (Gateway Frontend + Base de Datos)
*   **Rol:** Gestiona usuarios, aloja la Interfaz Web (UI), recibe los PDFs, almacena la base de datos y sirve los archivos.
*   **Tecnologías:** Docker (MongoDB), FastAPI, HTML/JS/CSS.
*   **Puerto API:** `8000` | **Puerto DB:** `27017`

### 2. Máquina 1: El Lector Profundo
*   **Rol:** Extrae el texto del PDF y usa un LLM pesado para limpiar la estructura y contexto.
*   **Modelo de Ollama:** `llama3.1:8b`
*   **Tecnologías:** PyMuPDF, FastAPI.
*   **Puerto API:** `8001`

### 3. Máquina 2: El Extractor Analítico
*   **Rol:** Actúa como analista, leyendo el texto limpio para extraer los 5 puntos más importantes en viñetas.
*   **Modelo de Ollama:** `llama3.2:3b` (o `qwen2.5:3b`)
*   **Tecnologías:** FastAPI.
*   **Puerto API:** `8002`

### 4. Máquina 3: El Sintetizador y Juez
*   **Rol:** Genera el resumen de 3 líneas, asigna la urgencia en color (ROJO, ÁMBAR, VERDE) y se conecta a la Base de Datos para guardar el resultado final.
*   **Modelo de Ollama:** `phi3`
*   **Tecnologías:** FastAPI, PyMongo.
*   **Puerto API:** `8003`

---

## 🌐 Guía de Despliegue (Cómo configurar cada máquina)

Si vas a presentar este proyecto utilizando 4 computadoras conectadas en red (LAN), sigue esta guía para cada computadora.
*(Asegúrate de que todas las computadoras estén conectadas al mismo módem/router).*

### Preparación (En el Servidor Principal)
1.  Pasa el código del proyecto a la computadora elegida como Servidor Principal.
2.  Abre una terminal y averigua la IP de esta máquina (ej. ejecutando `ipconfig` en Windows o `ip a` en Linux). Supongamos que su IP es `192.168.1.10`.
3.  Levanta la base de datos ejecutando: `docker-compose up -d`.
4.  Instala las dependencias (`pip install -r requirements.txt`).
5.  Entra a la carpeta `frontend` y ejecuta:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

### Preparación (En la Máquina 1)
1.  Pasa la carpeta `machine1` a esta computadora.
2.  Averigua la IP de la Máquina 2 (porque hacia ella enviará los datos). Supongamos que la M2 tiene la IP `192.168.1.20`.
3.  Instala Ollama y descarga el modelo: `ollama pull llama3.1:8b`.
4.  Instala dependencias (`pip install fastapi uvicorn requests PyMuPDF python-multipart`).
5.  Inicia el servicio apuntando a la M2:
    ```bash
    export MACHINE_2_URL="http://192.168.1.20:8002/process"
    uvicorn main:app --host 0.0.0.0 --port 8001
    ```
    *(Nota: Si usas Windows en vez de export usa `set MACHINE_2_URL=...`)*

### Preparación (En la Máquina 2)
1.  Pasa la carpeta `machine2` a esta computadora.
2.  Averigua la IP de la Máquina 3 (hacia donde enviará los datos). Supongamos que la M3 tiene la IP `192.168.1.30`.
3.  Instala Ollama y descarga el modelo: `ollama pull llama3.2:3b`.
4.  Instala dependencias (`pip install fastapi uvicorn requests pydantic`).
5.  Inicia el servicio apuntando a la M3:
    ```bash
    export MACHINE_3_URL="http://192.168.1.30:8003/process"
    uvicorn main:app --host 0.0.0.0 --port 8002
    ```

### Preparación (En la Máquina 3)
1.  Pasa la carpeta `machine3` a esta computadora.
2.  Como esta máquina debe guardar el resultado final en la Base de Datos, necesita la IP del **Servidor Principal** (que en este ejemplo era `192.168.1.10`).
3.  Instala Ollama y descarga el modelo: `ollama pull phi3`.
4.  Instala dependencias (`pip install fastapi uvicorn requests pydantic pymongo`).
5.  Inicia el servicio apuntando a la Base de Datos del Servidor Principal:
    ```bash
    export MONGO_URI="mongodb://192.168.1.10:27017"
    uvicorn main:app --host 0.0.0.0 --port 8003
    ```

---

## 🚀 Cómo ejecutarlo todo localmente (en una sola computadora)
Si quieres probar todo en tu misma PC antes de llevarlo a las 4 máquinas físicas:
1.  Asegúrate de tener Docker corriendo y ejecuta `docker-compose up -d`.
2.  Asegúrate de tener corriendo tu Ollama local con los 3 modelos descargados.
3.  Simplemente ejecuta el script automatizado:
    ```bash
    chmod +x run_cluster.sh
    ./run_cluster.sh
    ```
4.  Visita `http://localhost:8000` en tu navegador.
