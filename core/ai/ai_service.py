"""
AI Service
==========
High-level AI service for common tasks.
Provides easy-to-use functions for chat, analysis, and summarization.
"""

from typing import Optional, List, Dict, Any, Generator, Callable
from dataclasses import dataclass, field
from datetime import datetime
import copy
import threading

from .ollama_client import get_ollama_client, OllamaClient
from .prompts import SYSTEM_PROMPTS
from core.logging import app_logger


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, str]:
        """Convert to dict for Ollama API."""
        return {"role": self.role, "content": self.content}


@dataclass
class ConversationContext:
    """Manages conversation history (thread-safe)."""
    messages: List[ChatMessage] = field(default_factory=list)
    max_messages: int = 20
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to context."""
        with self._lock:
            self.messages.append(ChatMessage(role=role, content=content))
            # Keep only last N messages
            if len(self.messages) > self.max_messages:
                self.messages = self.messages[-self.max_messages:]

    def get_context(self) -> List[Dict[str, str]]:
        """Get messages for API."""
        with self._lock:
            return [m.to_dict() for m in self.messages]

    def clear(self) -> None:
        """Clear conversation history."""
        with self._lock:
            self.messages.clear()


class AIService:
    """
    High-level AI service for INTEGRA.

    Features:
    - Conversation management with context
    - Pre-defined prompts for common tasks
    - Streaming support with callbacks
    - Thread-safe operations

    Usage:
        service = AIService()

        # Simple chat
        response = service.chat("Hello!")

        # Streaming chat
        for chunk in service.chat_stream("Explain AI"):
            print(chunk, end="")

        # Analysis
        result = service.analyze_data(employee_data)
    """

    _instance: Optional['AIService'] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._client = get_ollama_client()
        self._context = ConversationContext()
        self._system_prompt: Optional[str] = SYSTEM_PROMPTS.get("default")
        self._initialized = True

    @property
    def is_available(self) -> bool:
        """Check if AI service is available."""
        return self._client.is_available()

    @property
    def model(self) -> Optional[str]:
        """Get current model name."""
        return self._client.get_default_model()

    @property
    def models(self) -> List[str]:
        """Get available models."""
        return self._client.get_model_names()

    def set_system_prompt(self, prompt: str) -> None:
        """Set custom system prompt."""
        self._system_prompt = prompt

    def use_prompt(self, prompt_name: str) -> bool:
        """Use a pre-defined system prompt."""
        if prompt_name in SYSTEM_PROMPTS:
            self._system_prompt = SYSTEM_PROMPTS[prompt_name]
            return True
        return False

    def clear_context(self) -> None:
        """Clear conversation history."""
        self._context.clear()

    def chat(
        self,
        message: str,
        keep_context: bool = True,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Send a chat message and get response.

        Args:
            message: User message
            keep_context: Whether to keep conversation history
            model: Model to use (optional)
            temperature: Response randomness

        Returns:
            Response text or None
        """
        if not self.is_available:
            app_logger.warning("AI service not available")
            return None

        context = self._context.get_context() if keep_context else None

        response = self._client.chat(
            message=message,
            model=model,
            system=self._system_prompt,
            context=context,
            temperature=temperature
        )

        if response and keep_context:
            self._context.add_message("user", message)
            self._context.add_message("assistant", response)

        return response

    def chat_stream(
        self,
        message: str,
        keep_context: bool = True,
        model: Optional[str] = None,
        temperature: float = 0.7,
        on_chunk: Optional[Callable[[str], None]] = None
    ) -> Generator[str, None, None]:
        """
        Send a chat message and get streaming response.

        Args:
            message: User message
            keep_context: Whether to keep conversation history
            model: Model to use
            temperature: Response randomness
            on_chunk: Callback for each chunk

        Yields:
            Response text chunks
        """
        if not self.is_available:
            return

        context = self._context.get_context() if keep_context else None
        full_response = []

        for chunk in self._client.chat_stream(
            message=message,
            model=model,
            system=self._system_prompt,
            context=context,
            temperature=temperature
        ):
            full_response.append(chunk)
            if on_chunk:
                on_chunk(chunk)
            yield chunk

        # Update context after stream completes
        if keep_context and full_response:
            self._context.add_message("user", message)
            self._context.add_message("assistant", "".join(full_response))

    def analyze_text(
        self,
        text: str,
        analysis_type: str = "general",
        language: str = "ar"
    ) -> Optional[str]:
        """
        Analyze text with AI.

        Args:
            text: Text to analyze
            analysis_type: Type of analysis (general, sentiment, summary, extract)
            language: Response language (ar, en)

        Returns:
            Analysis result
        """
        prompts = {
            "general": f"حلل النص التالي وقدم ملاحظات مفيدة:\n\n{text}",
            "sentiment": f"حلل المشاعر في النص التالي (إيجابي/سلبي/محايد) مع التفسير:\n\n{text}",
            "summary": f"لخص النص التالي بشكل مختصر ومفيد:\n\n{text}",
            "extract": f"استخرج المعلومات المهمة والنقاط الرئيسية من النص:\n\n{text}"
        }

        if language == "en":
            prompts = {
                "general": f"Analyze the following text and provide useful insights:\n\n{text}",
                "sentiment": f"Analyze the sentiment (positive/negative/neutral) with explanation:\n\n{text}",
                "summary": f"Summarize the following text concisely:\n\n{text}",
                "extract": f"Extract key information and main points from the text:\n\n{text}"
            }

        prompt = prompts.get(analysis_type, prompts["general"])

        return self._client.chat(
            message=prompt,
            system=SYSTEM_PROMPTS.get("analyst"),
            temperature=0.3  # Lower for more focused analysis
        )

    def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        language: str = "ar"
    ) -> Optional[str]:
        """
        Summarize text.

        Args:
            text: Text to summarize
            max_length: Approximate max length in words
            language: Response language

        Returns:
            Summary
        """
        length_hint = ""
        if max_length:
            if language == "ar":
                length_hint = f" في حدود {max_length} كلمة"
            else:
                length_hint = f" in approximately {max_length} words"

        if language == "ar":
            prompt = f"لخص النص التالي بشكل مختصر وواضح{length_hint}:\n\n{text}"
        else:
            prompt = f"Summarize the following text concisely{length_hint}:\n\n{text}"

        return self._client.chat(
            message=prompt,
            system=SYSTEM_PROMPTS.get("summarizer"),
            temperature=0.3
        )

    def translate(
        self,
        text: str,
        target_language: str = "en"
    ) -> Optional[str]:
        """
        Translate text.

        Args:
            text: Text to translate
            target_language: Target language code (ar, en)

        Returns:
            Translated text
        """
        lang_names = {"ar": "Arabic", "en": "English"}
        target = lang_names.get(target_language, target_language)

        prompt = f"Translate the following text to {target}. Only output the translation, no explanations:\n\n{text}"

        return self._client.chat(
            message=prompt,
            temperature=0.1  # Very low for accurate translation
        )

    def answer_question(
        self,
        question: str,
        context_data: Optional[str] = None,
        language: str = "ar"
    ) -> Optional[str]:
        """
        Answer a question, optionally with context data.

        Args:
            question: The question to answer
            context_data: Additional context/data for the answer
            language: Response language

        Returns:
            Answer
        """
        if context_data:
            if language == "ar":
                prompt = f"بناءً على البيانات التالية:\n{context_data}\n\nأجب على السؤال: {question}"
            else:
                prompt = f"Based on the following data:\n{context_data}\n\nAnswer the question: {question}"
        else:
            prompt = question

        return self._client.chat(
            message=prompt,
            system=SYSTEM_PROMPTS.get("assistant"),
            temperature=0.5
        )


# Singleton instance
_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get the singleton AI service instance."""
    global _service
    if _service is None:
        _service = AIService()
    return _service


def chat(message: str, **kwargs) -> Optional[str]:
    """Quick chat function."""
    return get_ai_service().chat(message, **kwargs)


def chat_stream(message: str, **kwargs) -> Generator[str, None, None]:
    """Quick streaming chat function."""
    return get_ai_service().chat_stream(message, **kwargs)


def analyze_text(text: str, **kwargs) -> Optional[str]:
    """Quick text analysis function."""
    return get_ai_service().analyze_text(text, **kwargs)


def summarize(text: str, **kwargs) -> Optional[str]:
    """Quick summarize function."""
    return get_ai_service().summarize(text, **kwargs)
