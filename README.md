# Cluster Doc AI - Sistema Distribuido de Procesamiento de Documentos

Este proyecto es una plataforma distribuida diseñada para procesar, analizar y clasificar documentos PDF utilizando Modelos de Lenguaje Grande (LLMs) ejecutados localmente con **Ollama**. El sistema consta de **4 máquinas (computadoras) en total** conectadas en red, las cuales se pasan el trabajo en cascada para repartir la carga computacional.

---

## 🏗 Arquitectura de las 4 Máquinas

Para asegurar la mayor eficiencia, **la Base de Datos se almacena en el Servidor Principal (Frontend)**. Esto libera la memoria RAM y procesador de las Máquinas 1, 2 y 3 para que se dediquen exclusivamente a correr los modelos pesados de Inteligencia Artificial de Ollama.

1. **Servidor Principal (Gateway Frontend + BD)**
   - **Rol:** Aloja la interfaz web, recibe los PDFs, guarda la base de datos (MongoDB) y sirve los archivos.
   - **Puerto API:** `8000` | **Puerto DB:** `27017`

2. **Máquina 1: El Lector Profundo**
   - **Rol:** Extrae el texto del PDF y usa un LLM pesado para limpiar la estructura y contexto.
   - **Modelo requerido:** `llama3.1:8b`
   - **Puerto API:** `8001`

3. **Máquina 2: El Extractor Analítico**
   - **Rol:** Lee el texto limpio para extraer los 5 puntos más importantes en viñetas.
   - **Modelo requerido:** `llama3.2:3b`
   - **Puerto API:** `8002`

4. **Máquina 3: El Sintetizador y Juez**
   - **Rol:** Genera el resumen final, asigna la prioridad en colores y se conecta a la Base de Datos para guardar el resultado.
   - **Modelo requerido:** `phi3`
   - **Puerto API:** `8003`

---

## 🛠 Requisitos y Preparación

1.  Todas las computadoras deben estar conectadas a la misma red local (mismo WiFi o router).
2.  Desactiva o configura el Firewall de Windows en todas las máquinas para permitir conexiones entrantes en redes privadas.
3.  Instala Ollama en las Máquinas 1, 2 y 3 y asegúrate de **descargar el modelo correspondiente en su respectiva computadora** abriendo la terminal y ejecutando:
    - En M1: `ollama pull llama3.1:8b`
    - En M2: `ollama pull llama3.2:3b`
    - En M3: `ollama pull phi3`

---

## 🌐 Configuración de Red (Código Editable)

Para que las máquinas puedan "platicar" entre sí a través de la red, necesitas editar el código fuente en cada una de ellas indicando la Dirección IP hacia dónde deben enviar los datos. Averigua la IP de cada PC (con `ipconfig` en Windows o `ip a` en Linux) y modifica los siguientes archivos:

### 1. En el Servidor Principal (Frontend)
Abre el archivo `frontend/main.py`. Ve a la **línea 24** y reemplaza `127.0.0.1` por la IP de la computadora que corre la Máquina 1.
```python
MACHINE_1_URL = os.getenv("MACHINE_1_URL", "http://IP_DE_MÁQUINA_1:8001/upload")
```

### 2. En la Máquina 1
Abre el archivo `machine1/main.py`. Ve a la **línea 10** y reemplaza la IP por la de la computadora que corre la Máquina 2.
```python
MACHINE_2_URL = os.getenv("MACHINE_2_URL", "http://IP_DE_MÁQUINA_2:8002/process")
```

### 3. En la Máquina 2
Abre el archivo `machine2/main.py`. Ve a la **línea 9** y reemplaza la IP por la de la computadora que corre la Máquina 3.
```python
MACHINE_3_URL = os.getenv("MACHINE_3_URL", "http://IP_DE_MÁQUINA_3:8003/process")
```

### 4. En la Máquina 3
Abre el archivo `machine3/main.py`. Ve a la **línea 11** y reemplaza la IP por la de la computadora del Servidor Principal (Frontend), para que pueda guardar los datos en MongoDB.
```python
MONGO_URI = os.getenv("MONGO_URI", "mongodb://IP_DEL_SERVIDOR_PRINCIPAL:27017")
```

*(Importante: En todos los archivos, la variable `OLLAMA_URL` debe seguir siendo `http://127.0.0.1:11434`, porque Ollama corre internamente dentro de cada una de sus respectivas máquinas).*

---

## 🚀 Guía de Ejecución

Una vez que las IPs están configuradas y los modelos descargados, enciende las máquinas en este orden:

### Paso 1: Encender la Base de Datos (Servidor Principal)
Abre una terminal en la raíz del proyecto y levanta Docker:
```bash
docker-compose up -d
```

### Paso 2: Encender los Microservicios
Ve físicamente a cada una de las 4 computadoras, abre una terminal en la carpeta principal del proyecto y activa el entorno virtual (si estás usando uno como `.llama`):
```bash
source .llama/bin/activate
pip install -r requirements.txt
```

Luego, entra a la subcarpeta correspondiente de esa máquina y enciende la API:

- **Servidor Principal:** `cd frontend` ➜ `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Máquina 1:** `cd machine1` ➜ `uvicorn main:app --host 0.0.0.0 --port 8001`
- **Máquina 2:** `cd machine2` ➜ `uvicorn main:app --host 0.0.0.0 --port 8002`
- **Máquina 3:** `cd machine3` ➜ `uvicorn main:app --host 0.0.0.0 --port 8003`

### Paso 3: Probar la plataforma
Desde el Servidor Principal (o desde cualquier dispositivo conectado al mismo WiFi, incluyendo un celular), abre tu navegador y entra a `http://localhost:8000` o a `http://IP_DEL_SERVIDOR_PRINCIPAL:8000`. 
Regístrate con un rol de "Subidor" y disfruta del procesamiento en cascada.
