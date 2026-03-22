"""Shared LLM configuration."""

from langchain_openai import ChatOpenAI

MODEL = "gpt-5.4-mini"


def get_llm(temperature: float = 0) -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=temperature)
