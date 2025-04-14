# api_server.py
# Minimal FastAPI server to expose RAG assistant via `/generate` and `/search` endpoints

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from retrieval_script import generate_with_gpt, embed_query, load_faiss_and_metadata, retrieve_top_k
import numpy as np
import faiss
import json
import os
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = FastAPI()

# Load indexes at startup (to avoid reloading per request)
TEXT_INDEX, TEXT_META = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata.json")
IMG_INDEX, IMG_META = load_faiss_and_metadata("/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_index_images.index", "/Users/sharvari/Downloads/CAFB_Challenge/outputs/faiss_metadata_images.json")

# ----------------------------
# Request and Response Schemas
# ----------------------------
class GenerateRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    format: Optional[str] = None  # e.g., "grant", "tweet"
    tone: Optional[str] = None    # e.g., "formal", "casual"

class SourceChunk(BaseModel):
    score: float
    source: str
    title: str
    text: str

class GenerateResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class SearchResponse(BaseModel):
    results: List[SourceChunk]

# ----------------------------
# Log queries to a file
# ----------------------------
def log_query(entry: dict, logfile: str = "query_log.jsonl"):
    with open(logfile, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ----------------------------
# /generate endpoint (RAG + GPT-4)
# ----------------------------
@app.post("/generate", response_model=GenerateResponse)
def generate_response(req: GenerateRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    query_vec = embed_query(req.query)

    # Retrieve chunks
    text_results = retrieve_top_k(TEXT_INDEX, TEXT_META, query_vec, k=req.top_k)
    image_results = retrieve_top_k(IMG_INDEX, IMG_META, query_vec, k=2)
    all_chunks = text_results + image_results

    extra_prompt = ""
    if req.format:
        extra_prompt += f" Format: {req.format}."
    if req.tone:
        extra_prompt += f" Tone: {req.tone}."

    context = "\n\n".join([r["text"] for r in all_chunks])[:3000]
    prompt = (
        f"You are a helpful assistant for the Capital Area Food Bank.\n"
        f"Based on the following retrieved information, write a clear and concise answer to the user's query."
        f"{extra_prompt}\n"
        f"\n---\n{context}\n---\n\nUser question: {req.query}\n\nAnswer:"
    )

    # Determine system prompt based on content format
    if req.format == "grant":
        system_prompt = "You are a nonprofit grant writer. Write a persuasive funding paragraph."
    elif req.format == "blog_post":
        system_prompt = "You are a nonprofit blog writer. Write an engaging, informative blog post."
    elif req.format == "social_media_post":
        system_prompt = "You are a social media specialist. Write a short, friendly post with hashtags."
    else:
        system_prompt = "You are a helpful nonprofit assistant."

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0.3,
            max_tokens=400,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPT-4 generation failed: {e}")

    # Log the query
    log_query({
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/generate",
        "query": req.query,
        "format": req.format,
        "tone": req.tone,
        "top_k": req.top_k
    })

    return GenerateResponse(
        answer=answer,
        sources=[
            SourceChunk(**chunk) for chunk in all_chunks
        ]
    )

# ----------------------------
# /search endpoint (retrieval only)
# ----------------------------
@app.post("/search", response_model=SearchResponse)
def search_chunks(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    query_vec = embed_query(req.query)

    text_results = retrieve_top_k(TEXT_INDEX, TEXT_META, query_vec, k=req.top_k)
    image_results = retrieve_top_k(IMG_INDEX, IMG_META, query_vec, k=2)
    all_results = text_results + image_results

    # Log the query
    log_query({
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint": "/search",
        "query": req.query,
        "top_k": req.top_k
    })

    return SearchResponse(results=[SourceChunk(**r) for r in all_results])
