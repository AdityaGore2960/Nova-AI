"""
app/models/chat.py
Pydantic schemas for chat request/response.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Literal["gpt-4o", "gpt-4o-mini", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-2.0-flash"] = Field(
        default="gemini-2.0-flash",
        description="The AI model to use for this chat completion.",
    )
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2048, ge=1, le=8192)


class ChatResponse(BaseModel):
    content: str
    model: str
    provider: Literal["openai", "gemini"]
