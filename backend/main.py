from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import bcrypt
import jwt
from typing import Optional, List

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Notes API", version="1.0.0")
security = HTTPBearer()

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: str
    content: str
    updated_at: str  # For collision detection

class Note(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    created_at: str
    updated_at: str

class User(BaseModel):
    id: int
    username: str

class ConflictError(BaseModel):
    error: str
    message: str
    current_note: Note
    your_changes: dict

# Database functions
def get_db_connection():
    conn = sqlite3.connect('notes.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            content TEXT,
            owner_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        )
    ''')
    
    # Create trigger to auto-update updated_at timestamp
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_notes_timestamp 
        AFTER UPDATE ON notes
        FOR EACH ROW
        BEGIN
            UPDATE notes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    conn.commit()
    conn.close()

# Auth utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Initialize database
init_db()

# Auth Routes
@app.post("/auth/register")
async def register(user: UserCreate):
    conn = get_db_connection()
    
    try:
        # Check if user exists
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (user.username,)
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user
        hashed_pw = hash_password(user.password)
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hashed_pw)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        return {"id": user_id, "username": user.username, "message": "User created"}
    
    finally:
        conn.close()

@app.post("/auth/login")
async def login(user: UserLogin):
    conn = get_db_connection()
    
    try:
        db_user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (user.username,)
        ).fetchone()
        
        if not db_user or not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = create_access_token({"user_id": db_user['id']})
        return {"access_token": access_token, "token_type": "bearer"}
    
    finally:
        conn.close()

# Notes Routes
@app.post("/notes", response_model=Note)
async def create_note(note: NoteCreate, current_user: int = Depends(get_current_user)):
    conn = get_db_connection()
    
    try:
        cursor = conn.execute(
            "INSERT INTO notes (title, content, owner_id) VALUES (?, ?, ?)",
            (note.title, note.content, current_user)
        )
        note_id = cursor.lastrowid
        conn.commit()
        
        # Fetch created note with timestamps
        created_note = conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        
        return Note(**dict(created_note))
    
    finally:
        conn.close()

@app.get("/notes", response_model=List[Note])
async def get_notes(current_user: int = Depends(get_current_user)):
    conn = get_db_connection()
    
    try:
        notes = conn.execute(
            "SELECT * FROM notes WHERE owner_id = ? ORDER BY updated_at DESC",
            (current_user,)
        ).fetchall()
        
        return [Note(**dict(note)) for note in notes]
    
    finally:
        conn.close()

@app.get("/notes/{note_id}", response_model=Note)
async def get_note(note_id: int, current_user: int = Depends(get_current_user)):
    conn = get_db_connection()
    
    try:
        note = conn.execute(
            "SELECT * FROM notes WHERE id = ? AND owner_id = ?",
            (note_id, current_user)
        ).fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return Note(**dict(note))
    
    finally:
        conn.close()

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(
    note_id: int, 
    note_update: NoteUpdate, 
    current_user: int = Depends(get_current_user)
):
    conn = get_db_connection()
    
    try:
        # Get current note from database
        current_note = conn.execute(
            "SELECT * FROM notes WHERE id = ? AND owner_id = ?",
            (note_id, current_user)
        ).fetchone()
        
        if not current_note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # COLLISION DETECTION: Check timestamps
        db_updated_at = current_note['updated_at']
        client_updated_at = note_update.updated_at
        
        print(f"DB timestamp: {db_updated_at}, Client timestamp: {client_updated_at}")
        
        if db_updated_at != client_updated_at:
            # Collision detected - return 409 Conflict
            current_note_obj = Note(**dict(current_note))
            conflict_data = {
                "error": "conflict",
                "message": "Note has been updated by another user. Please resolve conflicts.",
                "current_note": current_note_obj.dict(),
                "your_changes": {
                    "title": note_update.title,
                    "content": note_update.content
                }
            }
            raise HTTPException(status_code=409, detail=conflict_data)
        
        # No collision - proceed with update
        conn.execute(
            "UPDATE notes SET title = ?, content = ? WHERE id = ? AND owner_id = ?",
            (note_update.title, note_update.content, note_id, current_user)
        )
        conn.commit()
        
        # Fetch updated note (updated_at will be automatically updated by trigger)
        updated_note = conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        
        return Note(**dict(updated_note))
    
    finally:
        conn.close()

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, current_user: int = Depends(get_current_user)):
    conn = get_db_connection()
    
    try:
        # Check if note exists and belongs to user
        note = conn.execute(
            "SELECT id FROM notes WHERE id = ? AND owner_id = ?",
            (note_id, current_user)
        ).fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        
        # Delete note
        conn.execute(
            "DELETE FROM notes WHERE id = ? AND owner_id = ?",
            (note_id, current_user)
        )
        conn.commit()
        
        return {"message": "Note deleted successfully"}
    
    finally:
        conn.close()

@app.get("/")
async def root():
    return {"message": "Notes API is running! Visit /docs for API documentation"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)