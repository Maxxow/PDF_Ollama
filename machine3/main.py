import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

app = FastAPI(title="Máquina 3: El Sintetizador y Juez")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")

client = MongoClient(MONGO_URI)
db = client["document_system"]
docs_collection = db["documents"]

class ProcessRequest(BaseModel):
    document_id: str
    key_points: str

@app.post("/process")
async def process_document(req: ProcessRequest):
    print(f"======> MÁQUINA 3: Recibidas las viñetas. Llamando a phi3 para resumen y color...")
    
    # 1. Call A: Resumen Final
    prompt_a = f"Redacta un resumen final de máximo 3 líneas usando estos puntos:\n\n{req.key_points}"
    try:
        res_a = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "phi3",  # Using phi3 as suggested
            "prompt": prompt_a,
            "stream": False
        }, timeout=600)
        res_a.raise_for_status()
        summary = res_a.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        print(f"Error Llamada A M3: {e}")
        raise HTTPException(status_code=500, detail=f"Error en Llamada A: {e}")

    # 2. Call B: Evaluación de Urgencia
    prompt_b = f"Evalúa la urgencia de estos puntos. Responde estrictamente con una sola palabra: ROJO, ÁMBAR o VERDE.\nPuntos:\n{req.key_points}"
    try:
        res_b = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "phi3",
            "prompt": prompt_b,
            "stream": False
        }, timeout=600)
        res_b.raise_for_status()
        priority_raw = res_b.json().get("response", "").strip().upper()
        
        # Clean response to ensure it's just the valid words
        if "ROJO" in priority_raw:
            priority = "ROJO"
        elif "VERDE" in priority_raw:
            priority = "VERDE"
        elif "AMBAR" in priority_raw or "ÁMBAR" in priority_raw:
            priority = "ÁMBAR"
        else:
            priority = "VERDE" # Default if it fails
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error en Llamada B: {e}")

    # 3. Save to MongoDB
    from bson.objectid import ObjectId
    try:
        docs_collection.update_one(
            {"_id": ObjectId(req.document_id)},
            {"$set": {
                "summary": summary,
                "priority": priority,
                "status": "COMPLETED",
                "completed_at": datetime.utcnow()
            }}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating MongoDB: {e}")

    return {
        "message": "Processing complete",
        "summary": summary,
        "priority": priority
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
