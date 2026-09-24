from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


config = ConfigDict(protected_namespaces=())


class ChatMessage(BaseModel):
    model_config = config

    role: str = Field(..., description='User or assistant role')
    content: str = Field(..., description='Message content')


class ChatRequest(BaseModel):
    model_config = config

    question: str = Field(..., min_length=1, description='The user question to answer')
    session_id: str | None = Field(default=None, description='Conversation session ID')
    history: list[ChatMessage] = Field(default_factory=list, description='Optional prior messages')


class ConversationCreateRequest(BaseModel):
    model_config = config

    title: str | None = Field(default=None, description='Optional conversation title')


class ConversationResponse(BaseModel):
    model_config = config

    id: str
    user_id: int
    title: str
    created_at: str
    updated_at: str


class SourceDocument(BaseModel):
    model_config = config

    id: str
    title: str
    source: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    model_config = config

    answer: str
    session_id: str | None = None
    sources: list[SourceDocument] = Field(default_factory=list)
    status: str = 'ok'
    model_used: str = 'local-slm'
    warnings: list[str] = Field(default_factory=list)


class DocumentInfo(BaseModel):
    model_config = config

    id: str
    title: str
    category: str
    source: str
    content: str


class RegisterRequest(BaseModel):
    model_config = config

    full_name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = config

    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    created_at: str
    updated_at: str
