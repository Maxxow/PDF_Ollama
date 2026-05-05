import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Máquina 2: El Extractor Analítico")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MACHINE_3_URL = os.getenv("MACHINE_3_URL", "http://127.0.0.1:8003/process")

class ProcessRequest(BaseModel):
    document_id: str
    clean_text: str

@app.post("/process")
async def process_document(req: ProcessRequest):
    print(f"======> MÁQUINA 2: Recibido texto limpio. Llamando a llama3.2:3b para resumir viñetas...")
    
    # 1. Call Ollama (llama3.2:3b)
    prompt = f"Actúa como un analista de datos. Extrae los 5 puntos más importantes y las palabras clave de este texto. Devuelve únicamente una lista de viñetas. Texto:\n\n{req.clean_text}"
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.2:3b",  # Using llama3.2:3b as suggested
            "prompt": prompt,
            "stream": False
        }, timeout=600)
        response.raise_for_status()
        key_points = response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error Ollama M2: {e}")
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama on Machine 2: {e}")

    # 2. Send to Machine 3
    print(f"======> MÁQUINA 2: Puntos extraídos. Enviando a Máquina 3...")
    try:
        payload = {
            "document_id": req.document_id,
            "key_points": key_points
        }
        m3_response = requests.post(MACHINE_3_URL, json=payload, timeout=600)
        m3_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            err_msg += f" | M3 dijo: {e.response.text}"
        raise HTTPException(status_code=500, detail=f"Error forwarding to Machine 3: {err_msg}")

    return {"message": "Extracted key points and sent to Machine 3", "machine3_response": m3_response.json()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
