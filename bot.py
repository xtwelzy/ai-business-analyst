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
    await msg.answer("👋 Привет! Я AI Business Analyst.\nНапиши /new чтобы начать сбор требований.\n/help чтобы узнать все команды!")

# ==============================
# /help — список всех команд
# ==============================
@dp.message(Command("help"))
async def help_cmd(msg: types.Message):
    help_text = (
        "📘 *Справка по командам*\n\n"
        "Вот что я умею:\n\n"
        "🆕 */new* — начать сбор требований с нуля\n"
        "↩️ */back* — вернуться на один шаг назад\n"
        "⏭ */skip* — пропустить текущий вопрос\n"
        "📄 *Автоматически*: после последнего ответа я:\n"
        "   — генерирую предварительный BRD\n"
        "   — покажу кнопки *YES / NO*\n"
        "   — затем создам PDF\n"
        "   — загружу документ в Confluence\n\n"
        "ℹ️ */help* — показать эту справку\n"
        "❌ */cancel* — отменить текущую сессию и начать заново\n\n"
        "Если что-то пойдёт не так — просто напиши */new*."
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
# /cancel — отменить текущую сессию
# ==============================

@dp.message(Command("cancel"))
async def cancel_cmd(msg: types.Message):
    user_id = str(msg.from_user.id)
    reset_user(user_id)
    await msg.answer("❌ Текущая сессия отменена.\nНапиши /new чтобы начать заново.")


# ==============================
# /back — вернуться назад
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
# /skip — пропустить текущий вопрос
# ==============================
@dp.message(Command("skip"))
async def skip_question(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    if "step" not in dialog:
        return await msg.answer("❗ Нечего пропускать. Напиши /new чтобы начать.")

    step = dialog["step"]

    # Если уже на этапе подтверждения BRD — нельзя
    if dialog.get(CONFIRMATION_FLAG):
        return await msg.answer("❗ Сейчас нельзя пропустить, нужно подтвердить документ.")

    # Если больше нечего пропускать
    if step >= len(QUESTIONS):
        return await msg.answer("❗ Все вопросы уже пройдены. Ожидается подтверждение BRD.")

    key, _ = QUESTIONS[step]

    # Ставим пустой ответ, чтобы структура была заполнена
    add_user_answer(user_id, key, "— (пропущено пользователем) —")

    # Переход вперёд
    step += 1
    add_user_answer(user_id, "step", step)

    # Если это был последний шаг → идём в подтверждение BRD
    if step >= len(QUESTIONS):
        final_data = {k: v for k, v in dialog.items() if not k.startswith("_")}
        preview = generate_brd(final_data)

        add_user_answer(user_id, "brd_preview", preview)
        add_user_answer(user_id, CONFIRMATION_FLAG, True)

        # Inline-кнопки confirm
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
        kb.button(text="❌ Начать заново", callback_data="confirm_no")
        kb.adjust(2)

        await msg.answer(
            "📝 *Предварительный BRD сформирован (некоторые поля пропущены).*",
            parse_mode="Markdown",
            reply_markup=kb.as_markup()
        )

        await send_long_message(msg, preview)
        return

    # Иначе — отправляем следующий вопрос
    await msg.answer(f"⏭ Пропущено. Следующий вопрос:\n\n{QUESTIONS[step][1]}")


# ==============================
# ОСНОВНАЯ ЛОГИКА
# ==============================
@dp.message()
async def process_dialog(msg: types.Message):
    user_id = str(msg.from_user.id)
    dialog = get_user_dialog(user_id)

    # ——— Если ожидается подтверждение BRD ———
    if dialog.get(CONFIRMATION_FLAG):
        return await msg.answer("Используй кнопки ниже ⬇️")

    if "step" not in dialog:
        return await msg.answer("Напиши /new чтобы начать.")

    step = dialog["step"]

    # защита
    if step >= len(QUESTIONS):
        step = len(QUESTIONS) - 1
        add_user_answer(user_id, "step", step)

    key, question_text = QUESTIONS[step]

    # ——— Анализ ———
    analysis = analyze_answer(question_text, msg.text)
    status = analysis.get("status")
    normalized = analysis.get("normalized", msg.text)
    clarify = analysis.get("clarify_question")

    if status == "bad":
        return await msg.answer("⚠️ Ответ слишком слабый. Попробуй подробнее:\n" + question_text)

    if status == "clarify":
        return await msg.answer("❓ " + clarify)

    # сохраняем
    add_user_answer(user_id, key, normalized)
    add_user_answer(user_id, key + "_history", msg.text)

    step += 1
    add_user_answer(user_id, "step", step)

    # ——— Все вопросы отвечены ———
    if step >= len(QUESTIONS):

        # ⏳ Показываем индикатор обработки
        processing_msg = await msg.answer("⏳ Обрабатываю данные... Генерирую BRD...")

        final_data = {k: v for k, v in dialog.items() if not k.startswith("_")}
        preview = generate_brd(final_data)

        # Удаляем индикатор (не обязательно, но красиво)
        try:
            await processing_msg.delete()
        except:
            pass

        add_user_answer(user_id, "brd_preview", preview)
        add_user_answer(user_id, CONFIRMATION_FLAG, True)

        # кнопки yes/no
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ Подтвердить", callback_data="confirm_yes")
        kb.button(text="❌ Начать заново", callback_data="confirm_no")
        kb.adjust(2)

        await msg.answer(
            "📝 *Предварительный BRD:*\nПроверь документ ниже.",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )

        await send_long_message(msg, preview)
        return

    await msg.answer(QUESTIONS[step][1])


# ==============================
# INLINE YES / NO
# ==============================
@dp.callback_query(lambda c: c.data in ["confirm_yes", "confirm_no"])
async def brd_confirmation(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    dialog = get_user_dialog(user_id)

    if callback.data == "confirm_no":
        reset_user(user_id)
        await callback.message.answer("🔄 Начинаем заново.\nНапиши /new")
        return

    await callback.message.answer("📄 Подтверждено! Генерирую PDF и загружаю в Confluence…")
    await finalize_brd(callback.message, dialog)


# ==============================
# Финальный BRD + PDF + Confluence
# ==============================
async def finalize_brd(msg: types.Message, dialog):
    user_id = str(msg.from_user.id)

    brd_text = dialog.get("brd_preview")
    final_data = {k: v for k, v in dialog.items() if not k.startswith("_")}

    # ——— PDF ———
    pdf_path = tempfile.mktemp(suffix=".pdf")
    font_path = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Regular.ttf")
    pdfmetrics.registerFont(TTFont("Montserrat", font_path))

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Header", fontName="Montserrat", fontSize=20, spaceAfter=20))
    styles.add(ParagraphStyle(name="H1", fontName="Montserrat", fontSize=16, textColor=colors.HexColor("#1A4D8F"), spaceAfter=10))
    styles.add(ParagraphStyle(name="Body", fontName="Montserrat", fontSize=11, leading=16))

    elements = [
        Paragraph("Business Requirements Document (BRD)", styles["Header"]),
        Paragraph("AI Business Analyst Bot", styles["Body"]),
        PageBreak()
    ]

    for line in brd_text.split("\n"):
        if line.startswith("# "):
            elements.append(Paragraph(line.replace("# ", ""), styles["H1"]))
        elif line.startswith("## "):
            elements.append(Paragraph(line.replace("## ", ""), styles["H1"]))
        else:
            elements.append(Paragraph(line, styles["Body"]))
        elements.append(Spacer(1, 6))

    doc.build(elements)

    await msg.answer_document(types.FSInputFile(pdf_path), caption="📄 Ваш BRD документ (PDF)")

    # ——— Confluence ———
    raw_title = final_data.get("goal", "Новый проект")
    safe_title = f"BRD – {raw_title[:200]}"

    page_url = create_brd_page(title_raw=safe_title, brd_text=brd_text, pdf_path=pdf_path)

    if page_url:
        await msg.answer(f"✅ BRD загружен в Confluence:\n{page_url}")
    else:
        await msg.answer("⚠️ Ошибка при создании страницы Confluence.")

    os.remove(pdf_path)
    reset_user(user_id)


# ==============================
# RUN
# ==============================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
