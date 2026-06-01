"""
app/api/v1/endpoints/chat.py
Chat completion endpoint — routes to OpenAI or Gemini based on the model field.
"""

from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.core.config import settings

router = APIRouter()


def _is_gemini(model: str) -> bool:
    return model.startswith("gemini")


async def _call_openai(req: ChatRequest) -> str:
    """Call OpenAI Chat Completions API."""
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=req.model,
        messages=[{"role": m.role, "content": m.content} for m in req.messages],
        temperature=req.temperature,
        max_tokens=req.max_tokens,
    )
    return response.choices[0].message.content or ""


async def _call_gemini(req: ChatRequest) -> str:
    """Call Google Gemini GenerativeAI API."""
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key is not configured.")

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(req.model)

    # Build Gemini history from messages (exclude system prompt — pass as first user turn)
    history = []
    system_prompt = None
    for msg in req.messages[:-1]:
        if msg.role == "system":
            system_prompt = msg.content
            continue
        role = "user" if msg.role == "user" else "model"
        history.append({"role": role, "parts": [msg.content]})

    # Last message is always the new user query
    last_message = req.messages[-1].content
    if system_prompt:
        last_message = f"{system_prompt}\n\n{last_message}"

    chat = model.start_chat(history=history)
    response = chat.send_message(last_message)
    return response.text


@router.post("/chat", response_model=ChatResponse, summary="Chat Completion")
async def chat_completion(req: ChatRequest):
    """
    Send a chat message and receive a response from either OpenAI or Gemini.

    - **model**: Choose from `gpt-4o`, `gpt-4o-mini`, `gemini-1.5-pro`, `gemini-1.5-flash`, or `gemini-2.0-flash`
    - **messages**: Array of conversation messages
    """
    try:
        if _is_gemini(req.model):
            content = await _call_gemini(req)
            provider = "gemini"
        else:
            content = await _call_openai(req)
            provider = "openai"

        return ChatResponse(content=content, model=req.model, provider=provider)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


@router.get("/models", summary="Available Models")
async def list_models():
    """Returns the list of available AI models and their providers."""
    return {
        "models": [
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google", "description": "Fastest Gemini model"},
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "google", "description": "Most capable Gemini model"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "google", "description": "Balanced speed & capability"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai", "description": "OpenAI's most capable model"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai", "description": "Fast and affordable GPT-4o"},
        ]
    }
