import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_llm(api_key: str | None = None) -> ChatGroq:

    groq_api_key = (api_key or "").strip() or os.getenv("GROQ_API")

    if not groq_api_key:
        raise RuntimeError(
            "No Groq API key available: set one in your profile, or "
            "configure GROQ_API in the environment"
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.1,
        api_key=groq_api_key,  # type: ignore
    )