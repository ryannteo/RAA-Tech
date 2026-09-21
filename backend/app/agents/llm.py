# Swappable LLM client. Defaults to a mock (no API key needed) so the graph
# runs end-to-end on day one. Point LLM_PROVIDER/LLM_BASE_URL/LLM_API_KEY at
# any OpenAI-compatible endpoint (Tencent Hunyuan, OpenAI, ...) when ready.
from app.config import get_settings


class LLMClient:
    def __init__(self) -> None:
        self._settings = get_settings()

    async def complete(self, system: str, user: str) -> str:
        if self._settings.llm_provider == "mock" or not self._settings.llm_api_key:
            return f"[MOCK RESPONSE] system={system[:40]!r} user={user[:40]!r}"

        from openai import AsyncOpenAI  # lazy import: mock mode has no hard dependency on it

        client = AsyncOpenAI(api_key=self._settings.llm_api_key, base_url=self._settings.llm_base_url or None)
        response = await client.chat.completions.create(
            model=self._settings.llm_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return response.choices[0].message.content or ""


llm_client = LLMClient()
