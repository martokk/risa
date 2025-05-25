from phi.model.anthropic.claude import Claude
from phi.model.base import Model
from phi.model.google.gemini import Gemini
from phi.model.groq.groq import Groq
from phi.model.openai.chat import OpenAIChat


def get_llm_model(provider: str, model_str: str) -> Model:
    if provider == "openai":
        return OpenAIChat(id=model_str)
    if provider == "anthropic":
        return Claude(id=model_str)
    if provider == "groq":
        return Groq(id=model_str)
    if provider == "google":
        return Gemini(id=model_str)
    raise ValueError(f"Provider {provider} not supported")
