# Explicación del Flujo y Arquitectura del Clúster

Este documento fue creado para ayudarte a comprender a fondo cómo funciona tu proyecto de **Cluster Doc AI**. Aquí encontrarás la teoría y el flujo de datos paso a paso para que puedas explicarlo y defenderlo en tu clase de Sistemas Distribuidos.

---

## 1. El Concepto Fundamental: Pipeline Distribuido (Cascada)

A diferencia de los clústeres tradicionales que usan balanceo de carga (donde varias máquinas idénticas hacen el mismo trabajo al mismo tiempo), este proyecto implementa una arquitectura **Pipeline (o en Cascada)**.

Imagina una fábrica de ensamblaje de autos:
- El trabajador 1 pone el motor.
- El trabajador 2 pone las llantas.
- El trabajador 3 pinta el auto.

Ningún trabajador hace el auto completo por sí solo. En nuestro sistema, **ninguna máquina lee el PDF y hace el resumen completo**. Hemos fragmentado el trabajo para que cada nodo (computadora) utilice un modelo de IA especializado en una tarea específica. Esto es altamente eficiente porque permite usar modelos pequeños y rápidos para tareas sencillas, y reservar el modelo grande y pesado solo para la tarea más difícil.

---

## 2. El Flujo de Datos (Paso a Paso)

Cuando un usuario sube un PDF a la plataforma, ocurre la siguiente cadena de eventos a través de la red:

### Fase 0: El Servidor Principal (Gateway / Frontend)
1.  **Autenticación y Subida:** El usuario inicia sesión. El sistema verifica mediante un token (JWT) que el usuario sea de tipo `uploader`. Si es un `viewer`, le bloquea la opción de subir archivos.
2.  **Registro Inicial:** El servidor guarda el archivo PDF físico en la carpeta `uploads/` y crea un documento en la base de datos (MongoDB) con el estado **"Procesando"**.
3.  **Llamada a la Cascada:** Inmediatamente después, el servidor envía el archivo físico por red mediante una petición POST a la **Máquina 1** y se olvida del asunto, dejando que el clúster haga su magia en segundo plano.

### Fase 1: Máquina 1 (El Lector Profundo)
*   **Recepción:** Recibe el archivo PDF.
*   **Extracción en Crudo:** Usa la librería de Python `PyMuPDF` para sacar todo el texto del documento. Sin embargo, el texto de un PDF suele venir roto, sin espacios o desordenado.
*   **Procesamiento de IA:** Le envía este texto roto a **Ollama** usando el modelo pesado `llama3.1:8b`. El modelo actúa como un corrector de estilo, analiza el contexto y devuelve un texto limpio, con sentido y estructura coherente.
*   **Envío:** Toma este "Texto Limpio" y lo manda por red (HTTP POST) a la **Máquina 2**.

### Fase 2: Máquina 2 (El Extractor Analítico)
*   **Recepción:** Recibe el "Texto Limpio".
*   **Procesamiento de IA:** Usa a Ollama con el modelo analítico `llama3.2:3b`. Su única instrucción (prompt) es leer el texto y extraer **solo los 5 puntos más importantes** en formato de viñetas.
*   **Envío:** Toma esa lista corta de puntos clave y la manda por red a la **Máquina 3**.

### Fase 3: Máquina 3 (El Sintetizador y Juez)
*   **Recepción:** Recibe la lista de 5 puntos clave.
*   **Procesamiento de IA (Doble):**
    1.  Llama a Ollama con el modelo rápido `phi3` y le pide que redacte un pequeño resumen ejecutivo de 3 líneas basado en esos puntos.
    2.  Vuelve a llamar a `phi3` pidiéndole que lea esos puntos y decida una prioridad estricta: **ROJO, ÁMBAR o VERDE**.
*   **Finalización (Cierre del ciclo):** La Máquina 3 se conecta a la Base de Datos (MongoDB) alojada en el Servidor Principal y **actualiza el registro** del documento. Le asigna el resumen, el color obtenido y cambia su estado a **"Completado"**.

---

## 3. Manejo de Usuarios y Roles (Restricciones)

El sistema de autenticación está diseñado con dos roles:
-   **Uploader (Subidor):** Personas autorizadas para alterar el estado del sistema. Tienen permisos para: Visualizar, Subir PDFs, Descargar PDFs y Eliminar PDFs.
-   **Viewer (Visualizador):** Personas que solo consumen los datos. Tienen permisos para: Visualizar y Descargar PDFs. No pueden ver el botón de Subir ni el de Eliminar.

**La Regla de los 10 Usuarios:**
Dentro del código del servidor (`frontend/main.py`), en la ruta `/register`, existe una regla de negocio programada. Antes de registrar a un usuario nuevo con rol `uploader`, el servidor cuenta cuántos `uploaders` existen ya en la base de datos de MongoDB. **Si el conteo es igual o mayor a 10, la base de datos rechaza el registro lanzando un error 400**, cumpliendo estrictamente con el requerimiento del proyecto. Los usuarios `viewer` ignoran esta regla y pueden registrarse de forma indefinida y masiva.

---

## 4. Puntos Clave para tu Exposición

Si tu profesor te hace preguntas difíciles, aquí tienes las respuestas:

*   **¿Por qué es un sistema distribuido si no hay balanceo de carga?**
    Porque el procesamiento de los datos no reside en un solo núcleo o máquina. Estamos aplicando una **arquitectura orientada a eventos/servicios**, donde diferentes nodos distribuidos geográficamente (o en red local) colaboran pasándose mensajes (vía HTTP) para lograr completar un trabajo complejo que saturaría a una sola computadora.
*   **¿Por qué usar 3 modelos de Inteligencia Artificial distintos?**
    Por optimización de recursos. Usar el modelo gigante de `llama3.1:8b` para una tarea sencilla como decir "ROJO, ÁMBAR o VERDE" es un desperdicio enorme de RAM y Tiempo. En su lugar, el clúster reserva el modelo pesado para la tarea de alta comprensión de lectura, y delega las tareas analíticas y de etiquetado a modelos ágiles y diminutos (`llama3.2:3b` y `phi3`), haciendo que la cadena completa sea más veloz.
