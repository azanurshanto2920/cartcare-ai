from groq import Groq

from app.core.config import settings

client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = (
    "You are a helpful AI assistant. "
    "Reply briefly and clearly in the same language as the user. "
    "If context from a document is provided, answer using that context. "
    "If the answer is not in the context, say you don't have that information."
)


def build_user_turn(user_message: str, doc_context: str) -> str:
    if doc_context:
        return (
            f"Context from uploaded document:\n{doc_context}\n\n"
            f"Question: {user_message}"
        )
    return user_message


def generate_reply(history: list[dict], user_turn: str) -> str:
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_turn}]
    )

    completion = client.chat.completions.create(
        messages=messages,
        model=settings.llm_model,
        temperature=0.7,
        max_tokens=1024,
    )
    return completion.choices[0].message.content