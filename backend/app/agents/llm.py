"""TokenHub structured output through the existing OpenAI-compatible client."""
import json

from pydantic import BaseModel

from app.config import Settings, get_settings


class LLMError(Exception):
    """Safe diagnostic for the controlled advocate-error boundary."""


class LLMConfigurationError(LLMError):
    pass


class LLMOutputError(LLMError):
    pass


def _message_content(envelope: object) -> str:
    """Check untrusted wire data before accessing fields; ignore provider extras."""
    if not isinstance(envelope, dict) or envelope.get("error") is not None:
        raise LLMOutputError("LLM returned an invalid response envelope.")
    choices = envelope.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise LLMOutputError("LLM must return exactly one choice.")
    choice = choices[0]
    if not isinstance(choice, dict) or choice.get("finish_reason") != "stop":
        raise LLMOutputError("LLM did not finish the structured response.")
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise LLMOutputError("LLM returned an invalid assistant message.")
    if message.get("refusal") or message.get("tool_calls"):
        raise LLMOutputError("LLM refused or returned a tool call.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise LLMOutputError("LLM returned no structured content.")
    # In particular, never return reasoning_content or substitute it for content.
    return content


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    @property
    def settings(self) -> Settings:
        return self._settings if self._settings is not None else get_settings()

    @property
    def is_mock(self) -> bool:
        return self.settings.llm_provider == "mock"

    async def complete(self, system: str, user: str, *, response_model: type[BaseModel]) -> str:
        settings = self.settings
        if settings.llm_provider != "tokenhub":
            raise LLMConfigurationError("A real call requires LLM_PROVIDER=tokenhub; mock cases are explicit agent stubs.")
        if not settings.llm_api_key.strip():
            raise LLMConfigurationError("LLM_API_KEY is required when LLM_PROVIDER=tokenhub.")
        if not settings.llm_base_url.strip():
            raise LLMConfigurationError("LLM_BASE_URL must specify the TokenHub endpoint for the API key's site.")

        from openai import AsyncOpenAI, OpenAIError  # mock mode needs no provider client

        # One source of truth: the existing output contract, not a parallel schema.
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": response_model.model_json_schema(),
            },
        }
        try:
            async with AsyncOpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                timeout=60.0,
                max_retries=0,
            ) as client:
                response = await client.chat.completions.with_raw_response.create(
                    model=settings.llm_model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    response_format=response_format,
                    stream=False,
                )
                # Bypass SDK envelope coercion and parse helpers. A 200 response
                # is untrusted bytes, even when its Content-Type claims JSON.
                return _message_content(json.loads(response.content))
        except LLMError:
            raise
        except OpenAIError as exc:
            raise LLMError("LLM provider request failed or could not produce a complete response.") from exc
        except Exception as exc:
            # Narrow external boundary: SDK/HTTP decoding and envelope parsing
            # can raise exceptions outside OpenAIError (including recursion).
            # Do not catch BaseException/cancellation or expose response bodies.
            raise LLMOutputError("LLM provider response could not be decoded or parsed.") from exc


llm_client = LLMClient()
