# Cluster Doc AI - Sistema Distribuido de Procesamiento de Documentos

Este proyecto es una plataforma distribuida diseñada para procesar, analizar y clasificar documentos PDF utilizando Modelos de Lenguaje Grande (LLMs) ejecutados localmente con **Ollama**. Fue creado como un sistema distribuido donde diferentes "máquinas" (nodos) interactúan en cascada para repartir la carga computacional.

## 🏗 Arquitectura del Sistema

El sistema está dividido en 4 nodos (microservicios):

1. **Frontend / Gateway (Puerto 8000)**
   - Interfaz web moderna (Glassmorphism).
   - Control de autenticación de usuarios (JWT). Existen 2 roles: **Subidor** (máx. 10 usuarios) y **Visualizador** (ilimitado).
   - Recibe el PDF, lo guarda y notifica a la Máquina 1.
   
2. **Máquina 1: El Lector Profundo (Puerto 8001)**
   - Extrae el texto del PDF utilizando PyMuPDF.
   - Utiliza el modelo `llama3.1:8b` para limpiar la estructura, corregir el contexto y generar una versión coherente del texto.
   - Envía el texto limpio a la Máquina 2.

3. **Máquina 2: El Extractor Analítico (Puerto 8002)**
   - Utiliza el modelo `llama3.2:3b` (o qwen2.5:3b).
   - Actúa como analista de datos para extraer los 5 puntos más importantes y las palabras clave.
   - Envía esta lista de viñetas a la Máquina 3.

4. **Máquina 3: El Sintetizador y Juez (Puerto 8003)**
   - Utiliza modelos rápidos como `phi3` o `gemma2:2b`.
   - Genera un resumen ejecutivo (máx. 3 líneas).
   - Asigna una prioridad al documento en función de su urgencia: **ROJO** (Alta), **ÁMBAR** (Media) o **VERDE** (Baja).
   - Actualiza la base de datos de MongoDB con los resultados finales.

## 🚀 Requisitos Previos

- [Docker](https://www.docker.com/) y Docker Compose.
- [Python 3.8+](https://www.python.org/).
- [Ollama](https://ollama.com/) instalado en el host local.

Debes descargar los modelos de IA que el sistema utilizará. Abre una terminal y ejecuta:

```bash
ollama pull llama3.1:8b
ollama pull llama3.2:3b
ollama pull phi3
```

## 🛠 Instalación y Ejecución Local

1. **Clonar el repositorio**
   ```bash
   git clone <URL_DE_TU_REPOSITORIO>
   cd Cluster_U2
   ```

2. **Levantar la Base de Datos**
   El proyecto utiliza MongoDB para almacenar el estado de los documentos y los usuarios, y Mongo Express para visualizar la BD.
   ```bash
   docker-compose up -d
   ```
   *Puedes ver la base de datos en [http://localhost:8081](http://localhost:8081).*

3. **Iniciar los Nodos del Clúster**
   El proyecto incluye un script en Bash para levantar automáticamente todos los servicios de FastAPI.
   ```bash
   chmod +x run_cluster.sh
   ./run_cluster.sh
   ```

4. **Usar la Plataforma**
   - Entra a **[http://localhost:8000](http://localhost:8000)** en tu navegador.
   - Regístrate creando una cuenta (Asegúrate de elegir el rol de **Subidor** si quieres hacer pruebas subiendo archivos).
   - Inicia sesión y arrastra un documento PDF para ver la magia de la IA en acción.

## 🌐 Despliegue en Red (Múltiples Computadoras)

Para cumplir estrictamente con el concepto de "Sistema Distribuido" en diferentes computadoras físicas, haz lo siguiente:
1. Pasa la carpeta `machine1` a la PC 1, `machine2` a la PC 2, etc.
2. Abre el archivo `main.py` de cada máquina y modifica las variables de entorno de conexión (`OLLAMA_URL`, `MACHINE_2_URL`, `MACHINE_3_URL`) usando la dirección IPv4 de la computadora correspondiente en tu red local (LAN) en lugar de `localhost`.
3. Ejecuta `uvicorn main:app --host 0.0.0.0 --port <puerto>` dentro de la carpeta correspondiente en cada PC.

## 💻 Tecnologías Utilizadas

- **Backend**: FastAPI, Python
- **IA**: Ollama (Llama 3.1, Llama 3.2, Phi-3)
- **Base de Datos**: MongoDB, Docker
- **Frontend**: HTML5, Vanilla CSS, Vanilla JS
- **Seguridad**: JWT (JSON Web Tokens), Passlib (Bcrypt)
