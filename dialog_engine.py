from openai import OpenAI
from config import OPENAI_API_KEY, MODEL
import json

client = OpenAI(api_key=OPENAI_API_KEY)

# ===============================
# LLM-валидация + нормализация ответов (без f-string)
# ===============================

def analyze_answer(question: str, answer: str) -> dict:
    """
    Возвращает словарь:
    {
        "status": "ok" / "bad" / "clarify",
        "normalized": "...",
        "clarify_question": "..."
    }
    """

    prompt = (
        "Ты — senior бизнес-аналитик. Проанализируй ответ пользователя на вопрос.\n"
        "\n"
        "Вопрос: \"{question}\"\n"
        "Ответ пользователя: \"{answer}\"\n"
        "\n"
        "Твоя задача:\n"
        "1) Оценить качество ответа.\n"
        "2) Проверить, относится ли ответ к вопросу.\n"
        "3) Нормализовать текст до профессиональной формулировки.\n"
        "4) Если ответ неполный, бессмысленный, слишком короткий, или не относится — предложить уточняющий вопрос.\n"
        "\n"
        "Верни JSON строго в формате:\n"
        "{{\n"
        "  \"status\": \"ok\" или \"bad\" или \"clarify\",\n"
        "  \"normalized\": \"...\",\n"
        "  \"clarify_question\": \"...\"\n"
        "}}\n"
        "\n"
        "Правила:\n"
        "- 'ok' — ответ качественный, можно использовать.\n"
        "- 'bad' — ответ нерелевантный / мусор / слишком короткий.\n"
        "- 'clarify' — ответ частично понятен → нужно уточнение.\n"
    ).format(question=question, answer=answer)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    content = response.choices[0].message.content

    # Безопасный JSON парсинг
    try:
        data = json.loads(content)
        return data
    except:
        return {
            "status": "bad",
            "normalized": answer,
            "clarify_question": "Можешь, пожалуйста, дать более точный и содержательный ответ?"
        }