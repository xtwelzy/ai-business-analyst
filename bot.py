import asyncio
import os
import tempfile

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TELEGRAM_BOT_TOKEN
from utils import add_user_answer, get_user_dialog, reset_user
from llm_engine import generate_brd
from dialog_engine import analyze_answer
from confluence_api import create_brd_page
from diagram_renderer import render_diagram_png

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors


bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# ==============================
# ВОПРОСЫ
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

CONFIRMATION_FLAG = "_await_confirmation"


# ==============================
# Длинные сообщения
# ==============================
async def send_long_message(msg, text):
    MAX_LEN = 3500
    chunks = [text[i:i + MAX_LEN] for i in range(0, len(text), MAX_LEN)]
    for chunk in chunks:
        await msg.answer(chunk)


# ==============================
# /start
# ==============================
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer(
        "👋 Привет! Я AI Business Analyst.\n"
        "Напиши /new чтобы начать сбор требований.\n/help чтобы посмотреть команды!"
    )


# ==============================
# /help
# ==============================
@dp.message(Command("help"))
async def help_cmd(msg: types.Message):
    help_text = (
        "📘 *Команды бота*\n\n"
        "🆕 /new — начать сбор требований\n"
        "↩️ /back — вернуться назад\n"
        "⏭ /skip — пропустить вопрос\n"
        "❌ /cancel — отменить сессию\n"
        "ℹ️ /help — справка\n\n"
        "После завершения вопросов бот:\n"
        "— генерирует BRD\n"
        "— показывает предпросмотр\n"
        "— формирует PDF\n"
        "— вставляет PNG-диаграммы\n"
        "— выгружает документ в Confluence\n"
    )
    await msg.answer(help_text, parse_mode="Markdown")


# ==============================
# /new
# ==============================
@dp.message(Command("new"))
async def new_requirement(msg: types.Message):
    user_id = str(msg.from_user.id)
    reset_user(user_id)
    add_user_answer(user_id, "step", 0)
    await msg.answer("🔎 Начинаем сбор требований.\n\n" + QUESTIONS[0][1])


# ==============================
# /cancel
# ==============================
@dp.message(Command("cancel"))
async def cancel_cmd(msg: types.Message):
    user_id = str(msg.from_user.id)
    reset_user(user_id)
    await msg.answer("❌ Сессия отменена.\nНапиши /new чтобы начать заново.")


# ==============================
# /back
# ==============================
@dp.message(Command("back"))
async def go_back(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    if "step" not in dialog or dialog["step"] == 0:
        return await msg.answer("❗ Нельзя вернуться назад.")

    step = dialog["step"] - 1
    add_user_answer(user_id, "step", step)

    await msg.answer(f"↩️ Возвращаюсь назад:\n\n{QUESTIONS[step][1]}")


# ==============================
# /skip
# ==============================
@dp.message(Command("skip"))
async def skip_question(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    if "step" not in dialog:
        return await msg.answer("❗ Команда недоступна. Напиши /new.")

    step = dialog["step"]

    if dialog.get(CONFIRMATION_FLAG):
        return await msg.answer("❗ Сейчас нельзя пропустить — нужно подтвердить документ.")

    if step >= len(QUESTIONS):
        return await msg.answer("❗ Все вопросы уже завершены.")

    key, _ = QUESTIONS[step]
    add_user_answer(user_id, key, "— (пропущено пользователем) —")

    step += 1
    add_user_answer(user_id, "step", step)

    if step >= len(QUESTIONS):
        return await start_brd_preview(msg, dialog)

    await msg.answer(f"⏭ Пропущено.\nСледующий вопрос:\n\n{QUESTIONS[step][1]}")


# ==============================
# Обработка диалога
# ==============================
@dp.message()
async def process_dialog(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    if dialog.get(CONFIRMATION_FLAG):
        return await msg.answer("Используй кнопки ниже ⬇️")

    if "step" not in dialog:
        return await msg.answer("Напиши /new чтобы начать.")

    step = dialog["step"]

    if step >= len(QUESTIONS):  # защита
        step = len(QUESTIONS) - 1
        add_user_answer(user_id, "step", step)

    key, question_text = QUESTIONS[step]

    # анализ LLM
    analysis = analyze_answer(question_text, msg.text)
    status = analysis.get("status")

    if status == "bad":
        return await msg.answer("⚠️ Ответ недостаточно полный.\n" + question_text)

    if status == "clarify":
        return await msg.answer("❓ " + analysis["clarify_question"])

    normalized = analysis.get("normalized", msg.text)

    add_user_answer(user_id, key, normalized)
    add_user_answer(user_id, key + "_history", msg.text)

    step += 1
    add_user_answer(user_id, "step", step)

    if step >= len(QUESTIONS):
        return await start_brd_preview(msg, dialog)

    await msg.answer(QUESTIONS[step][1])


# ==============================
# Генерация предварительного BRD
# ==============================
async def start_brd_preview(msg: types.Message, dialog):
    processing = await msg.answer("⏳ Обрабатываю… Генерирую BRD + диаграммы…")

    final_data = {k: v for k, v in dialog.items() if not k.startswith("_")}
    brd = generate_brd(final_data)

    try:
        await processing.delete()
    except:
        pass

    add_user_answer(str(msg.from_user.id), "brd_data", brd)
    add_user_answer(str(msg.from_user.id), CONFIRMATION_FLAG, True)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
    kb.button(text="❌ Заново", callback_data="confirm_no")
    kb.adjust(2)

    await msg.answer("📝 *Предварительный BRD:*", parse_mode="Markdown", reply_markup=kb.as_markup())
    await send_long_message(msg, brd["document"])


# ==============================
# Inline YES / NO
# ==============================
@dp.callback_query(lambda c: c.data in ["confirm_yes", "confirm_no"])
async def confirm_callback(cb: types.CallbackQuery):
    user_id = str(cb.from_user.id)

    if cb.data == "confirm_no":
        reset_user(user_id)
        return await cb.message.answer("🔄 Начинаем заново. Напиши /new")

    await cb.message.answer("📄 Подтверждено! Генерация PDF + PNG + Confluence…")
    dialog = get_user_dialog(user_id)
    await finalize_brd(cb.message, dialog)


# ==============================
# Финальная генерация PDF + диаграмм PNG + Confluence
# ==============================
async def finalize_brd(msg: types.Message, dialog):
    user_id = str(msg.from_user.id)

    brd = dialog["brd_data"]
    document = brd["document"]

    pdf_path = tempfile.mktemp(suffix=".pdf")

    # шрифт
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Regular.ttf")
    pdfmetrics.registerFont(TTFont("Montserrat", font_path))

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1", fontName="Montserrat", fontSize=16, textColor=colors.HexColor("#1A4D8F")))
    styles.add(ParagraphStyle(name="Body", fontName="Montserrat", fontSize=11))

    elems = []

    # Текст BRD
    for line in document.split("\n"):
        if line.startswith("# "):
            elems.append(Paragraph(line[2:], styles["H1"]))
        else:
            elems.append(Paragraph(line, styles["Body"]))
        elems.append(Spacer(1, 6))

    elems.append(PageBreak())

    # ===== PNG-диаграммы =====
    diagrams = {
        "KPI Tree": brd.get("kpi_tree_mermaid"),
        "Use Case": brd.get("usecase_mermaid"),
        "Activity": brd.get("activity_mermaid"),
        "Sequence": brd.get("sequence_mermaid"),
        "Business Process": brd.get("bpmn_mermaid"),
    }

    for name, code in diagrams.items():
        if not code:
            continue

        png = render_diagram_png(code, name.replace(" ", "_").lower())
        if png:
            elems.append(Paragraph(f"{name} Diagram", styles["H1"]))
            elems.append(Image(png, width=430, height=260))
            elems.append(Spacer(1, 20))

    doc.build(elems)

    await msg.answer_document(types.FSInputFile(pdf_path), caption="📄 Финальный BRD (PDF + диаграммы)")

    # Confluence
    goal_title = dialog.get("goal", "Проект")[:200]
    page_url = create_brd_page(title_raw=f"BRD – {goal_title}", brd_text=document, pdf_path=pdf_path)

    if page_url:
        await msg.answer(f"✅ Загружено в Confluence:\n{page_url}")
    else:
        await msg.answer("⚠️ Ошибка загрузки в Confluence.")

    os.remove(pdf_path)
    reset_user(user_id)


# ==============================
# RUN
# ==============================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
