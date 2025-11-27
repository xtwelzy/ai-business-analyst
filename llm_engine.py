from openai import OpenAI
from config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_brd(requirements: dict) -> str:
    """
    Генерирует полный BRD документ:
    - Цель
    - Проблема
    - Stakeholders
    - Scope
    - Business Rules
    - FR
    - NFR (расширенные)
    - KPI (лидирующие + дерево)
    - User Stories
    - Use Case Diagram
    - Business Process Diagram
    - Activity Diagram
    - Sequence Diagram
    - Risk Matrix
    - Acceptance Criteria
    """

    prompt = (
        "Ты — senior business analyst. Сформируй полный BRD документ "
        "по мировым стандартам IIBA, Agile, PMBOK.\n\n"
        "Используй входные данные:\n"
        f"{requirements}\n\n"
        "Сформируй документ строго по структуре ниже.\n"
        "Каждый блок — обязательный.\n\n"
        "============================================================\n"
        "# 1. Цель проекта\n"
        "Опиши чётко и конкретно.\n\n"
        "# 2. Описание бизнес-проблемы\n"
        "Опиши корневую проблему, последствия и влияния.\n\n"
        "# 3. Stakeholders\n"
        "- Business Owner\n"
        "- End Users\n"
        "- SME\n"
        "- BA\n"
        "- IT Team\n"
        "- External Actors\n\n"
        "# 4. Scope\n"
        "## In Scope\n"
        "...\n"
        "## Out of Scope\n"
        "...\n\n"
        "# 5. Бизнес-правила\n"
        "Сформулируй конкретные правила.\n\n"
        "# 6. Функциональные требования (FR)\n"
        "Формат:\n"
        "FR-01: ...\n"
        "FR-02: ...\n\n"
        "# 7. Нефункциональные требования (расширенные NFR)\n"
        "- Performance (время ответа, обновление данных)\n"
        "- Security (уровни доступа, шифрование)\n"
        "- Scalability (масштабирование на N пользователей)\n"
        "- Reliability (устойчивость, fault tolerance)\n"
        "- Observability (логирование, мониторинг)\n"
        "- Usability (UI/UX требования)\n"
        "- Maintainability (поддержка, обновления)\n"
        "- Compliance (регуляторные требования)\n\n"
        "# 8. KPI / Лидирующие индикаторы\n"
        "1) ...\n"
        "2) ...\n\n"
        "## KPI Tree (Mermaid)\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    Root[KPI Главная цель]\n"
        "    Root --> KPI1\n"
        "    Root --> KPI2\n"
        "    Root --> KPI3\n"
        "```\n\n"
        "# 9. Acceptance Criteria\n"
        "- AC-01: ...\n"
        "- AC-02: ...\n"
        "- AC-03: ...\n\n"
        "# 10. User Stories\n"
        "Формат:\n"
        "As a <кто>, I want <что>, so that <ценность>.\n\n"
        "# 11. Use Case Diagram (Mermaid)\n"
        "```mermaid\n"
        "flowchart LR\n"
        "    Actor --> System\n"
        "```\n\n"
        "# 12. Business Process Diagram (BPMN / Flowchart)\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    Start --> Step1 --> Step2 --> End\n"
        "```\n\n"
        "# 13. Activity Diagram (Mermaid)\n"
        "```mermaid\n"
        "flowchart TD\n"
        "    Start --> Activity1 --> Decision --> Activity2 --> End\n"
        "```\n\n"
        "# 14. Sequence Diagram (Mermaid)\n"
        "```mermaid\n"
        "sequenceDiagram\n"
        "    participant User\n"
        "    participant System\n"
        "    User->>System: Действие\n"
        "    System-->>User: Ответ\n"
        "```\n\n"
        "# 15. Risk Matrix\n"
        "| Риск | Вероятность | Влияние | План реагирования |\n"
        "|------|-------------|---------|--------------------|\n"
        "| ... | ... | ... | ... |\n\n"
        "============================================================\n"
        "Верни ЧИСТЫЙ документ, без пояснений."
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты — эксперт по бизнес-аналитике уровня Senior."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
