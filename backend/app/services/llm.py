"""LLM service — model routing for Gemini Flash + optional external reasoning model."""

from __future__ import annotations
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings
import httpx
import logging

logger = logging.getLogger(__name__)


def extract_text_content(response) -> str:
    """
    Extract text content from a LangChain Gemini response.

    Gemini 3+ models with thinking enabled return response.content as a list
    of content blocks (thinking blocks + text blocks) rather than a plain string.
    This helper safely handles both formats.
    """
    content = response.content

    # If it's already a string, return it directly
    if isinstance(content, str):
        return content

    # If it's a list (thinking model), extract text parts
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                # Text blocks have type "text", thinking blocks have type "thinking"
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") != "thinking" and "text" in block:
                    text_parts.append(block.get("text", ""))
        return "\n".join(text_parts) if text_parts else str(content)

    return str(content)


def get_flash_model(temperature: float = 0.1) -> ChatGoogleGenerativeAI:
    """Return Gemini Flash for lightweight nodes (classifier, planner, etc.)."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        max_output_tokens=2048,
    )


def get_reasoning_model(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    """
    Return the reasoning model.

    Priority:
      1. REASONING_GEMINI_API_KEY  → use a second Gemini account (different key/model)
      2. Default                   → use the primary Gemini account
    (If REASONING_MODEL_URL is set, the reasoner node calls call_external_reasoning_model instead.)
    """
    if settings.reasoning_gemini_api_key:
        model_name = settings.reasoning_gemini_model or settings.gemini_model
        logger.info(f"Reasoning: using secondary Gemini account with model '{model_name}'")
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.reasoning_gemini_api_key,
            temperature=temperature,
            max_output_tokens=4096,
        )

    # Default: primary Gemini account
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
        max_output_tokens=4096,
    )


async def call_external_reasoning_model(prompt: str) -> str:
    """
    Call an OpenAI-compatible external endpoint (fine-tuned model, Vertex AI, etc.).

    Returns the model's text response.
    """
    if not settings.reasoning_model_url:
        raise ValueError("REASONING_MODEL_URL is not configured")

    headers = {"Content-Type": "application/json"}
    if settings.reasoning_model_api_key:
        headers["Authorization"] = f"Bearer {settings.reasoning_model_api_key}"

    payload = {
        "model": "legal-reasoning",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    logger.info(f"Reasoning: calling external endpoint {settings.reasoning_model_url}")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            settings.reasoning_model_url,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
