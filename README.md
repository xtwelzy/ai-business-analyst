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

### 🤖 Интеллектуальный сбор требований

* Автоматические уточняющие вопросы
* Нормализация и валидация ответов через LLM
* Возможность вернуться назад: `/back`
* Возможность пропустить вопрос: `/skip`
* История ответов сохраняется

### 📄 Генерация BRD (полный набор артефактов)

Генерация включает:

* Цель проекта
* Проблему
* Stakeholders
* Scope (In / Out)
* Бизнес-правила
* FR / NFR (расширенные)
* KPI + KPI Tree (Mermaid)
* Acceptance Criteria
* User Stories
* Use Case Diagram
* Business Process Diagram
* Activity Diagram
* Sequence Diagram
* Risk Matrix

### 📘 PDF-генерация

* Красиво оформленный BRD PDF
* Поддержка кириллицы (шрифт Montserrat)
* Автоматическая структура

### 🟦 Интеграция с Confluence

Бот автоматически:

* Авторизуется
* Создаёт страницу
* Загружает PDF
* Возвращает корректный URL

---

## 📁 Структура проекта

```
ai-business-analyst/
│── bot.py                 # Telegram-бот, FSM, диалоги
│── llm_engine.py          # Генерация BRD через OpenAI
│── dialog_engine.py       # Валидация/нормализация ответов
│── confluence_api.py      # Интеграция с Confluence
│── utils.py               # Хранилище ответов
│── config.py              # Конфигурация (.env)
│── fonts/
│     └── Montserrat-Regular.ttf
│     └── Montserrat-Bold.ttf
│── README.md
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

Используется ReportLab, стиль Montserrat, поддержка кириллицы.

### 5️⃣ Создание страницы в Confluence

* правильный space key
* ограничение title 255 символов
* загрузка PDF
* возврат корректной ссылки

---

## 🔐 Установка и запуск

### 1️⃣ Установить зависимости

```
pip install -r requirements.txt
```

### 2️⃣ Создать файл `.env`

```
TELEGRAM_BOT_TOKEN=xxx
OPENAI_API_KEY=xxx
CONFLUENCE_BASE_URL=https://your.atlassian.net/wiki
CONFLUENCE_EMAIL=you@gmail.com
CONFLUENCE_API_TOKEN=xxx
CONFLUENCE_SPACE_KEY=AA
MODEL=gpt-4.1
```

### 3️⃣ Запустить бота

```
python bot.py
```

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
