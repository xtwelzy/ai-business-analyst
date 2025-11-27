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
from pdf_engine import PDFEngine

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
    ("nfr", "7️⃣ Какие нефункциональные требования важны?"),
    ("kpi", "8️⃣ Какие KPI должны улучшиться?"),
]

CONFIRM_FLAG = "_await_confirmation"


# ==============================
# Отправка длинных сообщений
# ==============================
async def send_long(msg, text):
    MAX = 3500
    chunks = [text[i:i + MAX] for i in range(0, len(text), MAX)]
    for c in chunks:
        await msg.answer(c)


# ==============================
# /start
# ==============================
@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer(
        "👋 Привет! Я AI Business Analyst.\n"
        "Напиши /new чтобы начать сбор требований.\n/help — справка."
    )


# ==============================
# /help
# ==============================
@dp.message(Command("help"))
async def help_cmd(msg: types.Message):
    await msg.answer(
        "📘 Команды:\n\n"
        "🆕 /new — начать\n"
        "↩️ /back — назад\n"
        "⏭ /skip — пропустить\n"
        "❌ /cancel — отменить\n\n"
        "После вопросов бот:\n"
        "✔ генерирует BRD\n"
        "✔ создаёт диаграммы\n"
        "✔ делает идеальный PDF\n"
        "✔ выгружает в Confluence"
    )


# ==============================
# /new
# ==============================
@dp.message(Command("new"))
async def new_cmd(msg: types.Message):
    user = str(msg.from_user.id)
    reset_user(user)
    add_user_answer(user, "step", 0)
    await msg.answer("🔎 Начинаем.\n\n" + QUESTIONS[0][1])


# ==============================
# /cancel
# ==============================
@dp.message(Command("cancel"))
async def cancel_cmd(msg: types.Message):
    reset_user(str(msg.from_user.id))
    await msg.answer("❌ Сессия отменена.")


# ==============================
# /back
# ==============================
@dp.message(Command("back"))
async def back_cmd(msg: types.Message):
    user = str(msg.from_user.id)
    dialog = get_user_dialog(user)

    if "step" not in dialog or dialog["step"] == 0:
        return await msg.answer("⛔ Назад нельзя.")

    step = dialog["step"] - 1
    add_user_answer(user, "step", step)
    await msg.answer("↩️ Ок, вернулся:\n\n" + QUESTIONS[step][1])


# ==============================
# /skip
# ==============================
@dp.message(Command("skip"))
async def skip_cmd(msg: types.Message):
    user = str(msg.from_user.id)
    dialog = get_user_dialog(user)

    if "step" not in dialog:
        return await msg.answer("Используй /new")

    if dialog.get(CONFIRM_FLAG):
        return await msg.answer("⛔ Сейчас нельзя пропустить.")

    step = dialog["step"]
    key, _ = QUESTIONS[step]

    add_user_answer(user, key, "(пропущено)")

    step += 1
    add_user_answer(user, "step", step)

    if step >= len(QUESTIONS):
        return await preview_brd(msg, dialog)

    await msg.answer("⏭ Пропущено.\n\n" + QUESTIONS[step][1])


# ==============================
# Диалог
# ==============================
@dp.message()
async def collect(msg: types.Message):
    user = str(msg.from_user.id)
    dialog = get_user_dialog(user)

    if dialog.get(CONFIRM_FLAG):
        return await msg.answer("Используй кнопки ниже.")

    if "step" not in dialog:
        return await msg.answer("Напиши /new")

    step = dialog["step"]
    key, q_text = QUESTIONS[step]

    analysis = analyze_answer(q_text, msg.text)
    if analysis["status"] == "bad":
        return await msg.answer("⚠️ Ответ слабый.\n" + q_text)
    if analysis["status"] == "clarify":
        return await msg.answer("❓ " + analysis["clarify_question"])

    normalized = analysis.get("normalized", msg.text)

    add_user_answer(user, key, normalized)
    add_user_answer(user, key + "_history", msg.text)

    step += 1
    add_user_answer(user, "step", step)

    if step >= len(QUESTIONS):
        return await preview_brd(msg, dialog)

    await msg.answer(QUESTIONS[step][1])


# ==============================
# Предпросмотр BRD
# ==============================
async def preview_brd(msg: types.Message, dialog):
    loading = await msg.answer("⏳ Генерация BRD и диаграмм…")

    data = {k: v for k, v in dialog.items() if not k.startswith("_")}
    brd = generate_brd(data)

    await loading.delete()

    add_user_answer(str(msg.from_user.id), "brd_data", brd)
    add_user_answer(str(msg.from_user.id), CONFIRM_FLAG, True)

    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить", callback_data="yes")
    kb.button(text="❌ Заново", callback_data="no")
    kb.adjust(2)

    await msg.answer("📝 *Предварительный BRD:*", parse_mode="Markdown", reply_markup=kb.as_markup())
    await send_long(msg, brd["document"])


# ==============================
# Callback confirm
# ==============================
@dp.callback_query(lambda c: c.data in ["yes", "no"])
async def confirm(cb: types.CallbackQuery):
    user = str(cb.from_user.id)

    if cb.data == "no":
        reset_user(user)
        return await cb.message.answer("🔄 Начинаем заново. /new")

    await cb.message.answer("📄 Генерирую PDF + выгрузка в Confluence…")

    dialog = get_user_dialog(user)
    await finalize(cb.message, dialog)


# ==============================
# Финал: PDF + диаграммы + Confluence
# ==============================
async def finalize(msg: types.Message, dialog):
    brd = dialog["brd_data"]
    document = brd["document"]

    # Диаграммы → PNG файлы
    diagrams_raw = {
        "KPI Tree": brd.get("kpi_tree_mermaid"),
        "Use Case": brd.get("usecase_mermaid"),
        "Activity": brd.get("activity_mermaid"),
        "Sequence": brd.get("sequence_mermaid"),
        "Business Process": brd.get("bpmn_mermaid"),
    }

    diagram_paths = {}
    for name, code in diagrams_raw.items():
        if code:
            png = render_diagram_png(code, name.replace(" ", "_").lower())
            if png:
                diagram_paths[name] = png

    # PDF
    pdf_path = tempfile.mktemp(suffix=".pdf")

    engine = PDFEngine(pdf_path)
    engine.build(
        text_sections={"BRD Document": document},
        diagram_paths=diagram_paths
    )

    await msg.answer_document(types.FSInputFile(pdf_path), caption="📄 Финальный BRD PDF")

    # Confluence (НОВОЕ — ПЕРЕДАЁМ PNG)
    title = dialog.get("goal", "Project")[:120]
    url = create_brd_page(
        title_raw=f"BRD – {title}",
        brd_text=document,
        pdf_path=pdf_path,
        diagrams=diagram_paths
    )

    if url:
        await msg.answer("✅ Загружено в Confluence:\n" + url)
    else:
        await msg.answer("⚠️ Ошибка загрузки в Confluence.")

    os.remove(pdf_path)
    reset_user(str(msg.from_user.id))


# ==============================
# RUN
# ==============================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
