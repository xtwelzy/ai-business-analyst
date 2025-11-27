import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader


class PDFEngine:
    def __init__(self, output_path: str):
        self.output_path = output_path

        # ---- Шрифт ----
        font_path = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Regular.ttf")
        pdfmetrics.registerFont(TTFont("Montserrat", font_path))

        # ---- Стили ----
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name="H1", fontName="Montserrat", fontSize=22, leading=28, spaceAfter=12))
        self.styles.add(ParagraphStyle(name="H2", fontName="Montserrat", fontSize=16, leading=20, spaceAfter=8))
        self.styles.add(ParagraphStyle(name="Body", fontName="Montserrat", fontSize=11, leading=15, spaceAfter=6))

    # ----------------------------------------------------------------------
    # ПАРСЕР Markdown-ТАБЛИЦ → ДВУМЕРНЫЙ МАССИВ
    # ----------------------------------------------------------------------
    def parse_markdown_table(self, block: str):
        lines = block.strip().split("\n")
        lines = [ln for ln in lines if ln.strip()]

        # Находим строку --- разделителя
        divider_index = None
        for i, ln in enumerate(lines):
            if re.match(r"^\|[-: ]+\|", ln):
                divider_index = i
                break

        if divider_index is None:
            return None

        # Заголовки
        header_line = lines[0]
        headers = [h.strip() for h in header_line.strip("|").split("|")]

        # Тело таблицы
        rows = []
        for ln in lines[divider_index + 1:]:

            cols = [c.strip() for c in ln.strip("|").split("|")]

            # GPT может разрывать строки → склеиваем
            if len(cols) < len(headers):
                if rows:
                    rows[-1][-1] += " " + ln.strip()
                continue

            rows.append(cols)

        return [headers] + rows

    # ----------------------------------------------------------------------
    # РЕНДЕР МАРКДАУНА: ТЕКСТ + ТАБЛИЦЫ
    # ----------------------------------------------------------------------
    def add_markdown(self, elements, text: str):
        # Шаблон Markdown-таблицы
        pattern = r"(?:^\|.*\|\s*$\n?)+"
        blocks = re.finditer(pattern, text, flags=re.MULTILINE)

        last_end = 0

        for match in blocks:
            start, end = match.span()
            table_block = match.group()

            # 1. Рендер текста ДО таблицы
            before_text = text[last_end:start].strip()
            if before_text:
                for ln in before_text.split("\n"):
                    if ln.startswith("# "):
                        elements.append(Paragraph(ln[2:], self.styles["H1"]))
                    elif ln.startswith("## "):
                        elements.append(Paragraph(ln[3:], self.styles["H2"]))
                    elif ln.strip():
                        elements.append(Paragraph(ln, self.styles["Body"]))
                    elements.append(Spacer(1, 6))

            # 2. Рендер самой таблицы
            parsed = self.parse_markdown_table(table_block)
            if parsed:
                table = Table(parsed, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Montserrat'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.35, colors.grey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 16))

            last_end = end

        # 3. Текст ПОСЛЕ последней таблицы
        remaining = text[last_end:].strip()
        if remaining:
            for ln in remaining.split("\n"):
                if ln.startswith("# "):
                    elements.append(Paragraph(ln[2:], self.styles["H1"]))
                elif ln.startswith("## "):
                    elements.append(Paragraph(ln[3:], self.styles["H2"]))
                elif ln.strip():
                    elements.append(Paragraph(ln, self.styles["Body"]))
                elements.append(Spacer(1, 6))

    # ----------------------------------------------------------------------
    # Рендер обычной таблицы (если список)
    # ----------------------------------------------------------------------
    def add_table(self, elements, table_data):
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Montserrat'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.35, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 16))

    # ----------------------------------------------------------------------
    # Рендер диаграммы без растягивания
    # ----------------------------------------------------------------------
    def add_diagram(self, elements, title, png_path):
        elements.append(Paragraph(title, self.styles["H2"]))
        elements.append(Spacer(1, 8))

        img = ImageReader(png_path)
        iw, ih = img.getSize()

        max_width = 480
        max_height = 680

        ratio = max_width / iw
        new_w = max_width
        new_h = ih * ratio

        if new_h > max_height:
            ratio2 = max_height / new_h
            new_w = new_w * ratio2
            new_h = new_h * ratio2

        elements.append(Image(png_path, width=new_w, height=new_h))
        elements.append(Spacer(1, 24))

    # ----------------------------------------------------------------------
    # Финальная сборка PDF
    # ----------------------------------------------------------------------
    def build(self, text_sections: dict, diagram_paths: dict):
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=A4,
            leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=40
        )

        elements = []

        # ---------------- ОБЛОЖКА ----------------
        elements.append(Paragraph("Business Requirements Document", self.styles["H1"]))
        elements.append(Spacer(1, 16))
        elements.append(Paragraph("Generated by AI Business Analyst Bot", self.styles["Body"]))
        elements.append(PageBreak())

        # ---------------- ТЕКСТ ----------------
        for title, content in text_sections.items():
            elements.append(Paragraph(title, self.styles["H1"]))
            elements.append(Spacer(1, 12))

            if isinstance(content, list):
                if len(content) > 0 and isinstance(content[0], list):
                    self.add_table(elements, content)
                else:
                    for ln in content:
                        elements.append(Paragraph(f"• {ln}", self.styles["Body"]))
                        elements.append(Spacer(1, 4))
            else:
                self.add_markdown(elements, content)

            elements.append(Spacer(1, 18))

        elements.append(PageBreak())

        # ---------------- ДИАГРАММЫ ----------------
        for name, png in diagram_paths.items():
            if png:
                self.add_diagram(elements, f"{name} Diagram", png)

        doc.build(elements)

        return self.output_path
