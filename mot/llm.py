"""
Self-contained LLM client supporting OpenAI and Anthropic backends.

Supports:
  - OpenAI API  (GPT-4o-mini, GPT-4, etc.)
  - OpenAI-compatible APIs  (DeepSeek-R1 via https://api.deepseek.com)
  - Anthropic API  (Claude models)

Environment variables:
  OPENAI_API_KEY       OpenAI / DeepSeek API key
  OPENAI_BASE_URL      Override base URL (e.g., https://api.deepseek.com)
  ANTHROPIC_API_KEY    Anthropic API key (alias: ANTHROPIC_AUTH_TOKEN)
  ANTHROPIC_BASE_URL   Override Anthropic base URL
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Thin LLM wrapper with retry logic (exponential back-off).

    Parameters
    ----------
    backend : "openai" | "anthropic"
    model   : model name passed to the API
    api_key : overrides env-var lookup
    base_url: overrides env-var lookup (useful for DeepSeek or local servers)
    temperature : default sampling temperature (paper uses API default ≈ 1.0)
    max_tokens  : default max tokens for completions
    max_retries : number of retry attempts before raising
    """

    SUPPORTED_BACKENDS = {"openai", "anthropic"}

    def __init__(
        self,
        backend: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: int = 2048,
        max_retries: int = 3,
    ) -> None:
        if backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"backend must be one of {self.SUPPORTED_BACKENDS}, got {backend!r}"
            )
        self.backend = backend
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries

        if backend == "openai":
            import openai  # type: ignore[import]

            _key = api_key or os.environ.get("OPENAI_API_KEY")
            _url = base_url or os.environ.get("OPENAI_BASE_URL")
            self._client = openai.OpenAI(api_key=_key, base_url=_url)

        else:  # anthropic
            import anthropic  # type: ignore[import]

            _key = (
                api_key
                or os.environ.get("ANTHROPIC_AUTH_TOKEN")
                or os.environ.get("ANTHROPIC_API_KEY")
            )
            _url = base_url or os.environ.get("ANTHROPIC_BASE_URL")
            self._client = anthropic.Anthropic(api_key=_key, base_url=_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Single-turn chat completion.

        Parameters
        ----------
        messages    : list of {"role": "user"|"assistant", "content": "..."}
        system      : optional system prompt (prepended for OpenAI, top-level for Anthropic)
        temperature : overrides self.temperature if provided
        max_tokens  : overrides self.max_tokens if provided

        Returns
        -------
        str: the model's reply text
        """
        temp = temperature if temperature is not None else self.temperature
        tok = max_tokens if max_tokens is not None else self.max_tokens

        for attempt in range(self.max_retries):
            try:
                return self._call(messages, system, temp, tok)
            except Exception as exc:
                exc_str = str(exc)
                if "429" in exc_str or "rate" in exc_str.lower() or "quota" in exc_str.lower():
                    wait = 30 * (attempt + 1)   # 30s, 60s, 90s
                else:
                    wait = 2 ** attempt          # 1s, 2s, 4s
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying in %ds",
                    attempt + 1, self.max_retries, exc, wait,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait)
                else:
                    raise

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        if self.backend == "openai":
            return self._call_openai(messages, system, temperature, max_tokens)
        return self._call_anthropic(messages, system, temperature, max_tokens)

    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        all_messages: List[Dict[str, Any]] = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=all_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def _call_anthropic(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        kwargs: Dict[str, Any] = dict(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=messages,
        )
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return response.content[0].text.strip()
