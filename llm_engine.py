from openai import OpenAI
from config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def extract_mermaid_blocks(text: str):
    import re

    mermaid_blocks = re.findall(r"```mermaid(.*?)```", text, flags=re.DOTALL)

    diagrams = {
        "kpi_tree_mermaid": None,
        "usecase_mermaid": None,
        "bpmn_mermaid": None,
        "activity_mermaid": None,
        "sequence_mermaid": None
    }

    for block in mermaid_blocks:
        cleaned = block.strip()

        # KPI Tree
        if "Root" in cleaned and ("KPI" in cleaned or "KPI " in cleaned):
            diagrams["kpi_tree_mermaid"] = cleaned

        # Use Case — надёжно
        elif "flowchart" in cleaned and ("User" in cleaned or "Пользователь" in cleaned or "Actor" in cleaned):
            diagrams["usecase_mermaid"] = cleaned

        # BPMN-like
        elif "Start" in cleaned and "End" in cleaned:
            diagrams["bpmn_mermaid"] = cleaned

        # Activity
        elif "A1" in cleaned or "Action" in cleaned or "Действие" in cleaned:
            diagrams["activity_mermaid"] = cleaned

        # Sequence
        elif "sequenceDiagram" in cleaned:
            diagrams["sequence_mermaid"] = cleaned

    # ==== FALLBACKS ====

    if diagrams["usecase_mermaid"] is None:
        diagrams["usecase_mermaid"] = """
flowchart LR
    User((Пользователь))
    System((Система))
    External((Внешняя система))

    User -->|Оставляет отзыв| System
    System -->|Отправляет уведомление| User
    System --> External
""".strip()

    if diagrams["activity_mermaid"] is None:
        diagrams["activity_mermaid"] = """
flowchart TD
    Start --> A1[Сбор отзывов]
    A1 --> A2[Классификация тональности]
    A2 --> D{Негативный отзыв?}
    D -->|Yes| A3[Отправка алерта менеджеру]
    D -->|No| A4[Анализ положительных отзывов]
    A3 --> End
    A4 --> End
""".strip()

    clean_doc = re.sub(r"```mermaid.*?```", "", text, flags=re.DOTALL)

    return {
        "document": clean_doc.strip(),
        **diagrams
    }


def generate_brd(requirements: dict) -> dict:
    prompt = f"""
Ты — Senior Business Analyst международного уровня (IIBA CBAP, PMI-PBA).
Сформируй ИДЕАЛЬНЫЙ BRD документ строго по структуре ниже.

Используй входные данные пользователя (JSON):
{requirements}

⚠️ ТРЕБОВАНИЯ:
- Ноль воды
- Только финальный документ
- Чёткие формулировки
- Диаграммы строго в формате mermaid
- Таблицы в markdown
- ВСЕ секции обязательны

============================================================
# 1. Цель проекта
Опиши чёткую, измеримую, достижимую бизнес-цель.

# 2. Описание бизнес-проблемы
Опиши:
- корневую причину
- последствия
- влияние на процессы
- финансовый/операционный ущерб

# 3. Stakeholders
Укажи:
- Business Owner
- End Users
- SME
- BA
- IT Team
- External Actors

# 4. Scope
## In Scope
Перечисли всё, что входит.
## Out of Scope
Перечисли исключения.

# 5. Бизнес-правила
Сформируй 5–10 конкретных правил.

# 6. Функциональные требования (FR)
Формат:
FR-01: ...
FR-02: ...
FR-03: ...

# 7. Extended Non-Functional Requirements (NFR)
Разделы:
- Performance
- Security
- Scalability
- Reliability
- Observability
- Usability
- Maintainability
- Compliance
Каждый раздел — 3–5 требований.

# 8. KPI / Лидирующие показатели
Сформируй минимум 4 KPI.

## KPI Tree (Mermaid)
```mermaid
flowchart TD
    Root[KPI Главная цель]
    Root --> KPI1
    Root --> KPI2
    Root --> KPI3
    KPI1 --> KPI11
    KPI2 --> KPI21
```

# 9. Acceptance Criteria
Минимум 5 пунктов:
- AC-01: ...
- AC-02: ...

# 10. User Stories
Минимум 3–6 stories.
Формат:
As a <role>, I want <feature>, so that <value>.

# 11. Use Case Diagram (Mermaid)
```mermaid
flowchart LR
    User((Пользователь))
    System((Система))
    External((Внешняя система))

    User -->|Оставляет отзыв| System
    System -->|Отправляет уведомление| User
    System --> External
```

# 12. Business Process Diagram (Mermaid)
```mermaid
flowchart TD
    Start([Start])
    --> Step1
    --> Step2
    --> Decision{{condition?}}
    -->|Yes| StepYes
    -->|No| StepNo
    --> End([End])
```

# 13. Activity Diagram (Mermaid)
Построй Activity Diagram, отражающую обработку отзыва.
```mermaid
flowchart TD
    Start --> A1[Сбор отзывов]
    A1 --> A2[Классификация]
    A2 --> D{{Негативный?}}
    D -->|Yes| A3[Алерт менеджеру]
    D -->|No| A4[Анализ положительных]
    A3 --> End
    A4 --> End
```

# 14. Sequence Diagram (Mermaid)
```mermaid
sequenceDiagram
    participant User
    participant System
    participant Service

    User->>System: Отправляет отзыв
    System->>Service: Классификация
    Service-->>System: Результат
    System-->>User: Уведомление
```

# 15. Risk Matrix
| Риск | Вероятность | Влияние | Митигирование |
|------|-------------|---------|----------------|
| ... | ... | ... | ... |
| ... | ... | ... | ... |

============================================================
Верни только финальный BRD документ. БЕЗ пояснений.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Ты — эксперт по бизнес-аналитике уровня Senior."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.15
    )

    full_text = response.choices[0].message.content

    return extract_mermaid_blocks(full_text)