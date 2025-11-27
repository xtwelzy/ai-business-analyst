import asyncio
import os
import tempfile

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

from config import TELEGRAM_BOT_TOKEN
from utils import add_user_answer, get_user_dialog, reset_user
from llm_engine import generate_brd
from dialog_engine import analyze_answer
from confluence_api import create_brd_page

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# ==============================
# Вопросы
# ==============================
QUESTIONS = [
    ("goal", "1️⃣ Какая главная цель проекта?"),
    ("problem", "2️⃣ В чём бизнес-проблема?"),
    ("users", "3️⃣ Кто конечные пользователи (акторы)?"),
    ("scope_in", "4️⃣ Что входит в scope проекта?"),
    ("scope_out", "5️⃣ Что НЕ входит в scope?"),
    ("requirements", "6️⃣ Какие функциональные требования нужны?"),
    ("nfr", "7️⃣ Какие нефункциональные требования (скорость, надёжность)?"),
    ("kpi", "8️⃣ Какие KPI должны улучшиться?"),
]


@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("👋 Привет! Я AI Business Analyst. Напиши /new чтобы начать сбор требований.")


@dp.message(Command("new"))
async def new_requirement(msg: types.Message):
    user_id = str(msg.from_user.id)
    reset_user(user_id)
    add_user_answer(user_id, "step", 0)
    await msg.answer("🔎 Начинаем сбор требований.\n\n" + QUESTIONS[0][1])


@dp.message()
async def process_dialog(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    if "step" not in dialog:
        return await msg.answer("Напиши /new чтобы начать создание BRD.")

    step = dialog["step"]

    # защита
    if step >= len(QUESTIONS):
        step = len(QUESTIONS) - 1
        add_user_answer(user_id, "step", step)

    key, question_text = QUESTIONS[step]

    # -------------------------------
    # Проверка LLM
    # -------------------------------
    analysis = analyze_answer(question_text, msg.text)
    status = analysis.get("status")
    normalized = analysis.get("normalized", msg.text)
    clarify_q = analysis.get("clarify_question")

    if status == "bad":
        return await msg.answer("⚠️ Ответ выглядит неполным или нерелевантным.\n" + question_text)

    if status == "clarify":
        return await msg.answer("❓ " + clarify_q)

    add_user_answer(user_id, key, normalized)

    step += 1
    add_user_answer(user_id, "step", step)

    # -------------------------------
    # Генерация BRD
    # -------------------------------
    if step >= len(QUESTIONS):
        await msg.answer("🧠 Генерирую BRD, PDF и страницу в Confluence…")

        data = get_user_dialog(user_id)
        final_data = {k: v for k, v in data.items() if k != "step"}
        brd_text = generate_brd(final_data)

        # ==============================
        # PDF
        # ==============================
        pdf_path = tempfile.mktemp(suffix=".pdf")

        # Абсолютный путь к TTF файлу
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Regular.ttf")
        pdfmetrics.registerFont(TTFont("Montserrat", font_path))

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=60,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Header", fontName="Montserrat", fontSize=20, spaceAfter=20))
        styles.add(ParagraphStyle(name="H1", fontName="Montserrat", fontSize=16, textColor=colors.HexColor("#1A4D8F"), spaceAfter=10))
        styles.add(ParagraphStyle(name="Body", fontName="Montserrat", fontSize=11, leading=16))

        elements = []

        # Cover page
        elements.append(Paragraph("Business Requirements Document (BRD)", styles["Header"]))
        elements.append(Paragraph("AI Business Analyst Bot", styles["Body"]))
        elements.append(Spacer(1, 40))
        elements.append(PageBreak())

        # BRD sections
        for line in brd_text.split("\n"):
            if line.startswith("# "):
                elements.append(Paragraph(line.replace("# ", ""), styles["H1"]))
            elif line.startswith("## "):
                elements.append(Paragraph(line.replace("## ", ""), styles["H1"]))
            elif line.strip():
                elements.append(Paragraph(line, styles["Body"]))

            elements.append(Spacer(1, 6))

        doc.build(elements)

        # Отправка PDF в Telegram
        await msg.answer_document(types.FSInputFile(pdf_path), caption="📄 Ваш BRD документ (PDF)")

        # ==============================
        # Confluence
        # ==============================
        # Название страницы — лимит 255 символов у Confluence
        raw_title = final_data.get("goal", "Новый проект")
        safe_title = f"BRD – {raw_title[:200]}"  # гарантированно меньше 255

        page_url = create_brd_page(title_raw=safe_title, brd_text=brd_text, pdf_path=pdf_path)

        if page_url:
            await msg.answer(f"✅ BRD также загружен в Confluence:\n{page_url}")
        else:
            await msg.answer("⚠️ Ошибка при создании страницы Confluence. Проверь API-токен и настройки.")

        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        reset_user(user_id)
        return

    # Следующий вопрос
    await msg.answer(QUESTIONS[step][1])


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
