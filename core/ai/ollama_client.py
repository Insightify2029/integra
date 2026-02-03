"""
Ollama Client
=============
Low-level client for connecting to Ollama API.
Handles connection, model management, and basic chat operations.
"""

from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass
import threading

try:
    import ollama
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None
    Client = None

from core.logging import app_logger


@dataclass
class OllamaModel:
    """Represents an Ollama model."""
    name: str
    size: int
    modified_at: str
    digest: str

    @property
    def size_gb(self) -> float:
        """Return model size in GB."""
        return self.size / (1024 ** 3)

    @property
    def display_name(self) -> str:
        """Return display name without tag."""
        return self.name.split(':')[0]


class OllamaClient:
    """
    Client for interacting with Ollama API.

    Features:
    - Connection management with health checks
    - Model listing and selection
    - Streaming chat support
    - Thread-safe singleton pattern

    Usage:
        client = OllamaClient()
        if client.is_available():
            response = client.chat("Hello!", model="gemma3")
    """

    _instance: Optional['OllamaClient'] = None
    _lock = threading.Lock()

    # Default settings
    DEFAULT_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "gemma3"
    FALLBACK_MODELS = ["llama3.2", "mistral", "gemma2"]

    def __new__(cls, host: Optional[str] = None):
        """Singleton pattern with thread safety."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, host: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            host: Ollama server URL. Default: http://localhost:11434
        """
        if self._initialized:
            return

        self._host = host or self.DEFAULT_HOST
        self._client: Optional['Client'] = None
        self._available: Optional[bool] = None
        self._models: List[OllamaModel] = []
        self._default_model: Optional[str] = None

        self._initialize_client()
        self._initialized = True

    def _initialize_client(self) -> None:
        """Initialize the Ollama client."""
        if not OLLAMA_AVAILABLE:
            app_logger.warning("Ollama library not installed. AI features disabled.")
            self._available = False
            return

        try:
            self._client = Client(host=self._host)
            self._check_connection()
        except Exception as e:
            app_logger.warning(f"Failed to initialize Ollama client: {e}")
            self._available = False

    def _check_connection(self) -> bool:
        """Check if Ollama server is running."""
        if not self._client:
            self._available = False
            return False

        try:
            # Try to list models as a health check
            response = self._client.list()
            self._available = True
            self._update_models(response.get('models', []))
            app_logger.info(f"Ollama connected. {len(self._models)} models available.")
            return True
        except Exception as e:
            app_logger.warning(f"Ollama server not available: {e}")
            self._available = False
            return False

    def _update_models(self, models_data: List[Dict]) -> None:
        """Update the list of available models."""
        self._models = []
        for m in models_data:
            try:
                model = OllamaModel(
                    name=m.get('name', ''),
                    size=m.get('size', 0),
                    modified_at=m.get('modified_at', ''),
                    digest=m.get('digest', '')
                )
                self._models.append(model)
            except Exception:
                continue

        # Set default model
        self._select_default_model()

    def _select_default_model(self) -> None:
        """Select the best available default model."""
        if not self._models:
            self._default_model = None
            return

        model_names = [m.name.split(':')[0] for m in self._models]

        # Check preferred models in order
        preferred = [self.DEFAULT_MODEL] + self.FALLBACK_MODELS
        for model in preferred:
            if model in model_names:
                self._default_model = model
                app_logger.info(f"Default AI model: {model}")
                return

        # Use first available model
        self._default_model = self._models[0].name
        app_logger.info(f"Default AI model (fallback): {self._default_model}")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        if self._available is None:
            self._check_connection()
        return self._available or False

    def refresh(self) -> bool:
        """Refresh connection and model list."""
        self._available = None
        return self._check_connection()

    def get_models(self) -> List[OllamaModel]:
        """Get list of available models."""
        if not self.is_available():
            return []
        return self._models.copy()

    def get_model_names(self) -> List[str]:
        """Get list of model names."""
        return [m.name for m in self.get_models()]

    def get_default_model(self) -> Optional[str]:
        """Get the default model name."""
        if not self.is_available():
            return None
        return self._default_model

    def has_model(self, model_name: str) -> bool:
        """Check if a specific model is available."""
        names = [m.name.split(':')[0] for m in self._models]
        return model_name.split(':')[0] in names

    def chat(
        self,
        message: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[str]:
        """
        Send a chat message and get response.

        Args:
            message: User message
            model: Model name. Uses default if not specified.
            system: System prompt
            context: Previous conversation messages
            temperature: Response randomness (0.0-1.0)
            **kwargs: Additional Ollama options

        Returns:
            Response text or None if failed
        """
        if not self.is_available() or not self._client:
            return None

        model = model or self._default_model
        if not model:
            app_logger.error("No model available for chat")
            return None

        try:
            messages = []

            # Add system prompt
            if system:
                messages.append({"role": "system", "content": system})

            # Add context (previous messages)
            if context:
                messages.extend(context)

            # Add current message
            messages.append({"role": "user", "content": message})

            response = self._client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs}
            )

            return response.get('message', {}).get('content', '')

        except Exception as e:
            app_logger.error(f"Ollama chat error: {e}")
            return None

    def chat_stream(
        self,
        message: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Send a chat message and get streaming response.

        Args:
            message: User message
            model: Model name
            system: System prompt
            context: Previous conversation messages
            temperature: Response randomness
            **kwargs: Additional options

        Yields:
            Response text chunks
        """
        if not self.is_available() or not self._client:
            return

        model = model or self._default_model
        if not model:
            return

        try:
            messages = []

            if system:
                messages.append({"role": "system", "content": system})

            if context:
                messages.extend(context)

            messages.append({"role": "user", "content": message})

            stream = self._client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature, **kwargs},
                stream=True
            )

            for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                if content:
                    yield content

        except Exception as e:
            app_logger.error(f"Ollama stream error: {e}")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Generate text completion (non-chat mode).

        Args:
            prompt: Input prompt
            model: Model name
            system: System prompt
            **kwargs: Additional options

        Returns:
            Generated text or None
        """
        if not self.is_available() or not self._client:
            return None

        model = model or self._default_model
        if not model:
            return None

        try:
            response = self._client.generate(
                model=model,
                prompt=prompt,
                system=system,
                **kwargs
            )
            return response.get('response', '')
        except Exception as e:
            app_logger.error(f"Ollama generate error: {e}")
            return None


# Singleton instance
_client: Optional[OllamaClient] = None


def get_ollama_client(host: Optional[str] = None) -> OllamaClient:
    """Get the singleton Ollama client instance."""
    global _client
    if _client is None:
        _client = OllamaClient(host)
    return _client


def is_ollama_available() -> bool:
    """Check if Ollama is available."""
    return get_ollama_client().is_available()


def list_models() -> List[str]:
    """Get list of available model names."""
    return get_ollama_client().get_model_names()


def get_default_model() -> Optional[str]:
    """Get the default model name."""
    return get_ollama_client().get_default_model()
