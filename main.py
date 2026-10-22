
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from google import genai

from auth_db import init_db, get_connection
from rag_pipeline import search_schemes


# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not api_key:
    raise ValueError(
        "GEMINI_API_KEY is missing. Configure it in Render Environment."
    )

if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY is missing. Configure it in Render Environment."
    )

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()
security = HTTPBearer()


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Tamil Nadu Scheme AI Assistant"
)

# CORS: allow the deployed frontend and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tn-scheme-ai.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------

init_db()


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


# --------------------------------------------------
# EMAIL VALIDATION
# --------------------------------------------------

def validate_email(email: str) -> bool:
    return bool(
        re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
    )


# --------------------------------------------------
# REGISTER API
# POST /auth/register
# --------------------------------------------------

@app.post("/auth/register", status_code=201)
def register(request: RegisterRequest):
    name = request.name.strip()
    email = request.email.strip().lower()

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter your name."
        )

    if not validate_email(email):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email."
        )

    hashed_password = password_hash.hash(request.password)

    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )
            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Email already registered. Please login."
        )

    return {
        "message": "Registration successful!",
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }


# --------------------------------------------------
# LOGIN API
# POST /auth/login
# --------------------------------------------------

@app.post("/auth/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()

    if not validate_email(email):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email."
        )

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, name, email, password_hash
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

    if user is None or not password_hash.verify(
        request.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": str(user["id"]),
            "iat": now,
            "exp": now + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
        },
        JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Login successful!",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }


# --------------------------------------------------
# JWT AUTHENTICATION HELPER
# --------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token."
            )

    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token."
        )

    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT id, name, email
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found."
        )

    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }


# --------------------------------------------------
# HOME API
# GET /
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to Tamil Nadu Government Scheme AI Assistant!"
    }


# --------------------------------------------------
# HEALTH CHECK
# GET /health
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# CHAT API
# POST /chat
# --------------------------------------------------

@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    # Step 1: Retrieve relevant chunks from ChromaDB
    try:
        results = search_schemes(question, top_k=3)
    except Exception as error:
        print(
            "Scheme retrieval error:",
            type(error).__name__,
            str(error)
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve scheme information. Please retry."
        )

    if not results:
        return {
            "question": question,
            "answer": (
                "No relevant information was found in the indexed documents."
            ),
            "sources": []
        }

    context = "\n\n".join(
        result["text"] for result in results
    )

    sources = list(dict.fromkeys(
        result["source"] for result in results
    ))

    # Step 2: Send retrieved context to Gemini
    prompt = f"""
You are a Tamil Nadu Government Scheme AI Assistant.

Answer the user's question using ONLY the context below.

Rules:
- Do not invent scheme names, benefits, eligibility, or documents.
- If the context does not contain the answer, say so clearly.
- If the context identifies information as demo or synthetic data,
  clearly explain that it is not official government information.
- Recommend checking official government sources for confirmation.
- Give a clear and simple answer.
- Cite only sources that directly support the answer.
- Do not include unrelated scheme sources.
- If the context is insufficient, clearly say so.

Context:
{context}

User question:
{question}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        answer = response.text

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response."
            )

        return {
            "question": question,
            "answer": answer,
            "sources": sources
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Gemini API error:",
            type(error).__name__,
            str(error)
        )
        raise HTTPException(
            status_code=502,
            detail="AI service is temporarily unavailable. Please retry."
        )
