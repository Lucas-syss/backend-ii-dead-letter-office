import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()


def get_llm() -> LLM:
    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise ValueError("NVIDIA_API_KEY is not configured")

    return LLM(
        model="nvidia_nim/meta/llama-3.1-70b-instruct",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )