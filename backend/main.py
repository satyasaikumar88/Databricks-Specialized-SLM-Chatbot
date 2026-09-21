from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.model_service import model_service
from backend.schemas import ChatRequest, ChatResponse, SourceDocument
from rag import retriever

app = FastAPI(title='Databricks-Specialized SLM Chatbot')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

conversation_store: dict[str, list[dict[str, str]]] = {}


def normalize_question(question: str) -> str:
    return ' '.join(question.strip().split())


def build_prompt(question: str, sources: list[dict[str, Any]] | None = None, history: list[dict[str, str]] | None = None) -> str:
    context_chunks = []
    if sources:
        for src in sources:
            context_chunks.append(
                f"Document: {src.get('title', 'Databricks docs')}\n"
                f"Source: {src.get('source', '')}\n"
                f"Content: {src.get('snippet', '')}"
            )
    context = "\n\n---\n\n".join(context_chunks) if context_chunks else "No additional context available."

    messages = [
        "You are a Databricks expert assistant. Answer with Databricks-specific guidance and use the provided context when relevant.",
        f"User question: {question}",
        f"Relevant context:\n{context}",
    ]

    if history:
        messages.append('Conversation history:')
        for msg in history[-6:]:
            if hasattr(msg, 'role'):
                role = msg.role
                content = msg.content
            else:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
            messages.append(f'{role}: {content}')

    return '\n\n'.join(messages)


@app.get('/health')
def health() -> dict[str, Any]:
    return {
        'status': 'ok',
        'project': settings.project_name,
        'model': settings.model_name,
        'device': getattr(model_service, 'device', 'cpu'),
    }


@app.get('/model')
def model_info() -> dict[str, Any]:
    return model_service.get_model_info()


@app.get('/documents')
def list_documents() -> dict[str, Any]:
    try:
        docs = retriever.DocRetriever(settings.docs_path, settings.rag_index_path).list_documents()
        return {'documents': docs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unable to load documents: {exc}')


@app.post('/documents/index')
def build_index() -> dict[str, str]:
    try:
        indexer = retriever.DocRetriever(settings.docs_path, settings.rag_index_path)
        indexer.build_index()
        return {'status': 'ok', 'message': 'RAG index rebuilt successfully.'}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unable to index documents: {exc}')


@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail='Question cannot be empty.')

    question = normalize_question(request.question)
    history = request.history or []
    session_id = request.session_id or hashlib.sha256(question.encode('utf-8')).hexdigest()[:12]

    try:
        doc_retriever = retriever.DocRetriever(settings.docs_path, settings.rag_index_path)
        retrieval = doc_retriever.retrieve(question, top_k=4)
    except Exception as exc:
        retrieval = []
        warning = f'RAG retrieval unavailable: {exc}'
    else:
        warning = ''

    sources = []
    for item in retrieval:
        sources.append(
            SourceDocument(
                id=item.id,
                title=item.title,
                source=item.source,
                snippet=item.snippet,
                score=item.score,
            )
        )

    try:
        context = [
            {
                'title': item.title,
                'source': item.source,
                'snippet': item.snippet,
            }
            for item in retrieval
        ]
        prompt = build_prompt(question, context, history)
        answer = model_service.generate(prompt, max_new_tokens=220, temperature=0.2)
        if not answer:
            answer = 'I could not generate a grounded answer from the local model.'
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Model generation failed: {exc}')

    conversation_store.setdefault(session_id, [])
    conversation_store[session_id].append({'role': 'user', 'content': question})
    conversation_store[session_id].append({'role': 'assistant', 'content': answer})

    response = ChatResponse(
        answer=answer,
        session_id=session_id,
        sources=sources,
        status='ok',
        model_used='local-slm',
        warnings=[warning] if warning else [],
    )
    return response


@app.on_event('startup')
def startup_event():
    try:
        if not Path(settings.docs_path).exists():
            raise FileNotFoundError(f'Unable to locate docs at {settings.docs_path}')
        retriever.DocRetriever(settings.docs_path, settings.rag_index_path)
    except Exception as exc:
        print(f'Warning: RAG warmup failed: {exc}')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('backend.main:app', host=settings.api_host, port=settings.api_port, reload=True)
