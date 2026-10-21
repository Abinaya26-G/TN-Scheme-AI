
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
import sqlite3
from datetime import datetime, timedelta, timezone
import re
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from auth_db import init_db, get_connection
from rag_pipeline import search_schemes

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY missing in .env")

client = genai.Client(api_key=api_key)

MODEL_NAME = "gemini-3.5-flash-lite"

app = FastAPI(title="Tamil Nadu Scheme AI Assistant")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY missing in .env")

password_hash = PasswordHash.recommended()
security = HTTPBearer()

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

init_db()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


@app.post("/auth/register", status_code=201)
def register(request: RegisterRequest):
    name = request.name.strip()
    email = request.email.strip().lower()

    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter your name."
        )

    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
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


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


@app.post("/auth/login")
def login(request: LoginRequest):
    email = request.email.strip().lower()

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
        request.password, user["password_hash"]
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
            "exp": now + timedelta(minutes=60)
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
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


@app.get("/")
def home():
    return {
        "message": "Welcome to Tamil Nadu Government Scheme AI Assistant!"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/chat")
def chat(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    # Step 1: Retrieve relevant chunks from ChromaDB
    results = search_schemes(question, top_k=3)

    if not results:
        return {
            "question": question,
            "answer": "No relevant information was found in the indexed documents.",
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
        print("Gemini API error:", type(error).__name__, str(error))
        raise HTTPException(
            status_code=502,
            detail="AI service is temporarily unavailable. Please retry."
        )
