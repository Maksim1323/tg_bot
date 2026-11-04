import easyocr
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# Инициализируем один раз (тяжёлая операция)
reader = None

def get_reader():
    global reader
    if reader is None:
        logger.info("Загрузка EasyOCR модели...")
        reader = easyocr.Reader(['en', 'ru'], gpu=False, verbose=False)
        logger.info("EasyOCR готов")
    return reader


def recognize_text(image_bytes: bytes) -> str:
    """Распознаёт текст с изображения"""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        results = get_reader().readtext(image)
        texts = [res[1] for res in results if res[1].strip()]
        return '\n'.join(texts) if texts else ""
    except Exception as e:
        logger.error(f"OCR ошибка: {e}")
        return f"[Ошибка распознавания: {e}]"
