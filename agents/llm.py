"""Shared LLM configuration."""

from langchain_openai import ChatOpenAI

MODEL = "gpt-4o"


def get_llm(temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=temperature)
