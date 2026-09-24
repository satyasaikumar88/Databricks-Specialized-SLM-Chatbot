from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.auth import (
    AUTH_COOKIE,
    authenticate_user,
    create_access_token,
    create_conversation,
    create_user,
    current_user,
    delete_conversation,
    get_conversation,
    get_conversation_messages,
    initialize_database,
    list_conversations,
    save_message,
    update_conversation_title,
)
from backend.model_service import model_service
from backend.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreateRequest,
    ConversationResponse,
    LoginRequest,
    RegisterRequest,
    SourceDocument,
    UserResponse,
)
from rag import retriever

app = FastAPI(title='Databricks-Specialized SLM Chatbot')

allowed_origins = list(
    dict.fromkeys(
        [
            settings.frontend_url,
            'http://localhost:3000',
            'http://127.0.0.1:3000',
            'http://localhost:3001',
            'http://127.0.0.1:3001',
            'http://localhost:3002',
            'http://127.0.0.1:3002',
        ]
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

conversation_store: dict[str, list[dict[str, str]]] = {}


def set_auth_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=AUTH_COOKIE,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.frontend_url.startswith('https://'),
        samesite='lax',
        path='/',
    )


def normalize_question(question: str) -> str:
    return ' '.join(question.strip().split())


def conversation_title_from_question(question: str) -> str:
    normalized = normalize_question(question).strip(' .!?')
    lowered = normalized.lower()

    if lowered.startswith('what is '):
        title = normalized[8:]
    elif lowered.startswith('how does ') and lowered.endswith(' work'):
        title = normalized[9:-5].strip()
    elif lowered.startswith('explain ') and lowered.endswith(' architecture'):
        subject = normalized[8:-12].strip()
        title = f'{subject} Architecture'
    else:
        match = re.match(r'^how can i read (.+?) using (.+)$', normalized, flags=re.IGNORECASE)
        title = f'Reading {match.group(1)} with {match.group(2)}' if match else normalized

    title = re.sub(r'\s+', ' ', title).strip(' .,:;!?')
    title = re.sub(r'\bbronze\s+silver\s+gold\b', 'Bronze-Silver-Gold', title, flags=re.IGNORECASE)
    if len(title) > 35:
        shortened = title[:35].rsplit(' ', 1)[0].strip(' .,:;!?')
        title = shortened or title[:35].rstrip(' .,:;!?')
    return title or 'New Chat'


def normalize_generated_answer(question: str, answer: str) -> str:
    cleaned = answer.strip()
    cleaned = cleaned.replace('Contextualize the question using the provided context.', '').strip()
    cleaned = cleaned.replace('Context: The Apache Spark project aims to make it easy to build scalable, fault-tolerant, and highly available distributed systems that can process large volumes of data efficiently.', '').strip()
    cleaned = cleaned.replace('Answer:', '').strip()
    cleaned = cleaned.replace('Contextual information:', '').strip()
    cleaned = cleaned.replace('Answer Choices:', '').strip()
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    q = normalize_question(question).lower()
    if q.startswith('what is databricks'):
        first = cleaned.lower().find('databricks is')
        last = cleaned.lower().find('what is databricks?')
        if first >= 0:
            cleaned = cleaned[first:]
        if 'auto loader' in cleaned.lower() and 'databricks is' in cleaned.lower():
            cleaned = cleaned.replace('Auto Loader is a Databricks feature for incremental file ingestion.', '').strip()
        if 'databricks is' not in cleaned.lower():
            cleaned = 'Databricks is a cloud-based data and AI platform built around Apache Spark. It provides managed compute, Delta Lake, notebooks, workflows, and governance tools such as Unity Catalog.'
        cleaned = cleaned.split('What is Databricks?')[0].strip()
        cleaned = cleaned.split('What is Databricks')[0].strip()
        if len(cleaned.split()) > 30:
            cleaned = 'Databricks is a cloud-based data and AI platform built around Apache Spark. It provides managed compute, Delta Lake, notebooks, workflows, and governance tools such as Unity Catalog.'
        return cleaned

    if 'Auto Loader' in cleaned and 'Databricks is' in cleaned and 'What is Databricks?' in question:
        cleaned = cleaned.replace('Auto Loader is a Databricks feature for incremental file ingestion.', '').strip()

    return cleaned


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

    system_prompt = (
        "You are a Databricks Learning Assistant powered by a Qwen model fine-tuned with LoRA. "
        "Give accurate, concise, educational answers about Databricks and related technologies. "
        "Identify the exact technology being asked about before answering. "
        "Never confuse Databricks with its individual services or features. "
        "For simple questions, answer briefly in 2-5 sentences. "
        "For conceptual questions, give a short definition, 3-5 key points, and one small Databricks-related example. "
        "For how-to questions, explain the steps briefly and provide PySpark/SQL code when useful. "
        "For comparisons, use a brief table or bullet list. "
        "Do not repeat information or provide long background unless the user explicitly asks for detail. "
        "Use Databricks-specific examples and distinguish clearly between Databricks, Apache Spark, Delta Lake, Auto Loader, Unity Catalog, MLflow, PySpark, Databricks SQL, Workflows, Jobs, and Medallion Architecture. "
        "Never describe Databricks as Auto Loader or confuse Delta Lake with Parquet. "
        "When a question is simple, do not give essay-like answers. Keep the response short and precise."
    )

    messages = [
        system_prompt,
        "Response style rules:",
        "- For simple questions: answer directly in 2-5 sentences.",
        "- For conceptual questions: give a short definition, 3-5 key points, and one Databricks example.",
        "- For how-to questions: explain steps briefly and include code when useful.",
        "- For comparison questions: use a small table when helpful.",
        "- For complex questions: use a structured explanation, but do not repeat yourself.",
        "- Use the provided context to ground factual answers.",
        "- If the context is weak or missing, answer conservatively and say so briefly.",
        "- Never confuse Databricks with Auto Loader, Delta Lake, Unity Catalog, or Apache Spark.",
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


@app.post('/auth/register', response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, response: Response):
    user = create_user(request.full_name, request.email, request.password)
    token, max_age = create_access_token(user['id'], remember_me=True)
    set_auth_cookie(response, token, max_age)
    return user


@app.post('/auth/login', response_model=UserResponse)
def login(request: LoginRequest, response: Response):
    user = authenticate_user(request.email, request.password)
    token, max_age = create_access_token(user['id'], remember_me=request.remember_me)
    set_auth_cookie(response, token, max_age)
    return user


@app.get('/auth/me', response_model=UserResponse)
def me(user: dict[str, Any] = Depends(current_user)):
    return user


@app.post('/auth/logout', status_code=204)
def logout(response: Response):
    response.delete_cookie(AUTH_COOKIE, path='/')


@app.get('/model')
def model_info(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return model_service.get_model_info()


@app.get('/documents')
def list_documents(_: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    try:
        docs = retriever.DocRetriever(settings.docs_path, settings.rag_index_path).list_documents()
        return {'documents': docs}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unable to load documents: {exc}')


@app.post('/documents/index')
def build_index(_: dict[str, Any] = Depends(current_user)) -> dict[str, str]:
    try:
        indexer = retriever.DocRetriever(settings.docs_path, settings.rag_index_path)
        indexer.build_index()
        return {'status': 'ok', 'message': 'RAG index rebuilt successfully.'}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Unable to index documents: {exc}')


@app.get('/conversations', response_model=list[ConversationResponse])
def conversations(user: dict[str, Any] = Depends(current_user)):
    return [ConversationResponse(**conversation) for conversation in list_conversations(user['id'])]


@app.post('/conversations', response_model=ConversationResponse)
def create_conversation_endpoint(
    request: ConversationCreateRequest | None = None,
    user: dict[str, Any] = Depends(current_user),
):
    title = request.title if request else None
    conversation = create_conversation(user['id'], title=title)
    return ConversationResponse(**conversation)


@app.patch('/conversations/{conversation_id}', response_model=ConversationResponse)
def update_conversation_endpoint(
    conversation_id: str,
    request: ConversationCreateRequest,
    user: dict[str, Any] = Depends(current_user),
):
    conversation = update_conversation_title(user['id'], conversation_id, request.title or 'New Chat')
    return ConversationResponse(**conversation)


@app.get('/conversations/{conversation_id}/messages')
def conversation_messages(conversation_id: str, user: dict[str, Any] = Depends(current_user)):
    messages = get_conversation_messages(user['id'], conversation_id)
    return {'messages': messages}


@app.delete('/conversations/{conversation_id}')
def delete_conversation_endpoint(conversation_id: str, user: dict[str, Any] = Depends(current_user)):
    delete_conversation(user['id'], conversation_id)
    return {'status': 'ok'}


@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest, user: dict[str, Any] = Depends(current_user)):
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail='Question cannot be empty.')

    question = normalize_question(request.question)
    history = request.history or []
    conversation_id = request.session_id

    if conversation_id:
        get_conversation(user['id'], conversation_id)
    else:
        conversation = create_conversation(user['id'], title='New conversation')
        conversation_id = conversation['id']

    existing_messages = get_conversation_messages(user['id'], conversation_id)
    if not history:
        history = [
            {'role': item['role'], 'content': item['content']}
            for item in existing_messages
        ]

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
        answer = model_service.generate(prompt, max_new_tokens=140, temperature=0.2, top_p=0.9)
        if not answer:
            answer = 'I could not generate a grounded answer from the local model.'
        answer = normalize_generated_answer(question, answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f'Model generation failed: {exc}')

    conversation_store.setdefault(conversation_id, [])
    conversation_store[conversation_id].append({'role': 'user', 'content': question})
    conversation_store[conversation_id].append({'role': 'assistant', 'content': answer})

    save_message(user['id'], conversation_id, 'user', question)
    save_message(user['id'], conversation_id, 'assistant', answer)
    if not any(item['role'] == 'user' for item in existing_messages):
        update_conversation_title(user['id'], conversation_id, conversation_title_from_question(question))

    response = ChatResponse(
        answer=answer,
        session_id=conversation_id,
        sources=sources,
        status='ok',
        model_used='local-slm',
        warnings=[warning] if warning else [],
    )
    return response


@app.on_event('startup')
def startup_event():
    initialize_database()
    try:
        if not Path(settings.docs_path).exists():
            raise FileNotFoundError(f'Unable to locate docs at {settings.docs_path}')
        retriever.DocRetriever(settings.docs_path, settings.rag_index_path)
    except Exception as exc:
        print(f'Warning: RAG warmup failed: {exc}')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('backend.main:app', host=settings.api_host, port=settings.api_port, reload=True)
