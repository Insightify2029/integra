"""
INTEGRA AI Module
=================
AI integration using Ollama for local inference.
"""

from .ollama_client import (
    OllamaClient,
    get_ollama_client,
    is_ollama_available,
    list_models,
    get_default_model
)

from .ai_service import (
    AIService,
    get_ai_service,
    chat,
    chat_stream,
    analyze_text,
    summarize
)

__all__ = [
    # Ollama Client
    'OllamaClient',
    'get_ollama_client',
    'is_ollama_available',
    'list_models',
    'get_default_model',
    # AI Service
    'AIService',
    'get_ai_service',
    'chat',
    'chat_stream',
    'analyze_text',
    'summarize'
]
