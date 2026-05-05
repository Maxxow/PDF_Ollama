import os
import shutil
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
import aiofiles

app = FastAPI(title="Frontend y Gateway API")

# Setup MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
client = MongoClient(MONGO_URI)
db = client["document_system"]
users_collection = db["users"]
docs_collection = db["documents"]

MACHINE_1_URL = os.getenv("MACHINE_1_URL", "http://127.0.0.1:8001/upload")

# Security
SECRET_KEY = "my_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer" # uploader or viewer

import bcrypt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except jwt.PyJWTError:
        raise credentials_exception

# --- ROUTES ---

@app.post("/register")
def register(user: UserCreate):
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if user.role == "uploader":
        uploader_count = users_collection.count_documents({"role": "uploader"})
        if uploader_count >= 10:
            raise HTTPException(status_code=400, detail="Maximum number of uploaders reached (10).")
    
    hashed_password = get_password_hash(user.password)
    users_collection.insert_one({"username": user.username, "password": hashed_password, "role": user.role})
    return {"message": "User created successfully"}

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"username": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer", "role": user["role"]}

@app.get("/api/documents")
def get_documents(current_user: dict = Depends(get_current_user)):
    docs = list(docs_collection.find().sort("created_at", -1))
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
    return docs

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="Not authorized to upload files.")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Create document record
    doc_dict = {
        "filename": file.filename,
        "uploader": current_user["username"],
        "status": "PROCESSING",
        "summary": "Procesando en el clúster...",
        "priority": "PENDIENTE",
        "created_at": datetime.utcnow()
    }
    result = docs_collection.insert_one(doc_dict)
    doc_id = str(result.inserted_id)

    # Save file locally
    os.makedirs("../uploads", exist_ok=True)
    file_path = f"../uploads/{doc_id}_{file.filename}"
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # Send to Machine 1
    # Note: Using background tasks in a real scenario is better, but here we'll spawn a thread or just rely on requests.
    # To not block the UI response, we can just trigger it. We'll use a fast request or background task.
    # We will do a fire and forget to Machine 1 (or run it in a thread).
    import threading
    def send_to_machine1(path, d_id):
        try:
            with open(path, 'rb') as f:
                res = requests.post(MACHINE_1_URL, files={"file": f}, data={"document_id": d_id}, timeout=3000)
                res.raise_for_status()
        except Exception as e:
            print(f"Error calling Machine 1: {e}")
            docs_collection.update_one({"_id": ObjectId(d_id)}, {"$set": {"status": "ERROR", "summary": f"Fallo en el pipeline: {str(e)}", "priority": "ERROR"}})

    threading.Thread(target=send_to_machine1, args=(file_path, doc_id)).start()

    return {"message": "File uploaded and sent to cluster for processing", "id": doc_id}

@app.get("/api/download/{doc_id}")
def download_file(doc_id: str, current_user: dict = Depends(get_current_user)):
    doc = docs_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    file_path = f"../uploads/{doc_id}_{doc['filename']}"
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=doc['filename'])
    raise HTTPException(status_code=404, detail="File not found on server")

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "uploader":
        raise HTTPException(status_code=403, detail="Not authorized to delete files.")
    
    doc = docs_collection.find_one({"_id": ObjectId(doc_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from database
    docs_collection.delete_one({"_id": ObjectId(doc_id)})
    
    # Delete physical file if exists
    file_path = f"../uploads/{doc_id}_{doc['filename']}"
    if os.path.exists(file_path):
        os.remove(file_path)
        
    return {"message": "Document deleted successfully"}

# Mount Static Files (Frontend UI)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
