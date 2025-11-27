# 🤖 AI Business Analyst Bot – Automated BRD Generator

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Aiogram-3.x-0096FF?style=for-the-badge">
  <img src="https://img.shields.io/badge/OpenAI_API-Enabled-412991?style=for-the-badge&logo=openai">
  <img src="https://img.shields.io/badge/Confluence-Integration-172B4D?style=for-the-badge&logo=confluence">
  <br>
  <img src="https://img.shields.io/badge/Status-Production_ready-brightgreen?style=for-the-badge">
</p>

<p align="center">
  <strong>Полностью автоматизированный Telegram-бот для генерации BRD документов</strong><br>
  Сбор требований → LLM-валидация → Предпросмотр → PDF → загрузка в Confluence.
</p>

---

## ✨ Основные возможности

### ✔ Интеллектуальный сбор требований

Бот последовательно задаёт восемь ключевых вопросов:

* Цель проекта
* Бизнес‑проблема
* Stakeholders
* Scope (In / Out)
* Функциональные требования
* Нефункциональные требования
* KPI
* Risk Matrix

---

## 📲 Команды Telegram бота

| Команда  | Описание                  |
| -------- | ------------------------- |
| `/start` | Приветственное сообщение  |
| `/new`   | Начать сбор требований    |
| `/back`  | Вернуться на шаг назад    |
| `/skip`  | Пропустить текущий вопрос |
| `/help`  | Показать список команд    |
| `/cancel`| отменить текущую сессию и начать заново    |


Каждый ответ проверяется и нормализуется через LLM.

---

## 🧠 Генерация BRD

Бот формирует полный структурированный документ, содержащий:

* Цель проекта
* Проблему
* Stakeholders
* Scope
* Бизнес‑правила
* FR, NFR
* KPI + KPI Tree
* Acceptance Criteria
* User Stories
* Use Case Diagram
* Business Process Diagram
* Activity Diagram
* Sequence Diagram
* Risk Matrix

Все диаграммы генерируются в формате **Mermaid → PNG**.

---

## 📘 PDF генерация

PDF формируется с помощью ReportLab:

* Поддержка кириллицы (шрифт Montserrat)
* Корректное отображение таблиц
* Аккуратное масштабирование диаграмм
* Чёткая структура документа

---

## 🟦 Интеграция с Confluence

Бот автоматически:

* Создаёт или обновляет страницу
* Преобразует таблицы Markdown → HTML
* Загружает PDF как вложение
* Загружает PNG диаграмм
* Вставляет изображения в тело страницы
* Возвращает готовый URL

---

## 📁 Структура проекта

```
ai-business-analyst/
│── bot.py                 # Telegram-бот
│── llm_engine.py          # Генерация BRD
│── dialog_engine.py       # Валидация ответов
│── confluence_api.py      # Интеграция с Confluence
│── diagram_renderer.py    # Mermaid → PNG
│── pdf_engine.py          # Генерация PDF
│── utils.py               # Хранилище диалогов
│── config.py              # ENV настройки
│── fonts/                 # Шрифты Montserrat
│     └── Montserrat-Regular.ttf
│     └── Montserrat-Bold.ttf
│── diagrams/              # Генерируемые изображения
│── requirements.txt
└── .env
```

---

## 🧠 Как работает система

### 1️⃣ Сбор требований

Пользователь отвечает на 8 ключевых вопросов.
Бот проверяет:

* полноту
* смысл
* структуру
* необходимость уточнения

### 2️⃣ LLM-валидация

Каждый ответ проходит анализ:

* `ok` — принимаем
* `clarify` — бот задаёт уточняющий вопрос
* `bad` — просит уточнить

### 3️⃣ Предпросмотр

Пользователь получает полный BRD и кнопки:

* **Confirm (YES)**
* **Restart (NO)**

### 4️⃣ Генерация PDF

* ReportLab + Montserrat
* корректный рендер таблиц
* масштабирование диаграмм без искажений
* чистая структура документа

### 5️⃣ Создание страницы в Confluence

* генерация HTML‑контента
* преобразование таблиц в HTML
* загрузка PDF и PNG диаграмм
* корректная вставка <ac:image>
* обновление существующей страницы
* возврат удобного URL

---

## ⚙️ Установка

### 1. Установить зависимости

```
pip install -r requirements.txt
```

### 2. Создать файл `.env`

```
TELEGRAM_BOT_TOKEN=xxx
OPENAI_API_KEY=xxx
CONFLUENCE_BASE_URL=https://your.atlassian.net/wiki
CONFLUENCE_EMAIL=you@gmail.com
CONFLUENCE_API_TOKEN=xxx
CONFLUENCE_SPACE_KEY=AA
MODEL=gpt-4.1
```

### 3. Запуск

```
python bot.py
```

---

## 📄 Результат работы

После прохождения всех этапов бот автоматически:

1. Собирает требования
2. Генерирует полноценный BRD
3. Создаёт PNG‑диаграммы
4. Собирает PDF
5. Загружает всё в Confluence
6. Возвращает ссылку на опубликованную страницу

---

## 🔧 Технологии

<p align="center">
<img src="https://skillicons.dev/icons?i=python,git,github,idea" height="60"><br>
<img src="https://img.shields.io/badge/Aiogram-3.x-0096FF?style=for-the-badge">
<img src="https://img.shields.io/badge/OpenAI_API-Enabled-000?logo=openai&style=for-the-badge">
<img src="https://img.shields.io/badge/Confluence_API-Active-172B4D?style=for-the-badge&logo=confluence">
</p>

---

## ❤️ Автор

**Разработчик:** Братуха (xtwelzy)<br>
**Проект создан для:** ForteBank AI Hackathon
</p>

---

## 📄 Лицензи
  
**MIT — свободное использование.**
</p>
