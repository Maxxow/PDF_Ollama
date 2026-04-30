import os
import requests
import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel

app = FastAPI(title="Máquina 1: El Lector Profundo")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MACHINE_2_URL = os.getenv("MACHINE_2_URL", "http://localhost:8002/process")

class ProcessRequest(BaseModel):
    filename: str
    document_id: str

@app.post("/upload")
async def upload_document(file: UploadFile = File(...), document_id: str = Form(...)):
    # 1. Read PDF
    try:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")
        raw_text = ""
        for page in doc:
            raw_text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {e}")

    # 2. Call Ollama (llama3.1:8b)
    prompt = f"Analiza a profundidad este documento, corrige la estructura y genera una versión limpia y coherente del texto:\n\n[TEXTO CRUDO]\n{raw_text}"
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json={
            "model": "llama3.1:8b",
            "prompt": prompt,
            "stream": False
        }, timeout=300) # Give it 5 minutes as it's a large model
        response.raise_for_status()
        clean_text = response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to Ollama on Machine 1: {e}")

    # 3. Send to Machine 2
    try:
        payload = {
            "document_id": document_id,
            "clean_text": clean_text
        }
        m2_response = requests.post(MACHINE_2_URL, json=payload, timeout=30)
        m2_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding to Machine 2: {e}")

    return {"message": "Document processed by Machine 1 and sent to Machine 2.", "machine2_response": m2_response.json()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
