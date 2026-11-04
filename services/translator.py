from deep_translator import GoogleTranslator
from g2p_en import G2p
import re

g2p = G2p()

# Приближённая карта ARPAbet → русские буквы
ARPABET_TO_RU = {
    'AA': 'а', 'AE': 'э', 'AH': 'а', 'AO': 'о', 'AW': 'ау', 'AY': 'ай',
    'B': 'б', 'CH': 'ч', 'D': 'д', 'DH': 'з', 'EH': 'е', 'ER': 'ёр',
    'EY': 'ей', 'F': 'ф', 'G': 'г', 'HH': 'х', 'IH': 'и', 'IY': 'и',
    'JH': 'дж', 'K': 'к', 'L': 'л', 'M': 'м', 'N': 'н', 'NG': 'нг',
    'OW': 'оу', 'OY': 'ой', 'P': 'п', 'R': 'р', 'S': 'с', 'SH': 'ш',
    'T': 'т', 'TH': 'с', 'UH': 'у', 'UW': 'у', 'V': 'в', 'W': 'у',
    'Y': 'й', 'Z': 'з', 'ZH': 'ж',
}


def translate_en_to_ru(text: str) -> str:
    """Перевод английского текста на русский"""
    try:
        return GoogleTranslator(source='en', target='ru').translate(text)
    except Exception as e:
        return f"[Ошибка перевода: {e}]"


def phonetic_russian(text: str) -> str:
    """
    Приближённая фонетическая транскрипция
    английского текста русскими буквами.
    """
    try:
        phones = g2p(text)
        result = []
        for p in phones:
            clean = re.sub(r'\d', '', p)  # убираем цифры ударения
            if clean in ARPABET_TO_RU:
                result.append(ARPABET_TO_RU[clean])
            elif clean in [' ', '.', ',', '!', '?', ';', ':', '-', "'"]:
                result.append(clean)
            else:
                result.append(clean.lower())
        return ' '.join(result)
    except Exception as e:
        return f"[Ошибка транскрипции: {e}]"
