from fpdf import FPDF
from typing import Optional
import os


class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 8, 'Результат Telegram-бота', align='C')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Страница {self.page_no()}', align='C')


def create_translation_pdf(original: str, translation: str, phonetic: str) -> bytes:
    """Создаёт PDF с тремя страницами: оригинал / перевод / транскрипция"""
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Страница 1 — Оригинал
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, "1. ОРИГИНАЛ (English)", ln=True)
    pdf.ln(5)
    pdf.set_font('Helvetica', size=12)
    pdf.multi_cell(0, 7, original or "(пусто)")

    # Страница 2 — Перевод
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, "2. ПЕРЕВОД (Русский)", ln=True)
    pdf.ln(5)
    pdf.set_font('Helvetica', size=12)
    # Для кириллицы лучше использовать DejaVu, но для простоты используем стандартный
    # В реальном проекте добавьте DejaVuSans.ttf
    pdf.multi_cell(0, 7, translation or "(пусто)")

    # Страница 3 — Транскрипция
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, "3. КАК ЧИТАТЬ (русскими буквами)", ln=True)
    pdf.ln(5)
    pdf.set_font('Helvetica', size=12)
    pdf.multi_cell(0, 7, phonetic or "(пусто)")

    return bytes(pdf.output())


def create_ocr_pdf(text: str, title: str = "Распознанный текст") -> bytes:
    """Создаёт PDF с распознанным текстом"""
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(5)
    pdf.set_font('Helvetica', size=12)
    pdf.multi_cell(0, 7, text or "(текст не распознан)")
    return bytes(pdf.output())
