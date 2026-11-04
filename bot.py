import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_ID
from states import BotStates
from services.translator import translate_en_to_ru, phonetic_russian
from services.ocr import recognize_text
from services.pdf_generator import create_translation_pdf, create_ocr_pdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="1. Перевод текста (EN → RU + PDF)", callback_data="mode_translate")
    builder.button(text="2. Распознать текст с фото + PDF", callback_data="mode_ocr")
    builder.button(text="3. Произвольное задание → админу", callback_data="mode_task")
    builder.adjust(1)
    return builder.as_markup()


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>Привет!</b>\n\n"
        "Я бот для перевода, OCR и передачи заданий.\n"
        "Выбери нужную функцию:",
        reply_markup=main_menu()
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "<b>Доступные команды:</b>\n"
        "/start — главное меню\n"
        "/cancel — отменить текущее действие\n"
        "/help — эта справка\n\n"
        "В режиме задания после описания файлов напиши /done"
    )


# ========== 1. ПЕРЕВОД ==========
@dp.callback_query(F.data == "mode_translate")
async def mode_translate(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_text_for_translate)
    await callback.message.edit_text(
        "<b>Режим перевода</b>\n\n"
        "Отправь английский текст.\n\n"
        "Я создам PDF с 3 страницами:\n"
        "1. Оригинал\n"
        "2. Перевод на русский\n"
        "3. Как читать русскими буквами"
    )
    await callback.answer()


@dp.message(BotStates.waiting_text_for_translate, F.text)
async def process_translate(message: Message, state: FSMContext):
    status = await message.answer("⏳ Обрабатываю текст...")
    
    original = message.text.strip()
    if len(original) > 4000:
        await status.edit_text("Текст слишком длинный (макс. ~4000 символов).")
        return

    translation = translate_en_to_ru(original)
    phonetic = phonetic_russian(original)

    pdf_bytes = create_translation_pdf(original, translation, phonetic)
    file = BufferedInputFile(pdf_bytes, filename="translation.pdf")

    await message.answer_document(file, caption="✅ Готовый PDF с переводом")
    
    # Отправка админу
    if ADMIN_ID and ADMIN_ID != 0:
        try:
            await bot.send_document(
                ADMIN_ID,
                BufferedInputFile(pdf_bytes, filename="translation.pdf"),
                caption=f"📄 Перевод от @{message.from_user.username or message.from_user.id}"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить админу: {e}")

    await status.delete()
    await state.clear()
    await message.answer("Готово! Выбери следующую функцию:", reply_markup=main_menu())


# ========== 2. OCR ==========
@dp.callback_query(F.data == "mode_ocr")
async def mode_ocr(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_photo_for_ocr)
    await callback.message.edit_text(
        "<b>Режим OCR</b>\n\n"
        "Отправь фото с текстом.\n"
        "Я распознаю текст и создам PDF.\n\n"
        "<i>Примечание: поиск похожих картинок пока базовый (для полноценного нужен API).</i>"
    )
    await callback.answer()


@dp.message(BotStates.waiting_photo_for_ocr, F.photo)
async def process_ocr(message: Message, state: FSMContext):
    status = await message.answer("⏳ Распознаю текст... (это может занять 10–30 сек)")
    
    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        text = recognize_text(file_bytes.read())
        
        if not text.strip() or text.startswith("[Ошибка"):
            await status.edit_text("Текст не удалось распознать. Попробуй другое фото или более чёткое.")
            return

        pdf_bytes = create_ocr_pdf(text)
        pdf_file = BufferedInputFile(pdf_bytes, filename="ocr_result.pdf")

        await message.answer_document(pdf_file, caption="✅ Распознанный текст в PDF")

        if ADMIN_ID and ADMIN_ID != 0:
            try:
                await bot.send_document(
                    ADMIN_ID,
                    BufferedInputFile(pdf_bytes, filename="ocr_result.pdf"),
                    caption=f"📷 OCR от @{message.from_user.username or message.from_user.id}"
                )
            except Exception:
                pass

        await status.delete()
        await state.clear()
        await message.answer("Готово!", reply_markup=main_menu())
        
    except Exception as e:
        logger.exception("OCR error")
        await status.edit_text(f"Ошибка при обработке: {e}")


@dp.message(BotStates.waiting_photo_for_ocr)
async def process_ocr_wrong(message: Message):
    await message.answer("Пожалуйста, отправь именно фото (не документ и не текст).")


# ========== 3. ПРОИЗВОЛЬНОЕ ЗАДАНИЕ ==========
@dp.callback_query(F.data == "mode_task")
async def mode_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BotStates.waiting_task_description)
    await callback.message.edit_text(
        "<b>Режим задания</b>\n\n"
        "Опиши задание текстом.\n"
        "После описания можешь прислать файлы (фото, документы).\n"
        "Всё будет отправлено администратору.\n\n"
        "Когда закончишь с файлами — напиши /done"
    )
    await callback.answer()


@dp.message(BotStates.waiting_task_description, F.text)
async def process_task_desc(message: Message, state: FSMContext):
    await state.update_data(task_text=message.text, files=[])
    await state.set_state(BotStates.waiting_task_files)
    await message.answer(
        "✅ Описание сохранено.\n\n"
        "Теперь можешь прислать файлы (фото / документы).\n"
        "Когда закончишь — напиши <b>/done</b>"
    )


@dp.message(BotStates.waiting_task_files, F.photo | F.document)
async def process_task_files(message: Message, state: FSMContext):
    data = await state.get_data()
    files = data.get("files", [])
    
    if message.photo:
        files.append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.document:
        files.append({"type": "document", "file_id": message.document.file_id})
    
    await state.update_data(files=files)
    await message.answer(f"📎 Файл добавлен (всего {len(files)}). Пришли ещё или /done")


@dp.message(BotStates.waiting_task_files, Command("done"))
async def finish_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_text = data.get("task_text", "")
    files = data.get("files", [])

    if not ADMIN_ID or ADMIN_ID == 0:
        await message.answer("ADMIN_ID не настроен. Обратись к владельцу бота.")
        await state.clear()
        return

    try:
        await bot.send_message(
            ADMIN_ID,
            f"📩 <b>Новое задание</b> от @{message.from_user.username or message.from_user.id} "
            f"(ID: <code>{message.from_user.id}</code>):\n\n{task_text}"
        )
        for f in files:
            if f["type"] == "photo":
                await bot.send_photo(ADMIN_ID, f["file_id"])
            else:
                await bot.send_document(ADMIN_ID, f["file_id"])
        
        await message.answer("✅ Задание успешно отправлено администратору!", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        await message.answer(f"Не удалось отправить админу: {e}")

    await state.clear()


@dp.message(BotStates.waiting_task_files)
async def process_task_files_wrong(message: Message):
    await message.answer("Отправь фото/документ или напиши /done, чтобы завершить.")


async def main():
    logger.info("Бот запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
