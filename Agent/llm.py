import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_groq import ChatGroq

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def get_llm() -> ChatGroq:
    groq_api_key = os.getenv("GROQ_API")

    if not groq_api_key:
        raise RuntimeError(
            "GROQ_API is missing from environment"
        )

    return ChatGroq(
        model="openai/gpt-oss-20b",
        temperature=0.1,
        api_key=groq_api_key,  # type: ignore
    )