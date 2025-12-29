from personal_todo.config import settings

LLM_PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3-haiku"
    },
    "byok": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4-turbo"
    },
    "local": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama2"
    }
}


def get_llm_client():
    provider = settings.llm_provider
    config = LLM_PROVIDERS[provider]
    return {
        "provider": provider,
        "base_url": config["base_url"],
        "model": settings.llm_model,
        "api_key": settings.llm_api_key
    }
