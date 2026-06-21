import httpx
import json
from config import settings

SYSTEM_PROMPT = """You are a data extraction assistant. Your ONLY job is to extract \
information that is ALREADY PRESENT in the text provided to you.

Rules:
- DO NOT invent, infer, or generate any content of your own
- DO NOT fill in missing options or answers if they are not in the text
- If a field is not present in the text, return null for that field
- Extract ONLY: question_text, options (a/b/c/d), correct_answer, explanation
- correct_answer must be a single lowercase letter: a, b, c, or d
- Return a valid JSON object. Nothing else.

If the text does not contain a clear question, return: {"error": "no_question_found"}"""


async def extract_with_llm(raw_text: str) -> dict | None:
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract from this text:\n\n{raw_text}"},
        ],
        "stream": False,
        "format": "json",
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            data = json.loads(content)

            if "error" in data:
                return None

            # Normalize correct_answer to lowercase
            if "correct_answer" in data and data["correct_answer"]:
                data["correct_answer"] = data["correct_answer"].lower()

            return data
    except Exception:
        return None
